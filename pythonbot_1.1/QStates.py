from enum import Enum

class Street(Enum):
    preflop = 0
    flop = 1
    turn = 2
    river = 3

class RaiseSize():
    gran = 10
    def __init__(self, size):
        self.size = size/gran
    def __eq__(self, other):
        return self.size == self.size

class PrevAction:
    """ Create previous action stats """
    def __init__(self, ca1, ch1, fd1, ra1, rn1,
                       ca2, ch2, fd2, ra2, rn2):
        self.opp1CallNum  = ca1 # number of times called this street (~3)
        self.opp1CheckNum = ch1 # checked or not this street, boolean (2)
        self.opp1FoldNum  = fd1  # folded or not, boolean (2)
        self.opp1RaiseAmt = ra1 # total raise amount this street, discretized (10?)
        self.opp1RaiseNum = rn1 # number of times bet/raised this street (~4)
        # bets and raises are combined here, but we can split it up if we want

        self.opp2CallNum  = ca2 
        self.opp2CheckNum = ch2
        self.opp2FoldNum  = fd2
        self.opp2RaiseAmt = ra2
        self.opp2RaiseNum = rn2

        # total states here: 480^2 ~~ 2300
        
    def __eq__(self, other):
        if (type(other) is type(self):
            return self.__dict__ == other.__dict__
       return False 

class QState:
    def __init__(self, pos, eq, st, act):
        self.position = pos  # (3)
        self.equity = eq  # discretize (20)
        self.street = st  # (4)
        self.prevAction = act # (2300)
        # total states: 3*20*4*2300 
        
    def setPosition(pos): self.position = pos
    def setEquity(eq): self.equity = eq
    def setStreet(st): self.street = st
    def setPrevAction(act): self.prevAction = act

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


