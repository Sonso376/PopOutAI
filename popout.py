
# ============================================================
# Trabalho IA 2025/2026 - PopOut + MCTS + Decision Tree ID3
# ============================================================
# Requisitos cumpridos:
# 1) PopOut jogavel em 3 modos: Humano vs Humano, Humano vs IA, IA vs IA.
# 2) MCTS com UCT.
# 3) Geracao de dataset PopOut: pares (estado, melhor jogada MCTS).
# 4) Arvore de decisao ID3 feita de raiz, sem scikit-learn.
# 5) Discretizacao de atributos numericos para o dataset Iris.
# 6) Classificacao de novos exemplos e avaliacao de accuracy.

import random
import math
import copy
import csv
import time
import datetime
import numpy as np
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Optional

# -----------------------------
# POP OUT
# -----------------------------

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


# -----------------------------
# MCTS + UCT
# -----------------------------

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


# -----------------------------
# ID3 feito de raiz
# -----------------------------

@dataclass
class ID3Node:
    prediction: Any
    attribute: Optional[str] = None
    children: Optional[Dict[Any, "ID3Node"]] = None
    is_leaf: bool = False

    def classify(self, example):
        if self.is_leaf or self.attribute is None:
            return self.prediction
        value = example.get(self.attribute)
        if self.children and value in self.children:
            return self.children[value].classify(example)
        return self.prediction

    def pretty(self, indent=""):
        if self.is_leaf:
            return indent + f"Classe: {self.prediction}\n"
        s = indent + f"Se {self.attribute}:\n"
        for value, child in sorted(self.children.items(), key=lambda x: str(x[0])):
            s += indent + f"  = {value} ->\n"
            s += child.pretty(indent + "    ")
        return s

class ID3DecisionTree:
    def __init__(self, max_depth=None, min_samples_split=2):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.root = None
        self.label_col = None

    @staticmethod
    def entropy(labels):
        total = len(labels)
        counts = Counter(labels)
        return -sum((cnt/total) * math.log2(cnt/total) for cnt in counts.values() if cnt)

    def information_gain(self, rows, attribute, label_col):
        base = self.entropy([r[label_col] for r in rows])
        total = len(rows)
        parts = defaultdict(list)
        for r in rows:
            parts[r[attribute]].append(r)
        remainder = sum((len(part)/total) * self.entropy([r[label_col] for r in part]) for part in parts.values())
        return base - remainder

    def majority_label(self, rows, label_col):
        return Counter(r[label_col] for r in rows).most_common(1)[0][0]

    def fit(self, rows, label_col="label", attributes=None):
        if not rows:
            raise ValueError("Dataset vazio")
        self.label_col = label_col
        if attributes is None:
            attributes = [a for a in rows[0].keys() if a != label_col]
        self.root = self._id3(rows, attributes, label_col, depth=0)
        return self

    def _id3(self, rows, attributes, label_col, depth):
        labels = [r[label_col] for r in rows]
        majority = self.majority_label(rows, label_col)
        if len(set(labels)) == 1:
            return ID3Node(prediction=labels[0], is_leaf=True)
        if not attributes or len(rows) < self.min_samples_split or (self.max_depth is not None and depth >= self.max_depth):
            return ID3Node(prediction=majority, is_leaf=True)

        gains = [(self.information_gain(rows, a, label_col), a) for a in attributes]
        best_gain, best_attr = max(gains, key=lambda x: x[0])
        if best_gain <= 1e-12:
            return ID3Node(prediction=majority, is_leaf=True)

        node = ID3Node(prediction=majority, attribute=best_attr, children={}, is_leaf=False)
        values = sorted(set(r[best_attr] for r in rows), key=str)
        remaining = [a for a in attributes if a != best_attr]
        for v in values:
            subset = [r for r in rows if r[best_attr] == v]
            node.children[v] = self._id3(subset, remaining, label_col, depth + 1)
        return node

    def predict_one(self, example):
        if self.root is None:
            raise ValueError("A arvore ainda nao foi treinada")
        return self.root.classify(example)

    def predict(self, rows):
        return [self.predict_one(r) for r in rows]

    def score(self, rows, label_col=None):
        label_col = label_col or self.label_col
        preds = self.predict(rows)
        return sum(p == r[label_col] for p, r in zip(preds, rows)) / len(rows)

    def pretty(self):
        return self.root.pretty() if self.root else "<arvore vazia>"

def state_to_features(game):
    row = {}
    for c in range(game.cols):
        for r in range(game.rows):
            row[f"c{c}_r{r}"] = game.board[c][r]
    row["to_move"] = game.to_move
    for m in ["put", "pop"]:
        for c in range(game.cols):
            if (m,c) in game.legal_moves():
                row[f"{m}_{c}"]="T"
            else:
                row[f"{m}_{c}"]="F"
    return row

class ID3DecisionTreePlayer:
    def __init__(self, tree, changed_feature=False):
        self.tree=tree
        self.changed_feature=changed_feature

    def choose_move(self, state):
        game=state_to_features(state)
        if self.changed_feature:
            game=change_feature(game)
        move=self.tree.predict_one(game)
        move=move.split("_")
        return (move[0], int(move[1]))
    
