from QStates import *
import random
import pickle
import time
import math

class QLearn:
    def __init__(self, actions, epsilon=0.3, alpha=0.1, gamma=1.0):
        self.q = {}
        self.count = {}

        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma
        self.actions = actions
        self.toBeProcessed = []

    def getQ(self, state, action):
        return self.q.get(QStateActionPair(state, action), 0.0)
        # return self.q.get((state, action), 1.0)

    def learnQ(self, state, action, reward, value):

        return 

        oldv = self.q.get((state, action), None)
        print "learning... old qvalue is ", oldv
        if oldv is None:
            self.q[(state, action)] = reward
            self.count[(state, action)] = 1
        else:
            oldcount = self.count.get((state, action), 0)
            if oldcount:
                self.q[(state, action)] = float(oldv*oldcount + reward)/(oldcount + 1)
                self.count[(state, action)] = oldcount + 1
            else:
                print "ERROR: Count is 0 but qfile has qvalue"
                self.q[(state, action)] = reward
                self.count[(state, action)] = 1
            #self.q[(state, action)] = oldv + self.alpha * (value - oldv)
        print "learning... new qvalue is ", self.q[(state, action)]

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
            action = self.pickRandomPokerAction(equity, potSize, bet_metric)
            self.toBeProcessed.append(QStateActionPair(state, action))
            return action

        count = q.count(maxQ)
        if count > 1:
            best = [i for i in range(len(self.actions)) if q[i] == maxQ]
            i = random.choice(best)
            if i == "FOLD":
                rand = random.uniform(0,1)
                if rand < 0.5:
                    i = random.choice(best)

        else:
            i = q.index(maxQ)

        action = self.actions[i]
        print "(action, value) chosen is (%s, %.2f)" %(action, maxQ)
        self.toBeProcessed.append(QStateActionPair(state, action))

        if return_q: # if they want it, give it!
            return action, q
        return action

    def learn(self, state1, action1, reward, state2):
        maxqnew = max([self.getQ(state2, a) for a in self.actions])
        print "learning... maxqnew is ", maxqnew
        self.learnQ(state1, action1, reward, reward + self.gamma*maxqnew)

    def learnTerminalCase(self, reward, state, action):
        self.learnQ(state, action, reward, reward + self.gamma*reward)

    def learnAll(self, reward):
        if len(self.toBeProcessed) == 0:
            return

        print "processing toBeProcessed with"
        for i in self.toBeProcessed:
            print i.qstate.__hash__(), i.qaction

        self.learnTerminalCase(reward, self.toBeProcessed[-1].qstate, self.toBeProcessed[-1].qaction)
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
        except (IOError, KeyError, EOFError) as e:
            print e
            self.q = {}

    def loadCount(self, filename):
        try:
            print "reading count file", time.asctime()
            with open(filename, 'r') as f:
                self.count = pickle.load(f)
            print "done reading count file", time.asctime()
        except (IOError, KeyError, EOFError) as e:
            print e
            self.count = {}

    def dumpInfo(self, filename, info):
        print "writing file", filename, time.asctime()
        with open(filename, 'w') as f:
            pickle.dump(info, f)
        print "done writing file", filename, time.asctime()

    def pickRandomPokerAction(self, equity, potSize, bet_metric):
        print "Choosing random action with eq: %.2f, potSize: %i, bet_metric: %i" %(equity, potSize, bet_metric)
        
        actions = ["FOLD", "CHECK", "CALL", "ODDS2.0", "ODDS1.0"]
        if abs(bet_metric) < 1 or potSize < 2:
            odds = 50
        else:
            odds = potSize/bet_metric
        odds = max(1, odds)
        equity = max(0, equity)
        aggro = math.sqrt(0.7*math.sqrt(equity) + 0.3*math.log10(odds))
        print "Aggro is %.2f" %aggro

        if aggro > 1:
            aggro = 1
        aggro = aggro * (len(actions)-1)
        distances = [abs(elt - aggro) for elt in range(len(actions)-1)]
        upperbound = max(distances) * 1.2
        probabilities = [upperbound - elt for elt in distances]
        probabilities[1] = probabilities[1] * 1.3
        probabilities[2] = probabilities[2] * 1.3
        sum_prob = sum(probabilities)
        scaled_probs = [float(elt)/float(sum_prob) for elt in probabilities]

        print "Scaled probs is ", scaled_probs
        rand = random.uniform(0,1)
        print "Random number is ", rand
        counter = 0
        while rand > 0:
            rand = rand - scaled_probs[counter]
            counter += 1
        print counter
        counter = min(counter, len(scaled_probs) - 1)
        print "Action chosen is %s" %actions[counter-1]

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
