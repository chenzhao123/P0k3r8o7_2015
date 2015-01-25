import argparse
import socket
import sys
import pbots_calc
import Parser
from BotUtils import *
import re
import random
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
        self.numHandsPlayed = 0
        self.numChipsGained = 0

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
                print "sending:", resp
                s.send(resp+"\n")
                #print 'sent response', resp, time.asctime()
            elif packet_type == "HANDOVER":
                self.handover(packet_parser.parser_dict)
            elif packet_type == "REQUESTKEYVALUES":
                # At the end, the engine will allow your bot save key/value pairs.
                # Send FINISH to indicate you're done.
                #s.send("FINISH\n")
                #print "dumping q values to", self.qfile
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

        if (self.flop or self.turn or self.river):
            self.boardCards = [Card(card) for card in parser_dict['boardCards']]

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

        self.numHandsPlayed += 1
        self.numChipsGained += deltaStack
        if not self.numHandsPlayed % 1000:
            print "Average winning per hand:", self.numChipsGained / 1000.0
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
        numPlayers = 1 + int(self.opp1Active) + int(self.opp2Active)
        if numPlayers == 3:
            holeCardsInput = myCards + ":" + opp1Cards + ":" + opp2Cards
        if numPlayers == 2:
            holeCardsInput = myCards + ":" + opp1Cards
        eqResults = pbots_calc.calc(holeCardsInput, boardCards, deadCards, 10000)
        self.equity = eqResults.ev[0]
        self.opp1Equity = eqResults.ev[1]
        if numPlayers == 3:
            self.opp2Equity = eqResults.ev[2]

        street = len(self.boardCards)
        print self.boardCards
        print "street", street
        print numPlayers
        if numPlayers == 2:
            if street == 0:
                low = 0.40; high = 0.60
            elif street == 3:
                low = 0.50; high = 0.65
            elif street == 4:
                low = 0.55; high = 0.70
            elif street == 5:
                low = 0.60; high = 0.75
        elif numPlayers == 3:
            if street == 0:
                low = 0.35; high = 0.45
            elif street == 3:
                low = 0.40; high = 0.50
            elif street == 4:
                low = 0.45; high = 0.55
            elif street == 5:
                low = 0.50; high = 0.60

        tol = self.equity * float(self.potSize)
        print "potsize", self.potSize
        print "equity:", self.equity
        print "tol:", tol

        if (self.equity < low):
            if ("CALL" in self.legalActions):
                callAmt = int(self.legalActions["CALL"][0])
                if (callAmt < tol):
                    return "CALL:" + str(callAmt)
            return "CHECK"
        elif (self.equity >= low and self.equity < high):
            x = self.equity
            x2 = x*x
            x3 = x2*x
            if self.flop:
                bet = 100*x2 - 10*x - 15
            elif self.turn:
                bet = 150*x2 + 50*x - 50
            elif self.river:
                bet = 250*x2 + 80*x - 80
            else:
                bet = 50*x2 - 10*x - 5
            bet = int(bet)
            print "bet:", bet
            if ("BET" in self.legalActions):
                maxbet = int(self.legalActions["BET"][1]) #maxBet
                minbet = int(self.legalActions["BET"][0]) #minBet
                if (minbet <= bet and bet <= maxbet):
                    return "BET:" + str(bet)
                elif (bet > maxbet):
                    return "BET:" + str(maxbet)
                else:
                    return "BET:" + str(minbet)
            if("RAISE" in self.legalActions):
                maxraise = int(self.legalActions["RAISE"][1])
                minraise = int(self.legalActions["RAISE"][0])
                if (minraise <= bet and bet <= maxraise):
                    return "RAISE:" + str(bet)
                elif (bet > maxraise):
                    return "RAISE:" + str(maxraise)
            if ("CALL" in self.legalActions):
                callAmt = int(self.legalActions["CALL"][0])
                if (callAmt < tol):
                    return "CALL:" + str(callAmt)
            return "CHECK"
        else:
            if ("RAISE" in self.legalActions):
                maxraise = int(self.legalActions["RAISE"][1])
                return "RAISE:" + str(maxraise)
            elif ("BET" in self.legalActions):
                maxbet = int(self.legalActions["BET"][1])
                return "BET:" + str(maxbet)
            return "CHECK"


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