class HumanPlayer:
    def choose_move(self,state):
        while True:
            move=input(f"Jogador {state.to_move} [ex: put 3 / pop 2]:") 
            move=move.split(" ")
            action=move[0]
            col=int(move[1])
            jogada=(action,col)
            if jogada in state.legal_moves():
                return jogada
            else:
                print("Jogada Impossível, Tente novamente")

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
        if show and not isinstance(jogador, HumanPlayer):
            print(f"IA ({jogo.to_move}) a pensar...")
        jogada = jogador.choose_move(jogo)
        action, col = jogada
        if show:
            print(f"  -> IA jogou: {action} coluna {col}")
        if jogada not in jogo.legal_moves():
            if show:
                print(f"Tentativa de jogada ilegal! Ganha o {jogo.moved}")
            return jogo.moved
        jogo.make_move(action, col)
        state_counts[jogo.board_key()] += 1
        jogo.check_repeat(state_counts)
        jogo.change_to_move()
    if winner is not None:
        return winner
    return None

def load_csv_dataset(path):
    with open(path) as file:
        ds=csv.DictReader(file)
        rows=[]
        for r in ds:
            rows.append(r)
        return rows
    
def change_feature(feature):
    new_feature={}
    for atr in feature:
        if feature[atr]=="T" or feature[atr]=="F" or atr=="move":
            new_feature[atr]=feature[atr]
            continue
        if atr=="to_move":
            continue
        if feature[atr]==feature["to_move"]:
            new_feature[atr]="P"
        elif feature[atr]!="-":
            new_feature[atr]="A" 
        else:
            new_feature[atr]="-"
    return new_feature
def change_dataset(rows):
    new_rows=[]
    for r in rows:
        new_rows.append(change_feature(r))
    return new_rows

def main():
    dataset_100_base=load_csv_dataset("datasets/popout_dataset_100_base.csv")
    dataset_1000_base=load_csv_dataset("datasets/popout_dataset_1000_base.csv")
    dataset_10000_base=load_csv_dataset("datasets/popout_dataset_10000_base.csv")
    dataset_1000_random=load_csv_dataset("datasets/popout_dataset_100_base.csv")
    dataset_1000_random=load_csv_dataset("datasets/popout_dataset_1000_base.csv")
    dataset_10000_random=load_csv_dataset("datasets/popout_dataset_10000_base.csv")
    dataset_misto1=dataset_1000_base + dataset_1000_random[:len(dataset_1000_random)//2]
    dataset_misto2=dataset_10000_base + dataset_10000_random[:len(dataset_10000_random)//4]
    dataset_changed=change_dataset(dataset_misto2)
    datasets={1:dataset_100_base,
              2:dataset_1000_base,
              3:dataset_10000_base,
              4:dataset_misto1,
              5:dataset_misto2,
              6:dataset_changed
             }

    print("=== PopOut ===")
    print("1 - Humano vs Humano")
    print("2 - Humano (X) vs IA (O)")
    print("3 - IA vs IA")
    modo = ""
    while modo not in ("1", "2", "3"):
        modo = input("Escolhe o modo [1/2/3]: ").strip()

    if modo=="1":
        ai_x=HumanPlayer()
        ai_o=HumanPlayer()
    else:
        if modo=="2":
            ai_x=HumanPlayer()
        else:
            ai_type=0
            while ai_type not in [1,2]:
                print("Escolha o tipo de AI de X:")
                print("(1) MCTS")
                print("(2) ID3 decision tree")
                ai_type=int(input(""))
            if ai_type==1:
                ai_x=MCTS(iterations=int(input("Iteracoes da AI de X: ")))
            else:
                d=0
                while d not in list(datasets.keys()):
                    print("Seleciona o dastaset a ser usado:")
                    print("(1) 100 iterações base")
                    print("(2) 1000 iterações base")
                    print("(3) 10000 iterações base")
                    print("(4) misto 1 (melhores)")
                    print("(5) misto 2 (melhores)")
                    print("(6) misto 2 alterado")
                    d=int(input(""))
                tree=ID3DecisionTree(max_depth=int(input("profundidade máxima da árvore de X: ")))
                tree.fit(datasets[d],label_col="move")
                ai_x=ID3DecisionTreePlayer(tree) if d!=6 else ID3DecisionTreePlayer(tree, changed_feature=True)
        ai_type=0
        while ai_type not in [1,2]:
            print("Escolha o tipo de AI de O:")
            print("(1) MCTS")
            print("(2) ID3 decision tree")
            ai_type=int(input(""))
        if ai_type==1:
            ai_o=MCTS(iterations=int(input("Iteracoes da AI de O: ")))
        else:
            d=0
            while d not in list(datasets.keys()):
                print("Seleciona o dastaset a ser usado:")
                print("(1) 100 iterações base")
                print("(2) 1000 iterações base")
                print("(3) 10000 iterações base")
                print("(4) misto 1 (melhores)")
                print("(5) misto 2 (melhores)")
                print("(6) misto 2 alterado")
                d=int(input(""))
            tree=ID3DecisionTree(max_depth=int(input("profundidade máxima da árvore de O: ")))
            tree.fit(datasets[d],label_col="move")
            ai_o=ID3DecisionTreePlayer(tree) if d!=6 else ID3DecisionTreePlayer(tree, changed_feature=True)
    
    play(ai_x, ai_o, show=True)

if __name__ == "__main__":
    # Para jogar, descomenta a linha seguinte:
    # main()
    pass

main()
