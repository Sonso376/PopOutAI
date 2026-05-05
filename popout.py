import random
import math
import copy

class Poupout:
    def __init__(self,rows,cols,moved="O",to_move="X"):
        self.rows=rows
        self.cols=cols
        self.moved=moved
        self.to_move=to_move
        self.board=list()
        for c in range(cols):
            line=list()
            for r in range(rows):
                line.append("-")
            self.board.append(line)
        self.n_pieces=0
        self.repeated=False
        self.last_move=None
        self.draw=False
    
    def display(self):
        print("  " + " ".join(str(i) for i in range(self.cols)))
        for r in range(self.rows):
            print("  ", end="")
            for c in range(self.cols):
                print(self.board[c][r], end="")
            print("")

    def put(self, column):
        if self.board[column][0]!="-":
            raise Exception("Ação impossível")
        i=self.rows-1
        while True:
            if i<0:
                return
            if self.board[column][i]=="-":
                self.board[column][i]=self.to_move
                self.n_pieces+=1
                return
            else:
                i-=1
    
    def pop(self, column):
        if self.board[column][-1]!=self.to_move:
            raise Exception("Ação impossível")
        self.board[column]=["-"] + self.board[column][:-1]
        self.n_pieces-=1

    def change_to_move(self):
        temp=self.to_move
        self.to_move=self.moved
        self.moved=temp

    def make_move(self, move, column):
        try:
            if move=="put":
                self.put(column)
            elif move=="pop":
                self.pop(column)
            elif move=="draw" and (self.repeated or self.check_full()):
                self.draw=True
            else:
                return False
            self.last_move=(move,column)
            return True
        except:
            return False
        
    def check_row(self, row):
        line=""
        for i in range(self.cols):
            line+=self.board[i][row]
        moved=self.moved*4
        if line.find(moved)!=-1:
            return self.moved
        to_move=self.to_move*4
        if line.find(to_move)!=-1:
            return self.to_move
        return None
    
    def check_col(self, col):
        line=""
        for i in range(self.rows):
            line+=self.board[col][i]
        moved=self.moved*4
        if line.find(moved)!=-1:
            return self.moved
        to_move=self.to_move*4
        if line.find(to_move)!=-1:
            return self.to_move
        return None

    def check_diag1(self,row,col):
        cells=min(self.rows-row,self.cols-col)
        if cells<4:
            return None
        line=""
        for i in range(cells):
            line+=self.board[col+i][row+i]
        moved=self.moved*4
        if line.find(moved)!=-1:
            return self.moved
        to_move=self.to_move*4
        if line.find(to_move)!=-1:
            return self.to_move
        return None
    
    def check_diag2(self,row,col):
        cells=min(self.rows-row,col+1)
        if cells<4:
            return None
        line=""
        for i in range(cells):
            line+=self.board[col-i][row+i]
        moved=self.moved*4
        if line.find(moved)!=-1:
            return self.moved
        to_move=self.to_move*4
        if line.find(to_move)!=-1:
            return self.to_move
        return None
        
    def check_win(self):
        if self.last_move is None:
            return None
        move, column= self.last_move
        adversary_win=False
        if move=="put":
            row=self.board[column].index(self.moved)
            winner=self.check_row(row)
            if winner is not None:
                return winner
            winner=self.check_col(column)
            if winner is not None:
                return winner    
            winner=self.check_diag1(max(0,row-column),max(0,column-row))
            if winner is not None:
                return winner
            winner=self.check_diag2(max(0,row-(self.cols-1-column)),min(self.cols-1,row+column))
            if winner is not None:
                return winner
        if move=="pop":
            for row in range(self.rows-1, -1, -1):
                if self.board[column][row]=="-":
                    break
                winner=self.check_row(row)
                if winner == self.moved:
                    return winner
                elif winner==self.to_move:
                    adversary_win=True
                winner=self.check_diag1(max(0,row-column),max(0,column-row))
                if winner == self.moved:
                    return winner
                elif winner==self.to_move:
                    adversary_win=True
                winner=self.check_diag2(max(0,row-(self.cols-1-column)),min(self.cols-1,row+column))
                if winner == self.moved:
                    return winner
                elif winner==self.to_move:
                    adversary_win=True
        if adversary_win:
            return self.to_move
        return None
    
    def check_full(self):
        return self.n_pieces==self.rows*self.cols

    def check_repeat(self, states, states_dict):
        if self.repeated:
            return True
        elif states_dict[self.n_pieces]>=3:
            for s in states[self.n_pieces]:
                if states[self.n_pieces].count(s)>=3:
                    self.repeated=True
                    return True
        return False
    
    def clone(self):
        """Cópia profunda do estado — usada nas simulações do MCTS."""
        new = Poupout(self.rows, self.cols, self.moved, self.to_move)
        new.board = copy.deepcopy(self.board)
        new.n_pieces = self.n_pieces
        new.repeated = self.repeated
        new.last_move = self.last_move
        # não copiamos states/states_dict para poupar memória nas simulações
        return new

    def legal_moves(self):
        """Retorna lista de (ação, coluna) possíveis para o jogador actual."""
        moves = []
        for c in range(self.cols):
            if self.board[c][0] == "-":           # drop: coluna não cheia
                moves.append(("put", c))
            if self.board[c][-1] == self.to_move: # pop: peça própria no fundo
                moves.append(("pop", c))
        if self.repeated or self.check_full():
            moves.append(("draw",0))
        return moves

    def is_terminal(self):
        """True se o jogo acabou."""
        return (self.check_win() is not None
                or self.draw)

    def get_result(self, maximizing_player):
        """
        Retorna o resultado do ponto de vista de maximizing_player:
          +1 vitória, -1 derrota, 0 empate
        """
        winner = self.check_win()
        if winner == maximizing_player:
            return 1
        if winner is not None:
            return -1
        else:
            return 0  # empate
 
