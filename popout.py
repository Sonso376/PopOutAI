import random
import math
import copy

class Poupout:
    def __init__(self, rows, cols, moved="O", to_move="X"):
        #informações básicas do tabuleiro
        self.rows = rows                    
        self.cols = cols
        self.moved = moved
        self.to_move = to_move
        self.board = [["-" for _ in range(rows)] for _ in range(cols)]
        #informações adicionais para facilitar implementação de alguns métodos
        self.n_pieces = 0
        self.repeated = False
        self.last_move = None
        self.draw = False

    def display(self):
        print("  " + " ".join(str(i) for i in range(self.cols)))
        for r in range(self.rows):
            print("  ", end="")
            for c in range(self.cols):
                print(self.board[c][r], end="")
            print("")

    #usado para a criação do dataset
    def board_key(self):
        return tuple(tuple(col) for col in self.board), self.to_move

    def put(self, column):
        if column < 0 or column >= self.cols or self.board[column][0] != "-":
            raise Exception("Acao impossivel")
        for i in range(self.rows - 1, -1, -1):
            if self.board[column][i] == "-":
                self.board[column][i] = self.to_move
                self.n_pieces += 1
                return

    def pop(self, column):
        if column < 0 or column >= self.cols or self.board[column][-1] != self.to_move:
            raise Exception("Acao impossivel")
        self.board[column] = ["-"] + self.board[column][:-1]
        self.n_pieces -= 1

    def change_to_move(self):
        self.to_move, self.moved = self.moved, self.to_move

    def make_move(self, move, column):
        try:
            if move == "put":
                self.put(column)
            elif move == "pop":
                self.pop(column)
            elif move == "draw" and (self.repeated or self.check_full()):
                self.draw = True
            else:
                return False
            self.last_move = (move, column)
            return True
        except Exception:
            return False

    def check_row(self, row):
        line = "".join(self.board[c][row] for c in range(self.cols))
        if self.moved * 4 in line:
            return self.moved
        if self.to_move * 4 in line:
            return self.to_move
        return None

    def check_col(self, col):
        line = "".join(self.board[col][r] for r in range(self.rows))
        if self.moved * 4 in line:
            return self.moved
        if self.to_move * 4 in line:
            return self.to_move
        return None

    def check_diag1(self, row, col):
        cells = min(self.rows - row, self.cols - col)
        if cells < 4:
            return None
        line = "".join(self.board[col + i][row + i] for i in range(cells))
        if self.moved * 4 in line:
            return self.moved
        if self.to_move * 4 in line:
            return self.to_move
        return None

    def check_diag2(self, row, col):
        cells = min(self.rows - row, col + 1)
        if cells < 4:
            return None
        line = "".join(self.board[col - i][row + i] for i in range(cells))
        if self.moved * 4 in line:
            return self.moved
        if self.to_move * 4 in line:
            return self.to_move
        return None

    def check_win(self):
        if self.last_move is None:
            return None
        move, column = self.last_move
        adversary_win = False

        if move == "put":
            #verificar o local da ultima peça colocada
            row = None
            for r in range(self.rows):
                if self.board[column][r] == self.moved:
                    row = r
                    break

            for f in [lambda: self.check_row(row), lambda: self.check_col(column),
                      lambda: self.check_diag1(max(0, row - column), max(0, column - row)),
                      lambda: self.check_diag2(max(0, row - (self.cols - 1 - column)), min(self.cols - 1, row + column))]:
                winner = f()
                if winner is not None:
                    return winner

        elif move == "pop":
            #verificar a coluna da peça retirada
            for row in range(self.rows - 1, -1, -1):
                if self.board[column][row] == "-":
                    break
                for f in [lambda row=row: self.check_row(row),
                          lambda row=row: self.check_diag1(max(0, row - column), max(0, column - row)),
                          lambda row=row: self.check_diag2(max(0, row - (self.cols - 1 - column)), min(self.cols - 1, row + column))]:
                    winner = f()
                    if winner == self.moved:
                        return winner
                    if winner == self.to_move:
                        adversary_win = True
        #apenas verificar se adversãrio ganhou depois do jogador que jogou
        if adversary_win:
            return self.to_move
        return None

    def check_full(self):
        return self.n_pieces == self.rows * self.cols

    def check_repeat(self, state_counts):
        key = self.board_key()
        state_counts[key] += 1
        if state_counts[key] >= 3:
            self.repeated = True
        return self.repeated

    #auxiliares para a implementação de MCTS
    def clone(self):
        new = Poupout(self.rows, self.cols, self.moved, self.to_move)
        new.board = copy.deepcopy(self.board)
        new.n_pieces = self.n_pieces
        new.repeated = self.repeated
        new.last_move = self.last_move
        new.draw = self.draw
        return new

    def legal_moves(self):
        moves = []
        for c in range(self.cols):
            if self.board[c][0] == "-":
                moves.append(("put", c))
            if self.board[c][-1] == self.to_move:
                moves.append(("pop", c))
        if self.repeated or self.check_full():
            moves.append(("draw", 0))
        return moves
    
    def legal_put_moves(self):
        moves = []
        for c in range(self.cols):
            if self.board[c][0] == "-":
                moves.append(("put", c))
        return moves

    def is_terminal(self):
        return self.check_win() is not None or self.draw

    def get_result(self, maximizing_player):
        winner = self.check_win()
        if winner == maximizing_player:
            return 1
        if winner is not None:
            return -1
        return 0
    
    #auxiliares para criação dos datasets
    def random_board(self,n_pieces):
        for _ in range(n_pieces):
            moves=self.legal_put_moves()
            move=random.choice(moves)
            self.make_move(move[0], move[1])
            self.change_to_move()

    def full_check_win(self):
        adversary_win=False
        for r in range(self.rows):
            for f in [lambda row=r: self.check_row(row),
                        lambda row=r: self.check_diag1(row,0),
                        lambda row=r: self.check_diag2(row,self.cols-1)]:
                    winner = f()
                    if winner == self.moved:
                        return winner
                    if winner == self.to_move:
                        adversary_win = True
        for c in range(self.cols):
            for f in [lambda col=c: self.check_col(col),
                          lambda col=c: self.check_diag1(0,col),
                          lambda col=c: self.check_diag2(0,col)]:
                    winner = f()
                    if winner == self.moved:
                        return winner
                    if winner == self.to_move:
                        adversary_win = True
        if adversary_win:
            return self.to_move
        return None
 
