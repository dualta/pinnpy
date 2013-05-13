import pinnObjList

# ------------------------------------------- #
	
class pinnObjDict(dict):
	def __init__(self, dict1, filename=''):
		"""
		Initialize private variables
		"""
		self = dict1
		self._filename = filename

	# ------------------------------------------- #
	
	"""
	Subclass of dictionary object to offer some syntatic sugar.
	"""	
	def __getattr__(self, key):
		"""
		Allow user to access dictionary entries by the dot operator
		"""
		try:
			if type(self[key]) is dict:
				return pinnObjDict(self[key],self._filename)
			elif type(self[key]) is list:
				return pinnObjList.pinnObjList(self[key],self._filename)
			else:
				return self[key]
		except:
			raise 
	
	# ------------------------------------------- #
	
	def __setattr__(self,key,item):
		"""
		Allow user to set dictionary entries by the dot operator
		"""
		self[key] = item

	# ------------------------------------------- #
	
	def dir(self):
		"""
		Return a list of dictionary entries
		"""
		print self.keys()

	# ------------------------------------------- #
	
	def __dir__(self):
		"""
		Allow tab completion to work as expected
		"""		
		return self.keys()

	# ------------------------------------------- #

	def search(self, searchStr, inPath=''):
		"""
		Recursively search through dictionary levels for keys matching searchStr
		and print full heirarchy listing for matching entries.
		To match key should have non-case specific match to searchStr somewhere in key.
		"""
		for key in self:
			thisPath = inPath + '.' + key
			
			if searchStr.lower() in key.lower():
				print(thisPath)
		
			if type(self[key]) is dict:
				pinnObjDict(self[key],self._filename).search(searchStr, thisPath)
				
			elif type(self[key]) is list and len(self[key]) > 0 and type(self[key][0]) is dict:
				pinnObjDict(self[key][0],self._filename).search(searchStr, thisPath + ' .Current')
			
# ------------------------------------------- #

