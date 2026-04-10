import copy

class Poupout:
    def __init__(self,rows,cols,moved="O",to_move="X"):
        self.rows=rows
        self.cols=cols
        self.moved=moved
        self.to_move=to_move
        self.board=list()
        self.states=list()
        for c in range(cols):
            line=list()
            for r in range(rows):
                line.append("-")
            self.board.append(line)
        self.n_pieces=0
        self.repeated=False
        self.last_move=None
    
    def display(self):
        for r in range(self.rows):
            for c in range(self.cols):
                print(self.board[c][r],end="")
            print("")

    def put(self, column):
        if self.board[column][0]!="-":
            raise Exception("Ação impossível")
        i=0
        while True:
            if i==self.rows:
                return
            if self.board[column][-1-i]=="-":
                self.board[column][-1-i]=self.to_move
                self.n_pieces+=1
                return
            else:
                i+=1
    
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
                self.states.append(copy.deepcopy(self.board))
            elif move=="pop":
                self.pop(column)
                self.states.append(copy.deepcopy(self.board))
            else:
                return False
            self.last_move=(move,column)
            return True
        except:
            return False
        
    def check_row(self, row):
        counts={"X":0,"O":0}
        winners={"X":False, "O":False}
        for c in range(self.cols):
            if self.board[c][row]=="X":
                counts["X"]+=1
                counts["O"]=0
            elif self.board[c][row]=="O":
                counts["X"]=0
                counts["O"]+=1
            else:
                counts["X"]=0
                counts["O"]=0
            if counts["X"]>=4:
                winners["X"]=True
            elif counts["O"]>=4:
                winners["O"]=True
        if winners[self.moved]:
            return self.moved
        elif winners[self.to_move]:
            return self.to_move
        return None
    
    def check_col(self, col):
        counts={"X":0,"O":0}
        winners={"X":False, "O":False}
        for r in range(self.rows):
            if self.board[col][r]=="X":
                counts["X"]+=1
                counts["O"]=0
            elif self.board[col][r]=="O":
                counts["X"]=0
                counts["O"]+=1
            else:
                counts["X"]=0
                counts["O"]=0
            if counts["X"]>=4:
                winners["X"]=True
            elif counts["O"]>=4:
                winners["O"]=True
        if winners[self.moved]:
            return self.moved
        elif winners[self.to_move]:
            return self.to_move
        return None

    def check_diag1(self,row,col):
        counts={"X":0,"O":0}
        winners={"X":False, "O":False}
        for i in range(min(self.rows-row,self.cols-col)):
            if self.board[col+i][row+i]=="X":
                counts["X"]+=1
                counts["O"]=0
            elif self.board[col+i][row+i]=="O":
                counts["X"]=0
                counts["O"]+=1
            else:
                counts["X"]=0
                counts["O"]=0
            if counts["X"]>=4:
                winners["X"]=True
            elif counts["O"]>=4:
                winners["O"]=True
        if winners[self.moved]:
            return self.moved
        elif winners[self.to_move]:
            return self.to_move
        return None
    
    def check_diag2(self,row,col):
        counts={"X":0,"O":0}
        winners={"X":False, "O":False}
        for i in range(min(self.rows-row,col)):
            if self.board[col-i][row+i]=="X":
                counts["X"]+=1
                counts["O"]=0
            elif self.board[col-i][row+i]=="O":
                counts["X"]=0
                counts["O"]+=1
            else:
                counts["X"]=0
                counts["O"]=0
            if counts["X"]>=4:
                winners["X"]=True
            elif counts["O"]>=4:
                winners["O"]=True
        if winners[self.moved]:
            return self.moved
        elif winners[self.to_move]:
            return self.to_move
        return None
    
    def check_win(self):
        for r in range(self.rows):
            winner=self.check_row(r)
            if winner!=None:
                return winner
            winner=self.check_diag1(r,0)
            if winner!=None:
                return winner
            winner=self.check_diag2(r,self.cols-1)
            if winner!=None:
                return winner
        for c in range(self.cols):
            winner=self.check_col(c)
            if winner!=None:
                return winner
            winner=self.check_diag1(0,c)
            if winner!=None:
                return winner
            winner=self.check_diag2(0,c)
            if winner!=None:
                return winner
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

jogo=Poupout(6,7)
states=[]
states_dict=dict()
for i in range(jogo.rows*jogo.cols):
    states.append([])
    states_dict[i]=0
states[jogo.n_pieces].append(copy.deepcopy(jogo.board))
states_dict[jogo.n_pieces]+=1
while True:
    jogo.display()
    if jogo.check_win()!=None:
        print(f"Parabens {jogo.check_win()} ganhou!")
        break
    if jogo.check_full() or jogo.check_repeat(states,states_dict):
        empate=input("Declarar empate?")
        if empate=="y":
            break
    jogada=False
    while not jogada:
        move=input("")
        action=move.split()[0]
        col=int(move.split()[1])
        jogada=False
        jogada = jogo.make_move(action,col)
    states[jogo.n_pieces].append(copy.deepcopy(jogo.board))
    states_dict[jogo.n_pieces]+=1
    jogo.change_to_move()
    