class MCTSNode:
    def __init__(self, game_state, parent=None, move=None):
        self.state    = game_state   # instância Poupout (clonada)
        self.parent   = parent
        self.move     = move         # (ação, coluna) que originou este nó
        self.children = []
        self.wins     = 0.0
        self.visits   = 0
        # movimentos ainda não expandidos
        self._untried = game_state.legal_moves()
        random.shuffle(self._untried)

    def is_fully_expanded(self):
        return len(self._untried) == 0

    def uct_score(self, c=math.sqrt(2)):
        if self.visits == 0:
            return float('inf')
        return (self.wins / self.visits
                + c * math.sqrt(math.log(self.parent.visits) / self.visits))

    def best_child(self, c=math.sqrt(2)):
        return max(self.children, key=lambda n: n.uct_score(c))

class MCTS:
    def __init__(self, iterations=600, c=math.sqrt(2), max_depth=40):
        self.iterations = iterations
        self.c          = c
        self.max_depth  = max_depth

    def choose_move(self, game_state):
        """Ponto de entrada: recebe o estado actual, devolve (ação, coluna)."""
        root = MCTSNode(game_state.clone())

        for _ in range(self.iterations):
            node   = self._select(root)
            if not node.state.is_terminal():
                node = self._expand(node)
            result = self._simulate(node, game_state.to_move)
            self._backpropagate(node, result, game_state.to_move)

        # escolhe o filho com MAIS VISITAS (mais robusto que maior win-rate)
        best = max(root.children, key=lambda n: n.visits)
        return best.move

    # ── SELECTION ─────────────────────────────────────
    def _select(self, node):
        while not node.state.is_terminal() and node.is_fully_expanded():
            node = node.best_child(self.c)
        return node

    # ── EXPANSION ─────────────────────────────────────
    def _expand(self, node):
        if node._untried:
            move     = node._untried.pop()
            new_game = node.state.clone()  
            new_game.make_move(move[0], move[1])
            new_game.change_to_move()
            child = MCTSNode(new_game, parent=node, move=move)
            node.children.append(child)
            return child
        return node

    # ── SIMULATION (rollout aleatório) ─────────────────
    def _simulate(self, node, original_player):
        sim   = node.state.clone()
        depth = 0
        while not sim.is_terminal() and depth < self.max_depth:
            moves = sim.legal_moves()
            if not moves:
                break
            action, col = random.choice(moves)
            sim.make_move(action, col)
            sim.change_to_move()
            depth += 1
        return sim.get_result(original_player)

    # ── BACKPROPAGATION ────────────────────────────────
    def _backpropagate(self, node, result, original_player):
        while node is not None:
            node.visits += 1
            # o nó pertence ao jogador que jogou para chegar aqui
            node_player = node.state.moved  # quem acabou de jogar
            if node_player == original_player:
                node.wins += result          # +1, -1, ou 0
            else:
                node.wins -= result          # perspectiva inversa
            node = node.parent


# ─────────────────────────────────────────────────────────
#  LOOP PRINCIPAL — com selecção de modo no início
# ─────────────────────────────────────────────────────────

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
