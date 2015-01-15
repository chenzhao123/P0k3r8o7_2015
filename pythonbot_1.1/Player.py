import argparse
import socket
import sys
import pbots_calc
import Parser
from BotUtils import *
import re
import random
from Qlearn import *
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
        self.ai = QLearn(["FOLD", "CHECK", "BET10", "BET20", "BET30", "BET40", 
                          "BET50", "BET60", "BET70", "BET80", "BET90"],
                          epsilon=0.1, alpha=0.2, gamma=1.0)
 
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
                self.requestkeyvalues(packet_parser.parser_dict)
                for key in self.newkeyvalues:
                    s.send("PUT " + str(key) + " " + str(self.newkeyvalues[key]) + "\n")
                s.send("FINISH\n")
            #print "end while", time.asctime()
        # Clean up the socket.
        s.close()

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

        deltaStack = self.stack - self.startingStack
        self.ai.learnAll(deltaStack)

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
  
        state = self.createState(self.seat, boardCards, self.equity, self.lastActions)
        #print "choose action starts", time.asctime()
        action = self.ai.chooseAction(state)
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

    def createState(self, seat, boardCards, equity, lastActions):
        #State is a tuple of (position, street, equity, #total checks, #total folds, 
        #                     total amount bet, total amount called, total amount raised) <-discretized by 10s up to 100
        position = seat
        street = len(boardCards)/2
        discretized_equity = int((100*equity)/20)
        num_checks = sum([1 for elt in lastActions if "CHECK" == elt.name])
        num_folds = sum([1 for elt in lastActions if "FOLD" == elt.name])
        total_call = sum([int(elt.fields[0]) for elt in lastActions if "CALL" == elt.name])
        total_bet = sum([int(elt.fields[0]) for elt in lastActions if "BET" == elt.name])
        total_raise = sum([int(elt.fields[0]) for elt in lastActions if "RAISE" == elt.name])
        #total_call = sum([float(re.sub("[^0-9]", "",elt)) for elt in lastActions if "call" in elt.name.lower()])
        #Maybe consider combining bet and raise
        #total_bet = sum([float(re.sub("[^0-9]", "",elt)) for elt in lastActions if "bet" in elt.lower()])
        #total_raise = sum([float(re.sub("[^0-9]", "",elt)) for elt in lastActions if "raise" in elt.lower()])
        discretized_call = int(total_call/10)
        discretized_aggression = int((total_bet + total_raise)/10)

        return (position, street, equity, num_checks, num_folds, discretized_call, discretized_aggression)

    def createValidAction(self, action):
        #QLearn's possible actions ["FOLD", "CHECK", BET10", "BET20", "BET30", "BET40", 
        #                           "BET50", "BET60", "BET70", "BET80", "BET90"]
        #Format of legal actions to engine:
        #
        if action in ['FOLD', 'CHECK']:
            return action

        bet_amt = int(re.sub("[^0-9]", "",action))
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

        if len(dict_dists[min_dist]) == 1:
            validAction = dict_dists[min_dist][0]
        else:
            validAction = random.choice(dict_dists[min_dist])

        if validAction == "CHECK" and "CHECK" not in self.legalActions:
            return "FOLD"
        else:
            return validAction

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
