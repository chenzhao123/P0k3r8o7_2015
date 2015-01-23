QActions = ["FOLD",
            "CHECK",
            "CALL",
            "ODDS1.0",
            "ODDS1.5",
            "ODDS2.0",
            "ODDS3.0"]

class PrevAction:
    """ Create previous action stats """
    def __init__(self, ch1, ra1, rn1, fd1,
                       ch2, ra2, rn2, fd2):
        self.opp1Fold = fd1 # folded or not
        self.opp1CheckCallNum = ch1 # checked or not this street, boolean (2)
        self.opp1Amt = ra1 # total call/bet/raise amount this street, discretized (6)
        self.opp1Aggr = int(rn1 >= ch1)

        self.opp2Fold= fd2
        self.opp2CheckCallNum = ch2
        self.opp2Amt  = ra2
        self.opp2Aggr = int(rn2 >= ch2)

    def __hash__(self):
        return int(1e5 * self.opp1CheckCallNum + 1e4 * self.opp1Amt + 1e3 * self.opp1Aggr + 1e2 * self.opp2CheckCallNum + 1e1 * self.opp2Amt + 1e0 * self.opp2Aggr)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

class QState:
    def __init__(self, pos, eq, st, act):
        self.numOppFold = int(act.opp1Fold) + int(act.opp2Fold)
        self.position = pos  # dealer or not dealer
        self.equity = eq  # index
        self.street = st  # (4)
        self.prevAction = act #

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return int(1e4 * self.prevAction.__hash__() + \
                1e3 * self.numOppFold + \
                1e2 * self.position + \
                1e1 * self.equity + \
                1e0 * self.street)


def discretizeAmt(amount):
    """return index of discretized amount, starting at 0"""
    interval = [6, 12, 24, 48, 96]
    return sum(i < amount for i in interval)

def discretizeEq(equity, numPlayers, street):
    """return index of discretized equity, starting at 0"""
    interval2 = [0.4, 0.55, 0.7]
    interval3 = [0.3, 0.375, 0.45]

    if (numPlayers == 2):
        interval = [interval2[0]+0.01*street,
                    interval2[1]+0.02*street,
                    interval2[2]+0.03*street]
    else:
        interval = [interval3[0]+0.02*street,
                    interval3[1]+0.04*street,
                    interval3[2]+0.06*street]
    return sum(i < equity for i in interval)

class QStateActionPair():
    def __init__(self, qstate, qaction):
        self.qstate = qstate   # QState
        self.qaction = qaction # string

    def __hash__(self):
        assert self.qaction in QActions
        return 100 * self.qstate.__hash__() + QActions.index(self.qaction)

    #def __repr__(self):
    #    return str(self.qstate) + "|" + self.qaction
