class Parser(object):

	def __init__(self):
		self.parser_dict = {}

	def parse(self, string):
		
		self.parser_dict = {}
		packet_type, space, info = string.partition(' ')

		if packet_type == "NEWGAME":
			self.parse_new_game(info)
		elif packet_type == "KEYVALUE":
			self.parse_key_value(info)
		elif packet_type == "REQUESTKEYVALUES":
			self.parse_request_key_value(info)
		elif packet_type == "NEWHAND":
			self.parse_new_hand(info)
		elif packet_type == "GETACTION":
			self.parse_get_action(info)
		elif packet_type == "HANDOVER":
			self.parse_hand_over(info)
		else:
			raise ValueError

		return self.parser_dict

	def parse_new_game(self, string):

		#NEWGAME yourName opp1Name opp2Name stackSize bb numHands timeBank
		yourName, opp1Name, opp2Name, stackSize, bb, numHands, timeBank = string.split(' ')

		self.parser_dict['yourName'] = yourName
		self.parser_dict['opp1Name'] = opp1Name
		self.parser_dict['opp2Name'] = opp2Name
		self.parser_dict['stackSize'] = float(stackSize)
		self.parser_dict['bb'] = float(bb)
		self.parser_dict['numHands'] = int(numHands)
		self.parser_dict['timeBank'] = float(timeBank)

	def parse_new_hand(self, string):

		#handId seat holeCard1 holeCard2 [stackSizes] [playerNames] numActivePlayers [activePlayers] timeBank
		handId, seat, holeCard1, holeCard2, stackSize1, stackSize2, stackSize3, \
		playerName1, playerName2, playerName3, numActivePlayers, \
		activePlayer1, activePlayer2, activePlayer3, timeBank = string.split(' ')
		stackSizes = [float(stackSize1), float(stackSize2), float(stackSize3)]
		playerNames = [playerName1, playerName2, playerName3]
		activePlayers = [self.str2bool(activePlayer1), self.str2bool(activePlayer2), self.str2bool(activePlayer3)]

		self.parser_dict['handId'] = int(handId)
		self.parser_dict['seat'] = int(seat)
		self.parser_dict['holeCard1'] = holeCard1
		self.parser_dict['holeCard2'] = holeCard2
		self.parser_dict['stackSizes'] = stackSizes
		self.parser_dict['playerNames'] = playerNames
		self.parser_dict['numActivePlayers'] = int(numActivePlayers)
		self.parser_dict['activePlayers'] = activePlayers
		self.parser_dict['timeBank'] = float(timeBank)


	def parse_key_value(self, string):

		#KEYVALUE key value
		key, space, value = string.partition(' ')

		self.parser_dict['key'] = key
		self.parser_dict['value'] = value

	def parse_request_key_value(self, string):
		
		#REQUESTKEYVALUES bytesLeft
		bytesLeft = string

		self.parser_dict['bytesLeft'] = bytesLeft

	def parse_get_action(self, string):

		#GETACTION potSize numBoardCards [boardCards] [stackSizes] numActivePlayers 
		#[activePlayers] numLastActions [lastActions] numLegalActions [legalActions] timebank
		string = string.split(' ')
		potSize = string.pop(0)
		
		numBoardCards = int(string.pop(0))
		boardCards = string[:numBoardCards]
		string = string[numBoardCards:]		
		stackSizes = string[:numBoardCards]
		string = string[numBoardCards:]
		
		numActivePlayers = int(string.pop(0))	
		activePlayers = string[:numActivePlayers]
		string = string[numActivePlayers:]

		numLastActions = int(string.pop(0))
		lastActions = string[:numLastActions]
		string = string[numLastActions:]

		numLegalActions = int(string.pop(0))
		legalActions = string[:numLegalActions]
		string = string[numLegalActions:]

		timeBank = string.pop(0)

		self.parser_dict['potSize'] = float(potSize)
		self.parser_dict['numBoardCards'] = numBoardCards
		self.parser_dict['boardCards'] = boardCards
		self.parser_dict['stackSizes'] = [float(i) for i in stackSizes]
		self.parser_dict['numActivePlayers'] = numActivePlayers
		self.parser_dict['activePlayers'] = [str2bool(i) for i in activePlayers]
		self.parser_dict['numLastActions'] = numLastActions
		self.parser_dict['lastActions'] = lastActions
		self.parser_dict['numLegalActions'] = numLegalActions
		self.parser_dict['legalActions'] = legalActions
		self.parser_dict['timebank'] = float(timebank)

	def parse_hand_over(self, string):

		#HANDOVER [stackSizes] numBoardCards [boardCards] numLastActions [lastActions] timeBank
		string = string.split(' ')
		stackSizes = string[:3]
		string = string[3:]

		numBoardCards = int(string.pop(0))
		boardCards = string[:numBoardCards]
		string = string[numBoardCards:]

		numLastActions = int(string.pop(0))
		lastActions = string[:numLastActions]
		string = string[numLastActions:]

		timeBank = string.pop(0)

		self.parser_dict['stackSizes'] = [float(i) for i in stackSizes]
		self.parser_dict['numBoardCards'] = numBoardCards
		self.parser_dict['boardCards'] = boardCards
		self.parser_dict['numLastActions'] = numLastActions
		self.parser_dict['lastActions'] = lastActions
		self.parser_dict['timeBank'] = float(timeBank)

	def str2bool(v):
  		return v.lower() in ("yes", "true", "t", "1")
