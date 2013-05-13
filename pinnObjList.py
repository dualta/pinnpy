import pinnObjDict

# ------------------------------------------- #
	
class pinnObjList():
	"""
	Subclass of list object to offer some syntatic sugar.
	"""
	def __init__(self, inList, filename=''):
		self.__list = inList[:]
		self.__curNum = 0
		self.__listLen = len(self.__list)
		self._filename = filename

	# ------------------------------------------- #
	
	def __getitem__(self, index):
		if type(self.__list[index]) is dict:		
			return pinnObjDict.pinnObjDict(self.__list[index],self._filename)
		else:
			return self.__list[index]
	
	# ------------------------------------------- #
	
	def __setitem__(self, index, value):
		self.__list[index] = value
	
	# ------------------------------------------- #
	
	def __getattr__(self, key):
		if key is 'First':
			return self.getFirst()
		elif key is 'Last':
			return self.getLast()
		elif key is 'Current':
			return self.getCurrent()
		elif key is 'Count':
			return self.Count()
		elif key is 'AsList':
			return self.asList()
		elif key[0] is '#' and key[1:].isdigit():
			return self.__getitem__(index)
		else:
			print("Method not recognized")
		
	# ------------------------------------------- #
	
	def __iter__(self):
		"""
		Allow looping over the list
		"""		
		self.__curNum = 0
		return self

	# ------------------------------------------- #

	def next(self):
		"""
		Allow looping over the list and stop at the end
		"""
		if self.__curNum >= self.__listLen:
			raise StopIteration
		else:
			if type(self.__list[self.__curNum]) is dict:		
				rtnVal = pinnObjDict.pinnObjDict(self.__list[self.__curNum],self._filename)
			else:
				rtnVal = self.__list[self.__curNum]
			
			self.__curNum += 1
			return rtnVal
			
	# ------------------------------------------- #

	def asList(self):
		"""
		Access the elements as a normal python list
		"""
		return self.__list

	# ------------------------------------------- #
	
	def Count(self):
		"""
		Return the number of elements in the list
		"""
		return self.__listLen

	# ------------------------------------------- #
	
	def getFirst(self):
		"""
		Allow access of zeroth element by use of function First
		"""
		if type(self.__list[0]) is dict:		
			return pinnObjDict.pinnObjDict(self.__list[0],self._filename)
		else:
			return self.__list[0]
		
	# ------------------------------------------- #
	
	def getCurrent(self, num=-1):
		"""
		Allow access of current element by use of function First
		"""	
		if num != -1:
			self.__curNum = num
		else:
			if type(self.__list[self.__curNum]) is dict:		
				return pinnObjDict.pinnObjDict(self.__list[self.__curNum],self._filename)
			else:
				return self.__list[self.__curNum]
		
	# ------------------------------------------- #
	
	def getLast(self):
		if type(self.__list[-1]) is dict:		
			return pinnObjDict.pinnObjDict(self.__list[0],self._filename)
		else:
			return self.__list[-1]
		
	# ------------------------------------------- #
	
	def dir(self):
		"""
		Return a list of entries
		"""
		print(['Count','Current','First','Last'])

	# ------------------------------------------- #
	
	def __dir__(self):
		"""
		Allow tab completion to work as expected
		"""
		return ['Count','Current','First','Last']

	# ------------------------------------------- #
	
	def __len__(self):
		"""
		Report the length of the list
		"""
		return self.__listLen
