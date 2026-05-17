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

def main():
    print("=== PopOut ===")
    print("Modos disponíveis:")
    print("  1 - Humano vs Humano")
    print("  2 - Humano (X) vs IA (O)")
    print("  3 - IA vs IA")

    modo = ""
    while modo not in ("1", "2", "3"):
        modo = input("Escolhe o modo [1/2/3]: ").strip()

    ai_x = MCTS(iterations=int(input("Iteraçoes de X: "))) if modo == "3" else None
    ai_o = MCTS(iterations=int(input("Iteraçoes de O: "))) if modo in ("2", "3") else None

    jogo = Poupout(6, 7)
    states = []
    states_dict = dict()
    for i in range(jogo.rows * jogo.cols):
        states.append([])
        states_dict[i] = 0
    states[jogo.n_pieces].append(copy.deepcopy(jogo.board))
    states_dict[jogo.n_pieces] += 1

    while True:
        jogo.display()

        # verificar fim de jogo
        if jogo.check_win() is not None:
            print(f"Parabéns, {jogo.check_win()} ganhou!")
            break
        if jogo.draw:
            print("Empate!")
            break

        # decidir quem joga agora
        ai_actual = ai_x if jogo.to_move == "X" else ai_o

        jogada = False
        while not jogada:
            if ai_actual is not None:
                print(f"IA ({jogo.to_move}) a pensar...")
                action, col = ai_actual.choose_move(jogo)
                print(f"  -> IA jogou: {action} coluna {col}")
                jogada = jogo.make_move(action, col)
            else:
                if jogo.repeated or jogo.check_full():
                    print("É possível empatar o jogo [draw 0]")
                entrada = input(f"Jogador {jogo.to_move} [ex: put 3 / pop 2]: ").strip()
                try:
                    parts  = entrada.split()
                    action = parts[0]
                    col    = int(parts[1])
                    jogada = jogo.make_move(action, col)
                    if not jogada:
                        print("  Movimento inválido, tenta de novo.")
                except (IndexError, ValueError):
                    print("  Formato inválido. Usa: put 3  ou  pop 2")

        states[jogo.n_pieces].append(copy.deepcopy(jogo.board))
        states_dict[jogo.n_pieces] += 1
        jogo.check_repeat(states=states, states_dict=states_dict)
        jogo.change_to_move()


main()
