QActions = ["FOLD",
            "CHECK",
            "BET10",
            "BET20",
            "BET30",
            "BET40",
            "BET50",
            "BET60",
            "BET70",
            "BET80",
            "BET90"]

class PrevAction:
    """ Create previous action stats """
    def __init__(self, ch1, ra1, rn1, fd1,
                       ch2, ra2, rn2, fd2):
        self.opp1Fold = fd1 # folded or not
        self.opp1CheckCallNum = ch1 # checked or not this street, boolean (2)
        self.opp1Amt = ra1 # total call/bet/raise amount this street, discretized (10?)
        self.opp1BetRaiseNum = rn1 # number of times bet/raised this street (~4), <= 3
        # bets and raises are combined here, but we can split it up if we want

        self.opp2Fold  = fd2
        self.opp2CheckCallNum = ch2
        self.opp2Amt  = ra2
        self.opp2BetRaiseNum = rn2

    def __hash__(self):
        return int(1e7 * self.opp1Fold + \
                1e6 * self.opp1CheckCallNum + \
                1e5 * self.opp1Amt + \
                1e4 * self.opp1BetRaiseNum + \
                1e3 * self.opp2Fold + \
                1e2 * self.opp2CheckCallNum + \
                1e1 * self.opp2Amt + \
                1e0 * self.opp2BetRaiseNum)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

class QState:
    def __init__(self, pos, eq, st, act):
        self.position = pos  # (2, 1 if last or 0 if not last)
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
        return int(1e3 * self.prevAction.__hash__() + \
                1e2 * self.position + \
                1e1 * self.equity + \
                1e0 * self.street)


def discretizeAmt(amount):
    """return index of discretized amount, starting at 0"""
    interval = [2, 6, 12, 24, 48, 96]
    return sum(i < amount for i in interval)

def discretizeEq(equity, numPlayers):
    """return index of discretized equity, starting at 0"""
    if (numPlayers == 2):
        interval = [0.2, 0.325, 0.45, 0.575, 0.7]
    else:
        interval = [0.16, 0.27, 0.38, 0.49, 0.6]
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
