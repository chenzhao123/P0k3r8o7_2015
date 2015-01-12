class Card(object):
    rankMap = {'T':10, 'J':11, 'Q':12, 'K':13, 'A':14}
    def __init__(self, *args):
        if len(args) == 1:
            self.rank = args[0][0]
            self.suit = args[0][1]
        elif len(args) == 2:
            self.suit = args[0]
            self.rank = args[1]
        else:
            raise ValueError("Must have 1 argument (string) or 2 arguments (string suit, int rank)")

    def fromString(self, string):
        self.rank

    def __lt__(self, other):
        if (self.rank.isdigit() or other.rank.isdigit()):
            return self.rank < other.rank
        else:
            return Card.rankMap[self.rank] < Card.rankMap[other.rank]

    def __gt__(self, other):
        if (self.rank.isdigit() or other.rank.isdigit()):
            return self.rank > other.rank
        else:
            return Card.rankMap[self.rank] > Card.rankMap[other.rank]

    def __le__(self, other):
        if (self.rank.isdigit() or other.rank.isdigit()):
            return self.rank <= other.rank
        else:
            return Card.rankMap[self.rank] <= Card.rankMap[other.rank]

    def __ge__(self, other):
        if (self.rank.isdigit() or other.rank.isdigit()):
            return self.rank >= other.rank
        else:
            return Card.rankMap[self.rank] >= Card.rankMap[other.rank]

    def same_suit(self, other):
        return self.suit == other.suit

    def same_rank(self, other):
        return self.rank == other.rank
    
    def __eq__(self, other):
        return self.same_suit(other) and self.same_rank(other)    

    def __str__(self):
        return self.rank + self.suit
    

class LegalAction(object):
    def __init__(self, string):
        tokens = string.split(":")
        self.name = tokens[0]
        if (len(tokens) > 1):
            self.fields = tokens[1:]
        else:
            self.fields = None

class PerformedAction(object):
    def __init__(self, string):
        tokens = string.split(":")
        self.name = tokens[0]
        if (self.name != "DEAL"):
            self.actor = tokens[-1]
            self.fields = tokens[1:-1]
        else:
            self.actor = None
            self.fields = tokens[1]
         
class Action(object):
    def __init__(self, name, field=None):
        self.name = name
        self.field = field
 
def isValid(action, validActions):
    if action.name in validActions:
        validFields = validActions[action.name]
        if (validFields is not None):
            amt = int(action.field)
            if (action.name == "BET" or action.name == "RAISE"):
                return amt > int(validFields[0]) and amt < int(validFields[1])
            elif(action.name == "CALL"):
                return amt == int(validFields[0])
        else:
            return True
    else:
        return False
