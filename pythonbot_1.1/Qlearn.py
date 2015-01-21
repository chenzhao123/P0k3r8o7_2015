from QStates import *
import random
import pickle
import time
import math

class QLearn:
    def __init__(self, actions, epsilon=0.3, alpha=0.2, gamma=1.0):
        self.q = {}

        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma
        self.actions = actions
        self.toBeProcessed = []

    def getQ(self, state, action):
        return self.q.get(QStateActionPair(state, action), 0.0)
        # return self.q.get((state, action), 1.0)

    def learnQ(self, state, action, reward, value):
        oldv = self.q.get((state, action), None)
        if oldv is None:
            self.q[(state, action)] = reward
        else:
            self.q[(state, action)] = oldv + self.alpha * (value - oldv)

    def chooseAction(self, state, equity, potSize, bet_metric, return_q=False):
        print "(action, value) values for (state, a) is ", [(a, self.getQ(state, a)) for a in self.actions]
        q = [self.getQ(state, a) for a in self.actions]
        maxQ = max(q)

        if random.random() < self.epsilon:
            '''
            #action = random.choice(self.actions)
            #minQ = min(q); mag = max(abs(minQ), abs(maxQ))
            minQ = min(q); mag = abs(maxQ-minQ)
            #q = [q[i] + random.random() * mag - .5 * mag for i in range(len(self.actions))] # add random values to all the actions, recalculate maxQ
            q = [q[i] + random.random() * 3 * mag for i in range(len(self.actions))] # add random values to all the actions, recalculate maxQ
            maxQ = max(q)
            '''
            return pickRandomPokerAction(equity, potSize, bet_metric)

        count = q.count(maxQ)
        if count > 1:
            best = [i for i in range(len(self.actions)) if q[i] == maxQ]
            i = random.choice(best)
        else:
            i = q.index(maxQ)

        action = self.actions[i]
        self.toBeProcessed.append(QStateActionPair(state, action))

        if return_q: # if they want it, give it!
            return action, q
        return action

    def learn(self, state1, action1, reward, state2):
        maxqnew = max([self.getQ(state2, a) for a in self.actions])
        print "learning... maxqnew is ", maxqnew
        self.learnQ(state1, action1, reward, reward + self.gamma*maxqnew)

    def learnAll(self, reward):
        print "processing toBeProcessed with"
        for i in self.toBeProcessed:
            print i

        for i in xrange(len(self.toBeProcessed)-2,-1,-1):
            state1 = self.toBeProcessed[i].qstate
            action1 = self.toBeProcessed[i].qaction
            state2 = self.toBeProcessed[i+1].qstate
            self.learn(state1, action1, reward, state2)
            print "Q value:", self.getQ(state1, action1)
        self.toBeProcessed = []

    def printQ(self):
        keys = self.q.keys()
        states = list(set([a for a,b in keys]))
        actions = list(set([b for a,b in keys]))

        dstates = ["".join([str(int(t)) for t in list(tup)]) for tup in states]
        print (" "*4) + " ".join(["%8s" %("("+s+")") for s in dstates])
        for a in actions:
            print ("%3d " % (a)) + \
                " ".join(["%8.2f" % (self.getQ(s,a)) for s in states])

    def printV(self):
        keys = self.q.keys()
        states = [a for a,b in keys]
        statesX = list(set([x for x,y in states]))
        statesY = list(set([y for x,y in states]))

        print (" "*4) + " ".join(["%4d" % (s) for s in statesX])
        for y in statesY:
            maxQ = [max([self.getQ((x,y),a) for a in self.actions])
                    for x in statesX]
            print ("%3d " % (y)) + " ".join([ff(q,4) for q in maxQ])


    def loadQ(self, filename):
        try:
            print "reading qfile", time.asctime()
            with open(filename, 'r') as f:
                self.q = pickle.load(f)
            print "done reading qfile", time.asctime()
        except (IOError, KeyError) as e:
            print e
            self.q = {}

    def dumpQ(self, filename):
        print "writing file", time.asctime()
        with open(filename, 'w') as f:
            pickle.dump(self.q, f)
        print "done writing file", time.asctime()

    def pickRandomPokerAction(self, equity, potSize, bet_metric):
        actions = ["FOLD", "CHECK", "CALL", "ODD4.0", "ODD3.0", "ODD2.0", "ODD1.5", "ODD1.0"]
        if abs(bet_metric) < 1 or potSize < 2:
            odds = 50
        else:
            odds = potSize/bet_metric
        aggro = 0.7*math.sqrt(equity) + 0.3*math.log10(odds)
        if aggro > 1:
            aggro = 1
        aggro = aggro * 7
        distances = [elt - aggro for elt in range(8)]
        upperbound = max(distances) * 1.2
        probabilities = [upperbound - elt for elt in distances]
        probabilities[1] = probabilities[1] * 1.5
        probabilities[2] = probabilities[2] * 1.5
        sum_prob = sum(probabilities)
        scaled_probs = [float(elt)/float(sum_prob) for elt in probabilities]

        rand = random.uniform(0,1)
        counter = 0
        while rand > 0:
            rand = rand - scaled_probs[counter]
            counter += 1

        return actions[counter - 1]




import math
def ff(f,n):
    fs = "{:f}".format(f)
    if len(fs) < n:
        return ("{:"+n+"s}").format(fs)
    else:
        return fs[:n]
    # s = -1 if f < 0 else 1
    # ss = "-" if s < 0 else ""
    # b = math.floor(math.log10(s*f)) + 1
    # if b >= n:
    #     return ("{:" + n + "d}").format(math.round(f))
    # elif b <= 0:
    #     return (ss + ".{:" + (n-1) + "d}").format(math.round(f * 10**(n-1)))
    # else:
    #     return ("{:"+b+"d}.{:"+(n-b-1)+"