class MCTSNode:
    def __init__(self, game_state, parent=None, move=None):
        self.state = game_state
        self.parent = parent
        self.move = move
        self.children = []
        self.wins = 0.0
        self.visits = 0
        self._untried = game_state.legal_moves()
        random.shuffle(self._untried)

    def is_fully_expanded(self):
        return len(self._untried) == 0

    def uct_score(self, c=math.sqrt(2)):
        if self.visits == 0:
            return float("inf")
        return self.wins / self.visits + c * math.sqrt(math.log(self.parent.visits) / self.visits)

    def best_child(self, c=math.sqrt(2)):
        return max(self.children, key=lambda n: n.uct_score(c))

class MCTS:
    def __init__(self, iterations=600, c=math.sqrt(2), max_depth=40):
        self.iterations = iterations
        self.c = c
        self.max_depth = max_depth

    def choose_move(self, game_state):
        root = MCTSNode(game_state.clone())
        if not root._untried:
            return None
        original_player = game_state.to_move
        for _ in range(self.iterations):
            node = self._select(root)
            if not node.state.is_terminal():
                node = self._expand(node)
            result = self._simulate(node, original_player)
            self._backpropagate(node, result, original_player)
        return max(root.children, key=lambda n: n.visits).move

    def _select(self, node):
        while not node.state.is_terminal() and node.is_fully_expanded() and node.children:
            node = node.best_child(self.c)
        return node

    def _expand(self, node):
        if node._untried:
            move = node._untried.pop()
            new_game = node.state.clone()
            new_game.make_move(move[0], move[1])
            new_game.change_to_move()
            child = MCTSNode(new_game, parent=node, move=move)
            node.children.append(child)
            return child
        return node

    def _rollout_move(self, sim):
        moves = sim.legal_moves()
        return random.choice(moves)

    def _simulate(self, node, original_player):
        sim = node.state.clone()
        depth = 0
        while not sim.is_terminal() and depth < self.max_depth:
            moves = sim.legal_moves()
            if not moves:
                break
            action, col = self._rollout_move(sim)
            sim.make_move(action, col)
            sim.change_to_move()
            depth += 1
        return sim.get_result(original_player)

    def _backpropagate(self, node, result, original_player):
        while node is not None:
            node.visits += 1
            node_player = node.state.moved
            if node_player == original_player:
                node.wins += result
            else:
                node.wins -= result
            node = node.parent

def play(player_X, player_O, show=True):
    ai_x = player_X
    ai_o = player_O

    jogo = Poupout(6, 7)
    state_counts = defaultdict(int)
    state_counts[jogo.board_key()] += 1

    while True:
        if show:
            jogo.display()
        winner = jogo.check_win()
        if winner is not None:
            if show:
                print(f"Parabens, {winner} ganhou!")
            break
        if jogo.draw:
            if show:
                print("Empate!")
            break

        jogador = ai_x if jogo.to_move == "X" else ai_o
        if show:
            print(f"IA ({jogo.to_move}) a pensar...")
        jogada = jogador.choose_move(jogo)
        action, col = jogada
        if show:
            print(f"  -> IA jogou: {action} coluna {col}")
        if jogada not in jogo.legal_moves():
            if show:
                print("Tentativa de jogada ilegal!")
            return None
        jogo.make_move(action, col)
        state_counts[jogo.board_key()] += 1
        jogo.check_repeat(state_counts)
        jogo.change_to_move()
    if winner is not None:
        return winner
    return None

def simulate_games(Player1, Player2, n_games):
    games_set1=[]
    games_set2=[]
    p1_wins=0
    p2_wins=0
    #como o primeiro a jogar tem uma clara vantagem são realizados jogos de ambos os lados
    for _ in range(n_games//2):
        players={"X":Player1, "O":Player2}
        games_set1.append(play(players["X"], players["O"], show=False))
    p1_wins+=games_set1.count("X")
    p2_wins+=games_set1.count("O")
    for _ in range(n_games//2):
        players={"X":Player2, "O":Player1}
        games_set2.append(play(players["X"], players["O"], show=False))
    p2_wins+=games_set2.count("X")
    p1_wins+=games_set2.count("O")
    games=games_set1 + games_set2
    return (p1_wins, p2_wins, games)
