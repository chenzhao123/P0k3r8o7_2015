import argparse
import socket
import sys
import pbots_calc
import Parser
from BotUtils import *
import re
import random
from Qlearn import *
from QStates import *
import time

"""
Simple example pokerbot, written in python.

This is an example of a bare bones pokerbot. It only sets up the socket
necessary to connect with the engine and then always returns the same action.
It is meant as an example of how a pokerbot should communicate with the engine.
"""
class Player:
    def __init__(self):
        self.name = ""
        self.opp1 = ""
        self.opp2 = ""
        self.stack = 0.0
        self.startingStack = 0.0
        self.bb = 0.0
        self.seat = 0
        self.numHands = 0
        self.timeBank = 0.0
        self.keyvalues = {}
        self.card1 = None
        self.card2 = None
        self.handId = 0
        self.activePlayers = []
        self.opp1Stack = 0
        self.opp1Active = True
        self.opp1Stack = 0
        self.opp2Active = True
        self.active = True
        self.potSize = 0.0
        self.preflop = False
        self.flop = False
        self.turn = False
        self.river = False
        self.boardCards = []
        self.lastActions = []
        self.legalActions = {}
        self.bytesLeft = 0
        self.stats = {}
        self.newkeyvalues = {}
        self.equity = 0.0
        self.opp1Equity = 0.0
        self.opp2Equity = 0.0
        self.qfile = "QFile.txt"
        self.ai = QLearn(["FOLD", "CHECK", "CALL", "ODDS1.0", "ODDS2.0"],
                          epsilon=0.4, alpha=0.1, gamma=1.0)
        self.ai.loadQ(self.qfile)
        self.numHandsPlayed = 0
        self.numChipsGained = 0
        self.f = open('summary.txt', 'a')
        self.startingStreetPotSize = 3

    def run(self, input_socket):
        # Get a file-object for reading packets from the socket.
        # Using this ensures that you get exactly one packet per read.
        f_in = input_socket.makefile()
        packet_parser = Parser.Parser()
        #print "hi"
        while True:
            # Block until the engine sends us a packet.
            #print "before data", time.asctime()
            data = f_in.readline().strip()
            # If data is None, connection has closed.
            if not data:
                print "Gameover, engine disconnected."
                break

            # Here is where you should implement code to parse the packets from
            # the engine and act on it. We are just printing it instead.
            print data, time.asctime()
            packet_parser.parse(data)
            # When appropriate, reply to the engine with a legal action.
            # The engine will ignore all spurious responses.
            # The engine will also check/fold for you if you return an
            # illegal action.
            # When sending responses, terminate each response with a newline
            # character (\n) or your bot will hang!
            packet_type = data.split()[0]
            if packet_type == "NEWGAME":
                self.newgame(packet_parser.parser_dict)
            elif packet_type == "KEYVALUE":
                self.keyvalue(packet_parser.parser_dict)
            elif packet_type == "NEWHAND":
                self.newhand(packet_parser.parser_dict)
            elif packet_type == "GETACTION":
                # Currently CHECK on every move. You'll want to change this.
                #s.send("CHECK\n")
                resp = self.getaction(packet_parser.parser_dict)
                #print 'sending response', resp, time.asctime()
                s.send(resp+"\n")
                #print 'sent response', resp, time.asctime()
            elif packet_type == "HANDOVER":
                self.handover(packet_parser.parser_dict)
            elif packet_type == "REQUESTKEYVALUES":
                # At the end, the engine will allow your bot save key/value pairs.
                # Send FINISH to indicate you're done.
                #s.send("FINISH\n")
                print "dumping q values to", self.qfile
                self.ai.dumpQ(self.qfile)
                self.requestkeyvalues(packet_parser.parser_dict)
                for key in self.newkeyvalues:
                    s.send("PUT " + str(key) + " " + str(self.newkeyvalues[key]) + "\n")
                s.send("FINISH\n")
            #print "end while", time.asctime()
        # Clean up the socket.
        s.close()
        self.f.close()

    def newgame(self, parser_dict):
        self.name = parser_dict['yourName']
        self.opp1 = parser_dict['opp1Name']
        self.opp2 = parser_dict['opp2Name']
        self.stack = parser_dict['stackSize']
        self.startingStack = self.stack
        self.opp1Stack = self.stack
        self.opp2Stack = self.stack
        self.bb = parser_dict['bb']
        self.numHands = parser_dict['numHands']
        self.timeBank = parser_dict['timeBank']

    def keyvalue(self, parser_dict):
        for key in parser_dict:
          self.keyvalues[key] = parser_dict[key]

    def newhand(self, parser_dict):
        #print "new hand starts", time.asctime()
        self.card1 = Card(parser_dict['holeCard1'])
        self.card2 = Card(parser_dict['holeCard2'])
        self.handId = parser_dict['handId']
        self.seat = parser_dict['seat']
        p_index = 0
        self.startingStreetPotSize = 3
        self.activePlayers = parser_dict['activePlayers']
        for player_name in parser_dict['playerNames']:
            if player_name == self.opp1:
                self.opp1Stack = parser_dict['stackSizes'][p_index]
                self.opp1Active = parser_dict['activePlayers'][p_index]
                self.opp1Index = p_index
            elif player_name == self.opp2:
                self.opp2Stack = parser_dict['stackSizes'][p_index]
                self.opp2Active = parser_dict['activePlayers'][p_index]
                self.opp2Index = p_index
            elif player_name == self.name:
                self.stack = parser_dict['stackSizes'][p_index]
                self.active = parser_dict['activePlayers'][p_index]
                self.index = p_index
            p_index += 1
        self.startingStack = self.stack

    def getaction(self, parser_dict):
        #print "get action starts", time.asctime()
        self.potSize = parser_dict['potSize']
        numBoardCards = parser_dict['numBoardCards']
        lastStreet = len(self.boardCards)
        self.preflop = (numBoardCards == 0)
        self.flop = (numBoardCards == 3)
        self.turn = (numBoardCards == 4)
        self.river = (numBoardCards == 5)
        self.activePlayers = parser_dict['activePlayers']
        self.active = parser_dict['activePlayers'][self.index]
        self.opp1Active = parser_dict['activePlayers'][self.opp1Index]
        self.opp2Active = parser_dict['activePlayers'][self.opp2Index]
        self.stack = parser_dict['stackSizes'][self.index]
        self.opp1Stack = parser_dict['stackSizes'][self.opp1Index]
        self.opp2Stack = parser_dict['stackSizes'][self.opp2Index]

        if self.flop:
            self.boardCards = [Card(card) for card in parser_dict['boardCards']]
        if self.turn or self.river:
            self.boardCards.append(Card(parser_dict['boardCards'][-1]))

        #Resetting lastActions
        if (lastStreet != len(self.boardCards)):
            self.lastActions = []
            self.startingStreetPotSize = self.potSize


        self.lastActions.extend([PerformedAction(action) for action in parser_dict['lastActions']])
        for action in parser_dict['legalActions']:
            legalAction = LegalAction(action)
            self.legalActions[legalAction.name] = legalAction.fields
        self.timeBank = parser_dict['timeBank']
        response = self.getResponse()
        self.resetTurn()
        #print "get action ends", time.asctime()
        return response

    def handover(self, parser_dict):
        #print "handover starts", time.asctime()
        self.stack = parser_dict['stackSizes'][self.index]
        self.opp1Stack = parser_dict['stackSizes'][self.opp1Index]
        self.opp2Stack = parser_dict['stackSizes'][self.opp2Index]
        self.lastActions.extend([PerformedAction(action) for action in parser_dict['lastActions']])
        self.timeBank = parser_dict['timeBank']
        numBoardCards = parser_dict['numBoardCards']

        diffStack = self.stack - self.startingStack
        if numBoardCards == 0:
            reward = diffStack
        else:
            if diffStack > 0:
                reward = pow(diffStack, float(1)/numBoardCards)
            else:
                reward = -pow(abs(diffStack), float(1)/numBoardCards)
            '''
            reward = diffStack/2
        elif numBoardCards == 4:
            reward = diffStack/4
        else:
            reward = diffStack/8
            '''
        self.ai.learnAll(reward)

        self.f.write(str(diffStack) + "\n")

        self.numHandsPlayed += 1
        self.numChipsGained += diffStack
        if not self.numHandsPlayed % 1000:
            #self.f.write("Average winning per hand:" +  str(self.numChipsGained / 1000.0)) 
            self.numHandsPlayed = 0

        self.getstats()
        self.resetHand()
        #print "handover ends", time.asctime()

    def requestkeyvalues(self, parser_dict):
        self.bytesLeft = int(parser_dict['bytesLeft'])
        #Example to store new key values
        self.newkeyvalues[self.opp1] = self.stats[self.opp1]

    def getResponse(self):
        #print "get response starts", time.asctime()
        myCards = str(self.card1) + str(self.card2)
        boardCards = "".join(str(card) for card in self.boardCards)
        deadCards = ""
        opp1Cards = "xx"
        opp2Cards = "xx"
        holeCardsInput = myCards + ":" + opp1Cards + ":" + opp2Cards
        eqResults = pbots_calc.calc(holeCardsInput, boardCards, deadCards, 10000)
        self.equity = eqResults.ev[0]
        self.opp1Equity = eqResults.ev[1]
        self.opp2Equity = eqResults.ev[2]

        state = self.createQState()
        #print "choose action starts", time.asctime()
        action = self.ai.chooseAction(state, self.equity, self.potSize, self.analyzePotOdds())
        #print "choose action ends", time.asctime()
        validAction = self.createValidAction(action)
        #print "create action ends", time.asctime()
        return validAction

        #TODO HERE

        '''
        if (self.equity > 0):
            if ("BET" in self.legalActions):
                minbet = "BET:" + self.legalActions["BET"][0] #minBet
                maxbet = "BET:" + self.legActions["BET"][1] #maxBet
            if ("RAISE" in self.legalActions):
                minraise = "RAISE:" + self.legalActions["RAISE"][0] #minRaise
                maxraise = "RAISE:" + self.legalActions["RAISE"][1] #maxRaise
            if ("CALL" in self.legalActions):
                call = "CALL:" + self.legalActions["CALL"][0] #call
            action = Action("BET", 100)
            if (isValid(action, self.legalActions)):
                return str(action) + "\n"
            else:
                return "CHECK\n"
        else:
            print "SOMETHING WRONG!"
            return "CHECK\n"
        '''

    def createQState(self):
        seat = int(self.seat)
        street = len(self.boardCards)
        if (seat == 1 and street > 0): #Dealer and flop, turn, river
            position = 1
        elif (seat == 3 and street == 0): #BB and pre-flop
            position = 1
        else:
            position = 0
        numPlayers = 3 if (bool(self.opp1Active) and bool(self.opp2Active)) else 2
        equity = discretizeEq(self.equity, numPlayers, street)

        numCheckCall1 = sum([1 for elt in self.lastActions if (("CHECK" == elt.name or "CALL" == elt.name) and self.opp1 == elt.actor)])
        didFold1 = sum([1 for elt in self.lastActions if ("FOLD" == elt.name and self.opp1 == elt.actor)])
        totalAmt1 = sum([int(elt.fields[0]) for elt in self.lastActions if (("CALL" == elt.name or "BET" == elt.name or "RAISE" == elt.name) and self.opp1 == elt.actor)])
        numBetRaise1 = sum([1 for elt in self.lastActions if (("BET" == elt.name or "RAISE" == elt.name) and self.opp1 == elt.actor)])

        numCheckCall2 = sum([1 for elt in self.lastActions if (("CHECK" == elt.name or "CALL" == elt.name) and self.opp2 == elt.actor)])
        totalAmt2 = sum([int(elt.fields[0]) for elt in self.lastActions if (("CALL" == elt.name or "BET" == elt.name or "RAISE" == elt.name) and self.opp2 == elt.actor)])
        didFold2 = sum([1 for elt in self.lastActions if ("FOLD" == elt.name and self.opp2 == elt.actor)])
        numBetRaise2 = sum([1 for elt in self.lastActions if (("BET" == elt.name or "RAISE" == elt.name) and self.opp2 == elt.actor)])

        dAmt1 = discretizeAmt(totalAmt1)
        dAmt2 = discretizeAmt(totalAmt2)
        numCheckCall1 = min(3, numCheckCall1)
        numCheckCall2 = min(3, numCheckCall2)
        numBetRaise1 = min(3, numBetRaise1)
        numBetRaise2 = min(3, numBetRaise2)
        prevAct = PrevAction(numCheckCall1, dAmt1, numBetRaise1, didFold1, numCheckCall2, dAmt2, numBetRaise2, didFold2, self.startingStreetPotSize)
        return QState(position, equity, street, prevAct)

    def createValidAction(self, action):
        #QLearn's possible actions ["FOLD", "CHECK", "CALL", "ODDS1.0", "ODDS1.5", "ODDS2.0", "ODDS3.0", "ODDS4.0"]
        #Format of legal actions to engine:
        #
        #self.lastActions is a list of PerformedActions

        if action == "FOLD":
            if "CHECK" in self.legalActions:
                return "CHECK"
            return action
        if action == "CHECK":
            if action in self.legalActions:
                return "CHECK"
            else:
                return "FOLD"
        if action == "CALL":
            if action in self.legalActions:
                return "CALL:" + self.legalActions["CALL"][0]
            else:
                return "CHECK"

        goal_odds = float(re.sub("[^0-9]", "",action))/10

        bet_metric = self.analyzePotOdds()

        bet_amt = int(self.potSize/goal_odds + bet_metric)


        #TODO, convert odds to bet amt.
        '''
        bet_amt = int(re.sub("[^0-9]", "",action))
        '''
        #dists keeps track of how close each valid action is to the amt qlearn decides to bet
        #The first value is distance from a fold/check
        dict_dists = {}
        dict_dists[bet_amt] = ["CHECK"]
        min_dist = bet_amt

        if "BET" in self.legalActions:
            minbet = int(self.legalActions["BET"][0]) #minBet
            maxbet = int(self.legalActions["BET"][1]) #maxBet
            if minbet < bet_amt and bet_amt < maxbet:
                return "BET:" + str(bet_amt)
            else:
                min_bet_diff = abs(minbet-bet_amt)
                max_bet_diff = abs(maxbet-bet_amt)
                min_dist = min(min_dist, min_bet_diff, max_bet_diff)
                if min_bet_diff in dict_dists:
                    dict_dists[min_bet_diff].append("BET:" + str(minbet))
                else:
                    dict_dists[min_bet_diff] = ["BET:" + str(minbet)]
                if max_bet_diff in dict_dists:
                    dict_dists[max_bet_diff].append("BET:" + str(maxbet))
                else:
                    dict_dists[max_bet_diff] = ["BET:" + str(maxbet)]

        if "RAISE" in self.legalActions:
            minraise = int(self.legalActions["RAISE"][0]) #minRaise
            maxraise = int(self.legalActions["RAISE"][1]) #maxRaise
            if minraise < bet_amt and bet_amt < maxraise:
                return "RAISE:" + str(bet_amt)
            else:
                min_raise_diff = abs(minraise-bet_amt)
                max_raise_diff = abs(maxraise-bet_amt)
                min_dist = min(min_dist, min_raise_diff, max_raise_diff)
                if min_raise_diff in dict_dists:
                    dict_dists[min_raise_diff].append("RAISE:" + str(minraise))
                else:
                    dict_dists[min_raise_diff] = ["RAISE:" + str(minraise)]
                if max_raise_diff in dict_dists:
                    dict_dists[max_raise_diff].append("RAISE:" + str(maxraise))
                else:
                    dict_dists[max_raise_diff] = ["RAISE:" + str(maxraise)]

        '''
        if "CALL" in self.legalActions:
            call = int(self.legalActions["CALL"][0])
            if abs(call - bet_amt) < 1:
                return "CALL:" + str(call)
            else:
                call_diff = abs(call - bet_amt)
                min_dist = min(min_dist, call_diff)
                if call_diff in dict_dists:
                    dict_dists[call_diff].append("CALL:" + str(call))
                else:
                    dict_dists[call_diff] = ["CALL:" + str(call)]
        '''



        if len(dict_dists[min_dist]) == 1:
            validAction = dict_dists[min_dist][0]
        else:
            validAction = random.choice(dict_dists[min_dist])


        print "goal odds: %.2f, pot size: %i, bet metric: %i,  bet amt is: %i, valid action is: %s" %(goal_odds, self.potSize, bet_metric, bet_amt, validAction)
        if validAction == "CHECK" and "CHECK" not in self.legalActions:
            return "FOLD"
        else:
            return validAction

    def analyzePotOdds(self):

        opp1_last_bet = 0
        opp2_last_bet = 0
        opp3_last_bet = 0
        for PerformedAction in self.lastActions:
            if PerformedAction.actor == self.opp1 and PerformedAction.name in ["BET", "RAISE"]:
                opp1_last_bet = int(PerformedAction.fields[0])
            if PerformedAction.actor == self.opp2 and PerformedAction.name in ["BET", "RAISE"]:
                opp2_last_bet = int(PerformedAction.fields[0])
            if PerformedAction.actor == self.name and PerformedAction.name in ["BET", "RAISE"]:
                opp3_last_bet = int(PerformedAction.fields[0])
        last_bets = [opp1_last_bet, opp2_last_bet, opp3_last_bet]
        print "last bets are ", last_bets
        last_player_seat = (self.seat - 1) % 3
        next_player_seat = (self.seat + 1) % 3
        player_seat = self.seat

        if last_player_seat == 0:
            last_player_seat = 3
        if next_player_seat == 0:
            next_player_seat = 3
        if next_player_seat == 0:
            player_seat = 3

        last_player_bet = last_bets[last_player_seat - 1]
        next_player_bet = last_bets[next_player_seat - 1]
        player_bet = last_bets[player_seat - 1]

        final_bet_metric = 0

        if self.activePlayers[last_player_seat - 1]:
            final_bet_metric = last_player_bet
        else:
            final_bet_metric = next_player_bet

        return final_bet_metric - player_bet

    def resetTurn(self):
        self.legalActions = {}

    def getstats(self):
        #Any stats we would need here about opponents. Use lastActions and others
        #Example to store stats about an opponent
        self.stats[self.opp1] = self.opp1Stack

    def resetHand(self):
        self.lastActions = []
        self.seat = 0
        self.card1 = None
        self.card2 = None
        self.equity = 0.0
        self.opp1Equity = 0.0
        self.opp2Equity = 0.0
        self.boardCards = []


if __name__ == '__main__':

    #1st arg, 2nd arg, 3rd arg
    #Hands, board cards, dead cards
    #Hands: colon is a delimiter, x is wild card
    #Output is a list of tuples: [('AhAs', 0.7329499999999994), ('xx', 0.1386499999999999), ('xx', 0.12839999999999996)]
    #r = pbots_calc.calc("AhAs:xx", "", "", 1000000)
    #print r
    #sys.exit(0)

    parser = argparse.ArgumentParser(description='A Pokerbot.', add_help=False, prog='pokerbot')
    parser.add_argument('-h', dest='host', type=str, default='localhost', help='Host to connect to, defaults to localhost')
    parser.add_argument('port', metavar='PORT', type=int, help='Port on host to connect to')
    args = parser.parse_args()

    # Create a socket connection to the engine.
    print 'Connecting to %s:%d' % (args.host, args.port)
    try:
        s = socket.create_connection((args.host, args.port))
    except socket.error as e:
        print 'Error connecting! Aborting'
        exit()

    bot = Player()
    bot.run(s)
