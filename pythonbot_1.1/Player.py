import argparse
import socket
import sys
import pbots_calc
import Parser
from BotUtils import *

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
        self.bytesleft = 0
        self.stats = {}
        self.newkeyvalues = {}
        self.equity = 0.0 
        self.opp1Equity = 0.0
        self.opp2Equity = 0.0
        self.ai = Qlearn(["FOLD", "CHECK", "CALL", "BET10", "BET20", "BET30", 
                          "BET40", "BET50", "BET60", "BET70", "BET80", "BET90"],
                          epsilon=0.1, alpha=0.2, gamma=1.0)
 
    def run(self, input_socket):
        # Get a file-object for reading packets from the socket.
        # Using this ensures that you get exactly one packet per read.
        f_in = input_socket.makefile()
        packet_parser = Parser.Parser()

        while True:
            # Block until the engine sends us a packet.
            data = f_in.readline().strip()
            # If data is None, connection has closed.
            if not data:
                print "Gameover, engine disconnected."
                break

            # Here is where you should implement code to parse the packets from
            # the engine and act on it. We are just printing it instead.
            print data
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
                s.send(resp)
            elif packet_type == "HANDOVER":
                self.handover(packet_parser.parser_dict)    
            elif word == "REQUESTKEYVALUES":
                # At the end, the engine will allow your bot save key/value pairs.
                # Send FINISH to indicate you're done.
                #s.send("FINISH\n")
                self.requestkeyvalues(packet_parser.parser_dict)
                for key in self.newkeyvalues:
                    s.send("PUT " + key + " " + self.newkeyvalues[key] + "\n")
                s.send("FINISH\n")
        # Clean up the socket.
        s.close()

    def newgame(self, parser_dict):
        self.name = parser_dict['yourName']
        self.opp1 = parser_dict['opp1Name']
        self.opp2 = parser_dict['opp2Name']
        self.stack = parser_dict['stackSize']
        self.opp1Stack = self.stack
        self.opp2Stack = self.stack
        self.bb = parser_dict['bb']
        self.numHands = parser_dict['numHands']
        self.timeBank = parser_dict['timeBank']

    def keyvalue(self, parser_dict):
        for key in parser_dict:
          self.keyvalues[key] = parser_dict[key]    

    def newhand(self, parser_dict):
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
        
    def getaction(self, parser_dict):
        self.potSize = parser_dict['potSize']
        numBoardCards = parser_dict['numBoardCards']
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
        
        self.lastActions.extend([PerformedAction(action) for action in parser_dict['lastActions']])
        for action in parser_dict['legalActions']:
            legalAction = LegalAction(action)
            self.legalActions[legalAction.name] = legalAction.fields
        self.timeBank = parser_dict['timeBank']
        self.resetTurn()
        return self.getResponse()       

    def handover(self, parser_dict):
        self.stack = parser_dict['stackSizes'][self.index]
        self.opp1Stack = parser_dict['stackSizes'][self.opp1Index]
        self.opp2Stack = parser_dict['stackSizes'][self.opp2Index]
        self.lastActions.extend([PerformedAction(action) for action in parser_dict['lastActions']])
        self.timeBank = parser_dict['timeBank']
        self.getstats()
        self.resetHand()

    def requestkeyvalues(self, parser_dict):
        self.bytesleft = int(parser_dict['bytesleft'])
        #Example to store new key values
        self.newkeyvalues[self.opp1] = self.stats[self.opp1]

    def getResponse(self):
        myCards = str(self.card1) + str(self.card2)
        boardCards = "".join(str(card) for card in self.boardCards)
        deadCards = ""
        opp1Cards = "xx"
        opp2Cards = "xx"
        holeCardsInput = myCards + ":" + opp1Cards + ":" + opp2Cards
        eqResults = pbots_calc.calc(holeCardsInput, boardCards, deadCards, 10000)
        #Example of how to make actions and check if they are valid
        print "equities:", eqResults, type(eqResults)
        if eqResults == None:
            print "pbots_calc input:", holeCardsInput
            print self.card1
            print self.card2
            print "b", boardCards
            print "d", deadCards
        self.equity = eqResults.ev[0]
        self.opp1Equity = eqResults.ev[1]
        self.opp2Equity = eqResults.ev[2]

        state = self.createState(self.seat, boardCards, self.equity, self.lastActions)
        
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
        equity = equity
        num_checks = sum([1 for elt in lastActions if "check" in elt.lower()])
        num_folds = sum([1 for elt in lastActions if "fold" in elt.lower()])
        total_call = sum([float(re.sub("[^0-9]", "",elt)) for elt in list if "call" in elt.lower()])
        #Maybe consider combining bet and raise
        total_bet = sum([float(re.sub("[^0-9]", "",elt)) for elt in list if "bet" in elt.lower()])
        total_raise = sum([float(re.sub("[^0-9]", "",elt)) for elt in list if "raise" in elt.lower()])
        discretized_call = total_call/10
        discretized_aggression = (total_bet + total_raise)/10

        return (position, street, equity, num_checks, num_folds, discretized_call, discretized_aggression)

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
