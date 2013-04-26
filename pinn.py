#!/usr/bin/env python
# coding=utf-8

import re, sys, json
import numpy as np
from optparse import OptionParser

import pinnObjList
import pinnObjDict

# ----------------------------------------- #
"""
Use JSON structured text file readers to parse pinnacle file into a muliple layered dictionary.

A pinnacle file is similar in structure to a json file although not identical. Script parses the 
pinnacle file and resolves the syntax differences to make a valid json specification conforming 
string which contains all the data present in the original file.

Issue with new line inside comments field in Patient file.
Issue with plan.defaults file Line : 
	image_file      : ../ImageSet_1
"""

# ----------------------------------------- #
	
def read(pinnFile):
	"""
	Read the pinnacle file and return as a dictionary or array of dictionaries.
	"""
	f = open(pinnFile)
	fileTxt = pinn2Json(f.read())
	f.close()
	
	f = open(pinnFile + '.json','w')
	f.write(fileTxt)
	f.close()
	
	return pinnObjDict.pinnObjDict(json.loads(fileTxt))

# ----------------------------------------- #
	
def reads(fileTxt):
	"""
	Translate the pinnacle file text to a python dictionary object.
	"""
	fileTxt = pinn2Json(fileTxt)
	
	return pinnObjDict.pinnObjDict(json.loads(fileTxt))

# ----------------------------------------- #

def readJson(pinnFile):
	"""
	Read the pinnacle data from a file in JSON format
	"""
	f = open(pinnFile)
	fileTxt = f.read()
	f.close()
	
	return pinnObjDict.pinnObjDict(json.loads(fileTxt))

# ----------------------------------------- #

def writeJson(pinnFile, jsonFile):
	"""
	Write the pinnacle file to a new file in JSON format
	"""
	f = open(pinnFile)
	fileTxt = pinn2Json(f.read())
	f.close()
	
	f2 = open(jsonFile,'w')
	f2.write(fileTxt)
	f2.close()

# ----------------------------------------- #

def pinn2Json(pinnFileText):
	"""
	Convert pinnacle format text to JSON format text
	"""
	
	sectionStart, sectionEnd, sectionDepth = findSectionBrakes(pinnFileText)
	
	pinnFileText = dotHeirarchyToPinnFormat(pinnFileText)
	
	#print(pinnFileText[:150])

	# For opening objects add an opening list to contain them:
	#	E.g. files start with Trial{ ... } followed by another Trial{ ... }
	#		 should start with TrialList{ Trial{...} Trial{...} } 
	sectionStart, sectionEnd, sectionDepth = findSectionBrakes(pinnFileText)
	
	# Files that contain primary sections need an incasing list for consistancy with the rest of the file.
	# E.g. this:				becomes:
	#		 	roi ={				roiList ={
	#				...					roi ={
	# 			}; 							...
	# 			roi ={					};
	# 				...					roi ={
	# 			}; 							...
	#									};
	#								};
	numPrimaries = 0
	sectionName = []
	primaryStart = []
	primaryEnd = []
	for sDepth, sStart, sEnd in zip(sectionDepth, sectionStart, sectionEnd):
		if sDepth == 0: 
			numPrimaries += 1
			#sName = re.search('(?<=\n).*(?=\=$)', pinnFileText[:sStart]).group()
			sName = re.search('^.*(?=\=$)', pinnFileText[:sStart], re.MULTILINE).group()
			sectionName.append(sName)
			primaryStart.append(sStart)
			primaryEnd.append(sEnd)
	
	if numPrimaries > 0:
		# Find first repeated primary section		
		for sName in set(sectionName):
			if sectionName.count(sName) > 1:
				pStart = primaryStart[sectionName.index(sName)]
				pEnd = primaryEnd[len(sectionName)-sectionName[::-1].index(sName)-1]
				pinnFileText = pinnFileText[:pStart-len(sName)-1] + sName.strip() + \
								"List ={\n" + sName + "=" + pinnFileText[pStart:pEnd] + "\n};\n" + \
								pinnFileText[pEnd:]
				break
		
		#match1 = re.search("\w*(?= {0,1}={)",pinnFileText)
		#objName = pinnFileText[match1.start():match1.end()]
		#pinnFileText = pinnFileText[:match1.start()] + objName + "List ={\n" + pinnFileText[match1.start():] + "\n};\n"
	
	#f1 = open('debug01','w')
	#f1.write(pinnFileText)
	#f1.close()
	
	sectionStart2, sectionEnd2, sectionDepth2 = findSectionBrakes(pinnFileText)
	
	# Remove single line comments
	pinnFileText = re.sub('^//.*?\n', '', pinnFileText, re.MULTILINE )
	pinnFileText = re.sub('//.*?\n', '\n', pinnFileText )

	# Remove block comments
	pinnFileText = re.sub(r'\/\*[^*]*\*+([^/][^*]*\*+)*\/', '', pinnFileText, re.DOTALL )
	
	# Protect = sign when inside string quotation by changing to @$, will be changed back later
	pinnFileText = re.sub(r'("[\w \t;,\-\+\.]*)(=)([\w \t;,\-\+\.]*")',r'\1@$\3', pinnFileText)

	#f1 = open('debug02','w')
	#f1.write(pinnFileText)
	#f1.close()
	
	# In some pinnacle files : is used for string equality instead of = "" change for consistency
	pinnFileText = re.sub(r'\n([ \t\w\^\._-]*) *: *([ \t\w\^\.:/_-]*)', r'\n\1 = "\2";', pinnFileText)
	
	# At end of line change ; to , and at start of line add a " to start of key
	pinnFileText = re.sub(';\n*\s*(?=[\w#])', ',\n"', pinnFileText )

	#f1 = open('debug03','w')
	#f1.write(pinnFileText)
	#f1.close()
	
	# For lines ending in { make sure following line has a "
	pinnFileText = re.sub('{\n\s*(?=[A-Za-z#])', '{\n"', pinnFileText )

	#f1 = open('debug04','w')
	#f1.write(pinnFileText)
	#f1.close()
	
	# If there is a key on the first line then it also needs a "
	pinnFileText = re.sub('\A\s*(?=[A-Za-z#])','"',pinnFileText)

	#f1 = open('debug05','w')
	#f1.write(pinnFileText)
	#f1.close()
	
	# And last line needs the semicolon removed
	pinnFileText = re.sub(';\s*\Z','',pinnFileText)

	# Remove semicolon for lines followed by a closing paren
	pinnFileText = re.sub(';\n*\s*}','\n}',pinnFileText)

	# Add " to end of key and change key, value separator from = to :
	pinnFileText = re.sub('\s*=\s*', '" : ', pinnFileText )
	
	#f1 = open('debug06','w')
	#f1.write(pinnFileText)
	#f1.close()
	
	# Return the = inside quotation marks
	pinnFileText = re.sub('@$', '=', pinnFileText )
	
	# Add an enclosing parenthesis for the file
	pinnFileText = "{\n" + pinnFileText + "\n}\n"

	#f1 = open('debug07','w')
	#f1.write(pinnFileText)
	#f1.close()
	
	# Convert plan.roi points into plan.Trial Points[]
	pinnFileText = re.sub(r'\n\s*"points" ?: ?{\n', r'\n"Points[]" :{\n', pinnFileText )

	# Convert N N N lines into [ N, N, N ], lines, where N is a number that might be negative and might have a decimal point.
	pinnFileText = re.sub(r'\n\s*(\-?[0-9]+\.?[0-9]*)\s(\-?[0-9]+\.?[0-9]*)\s(\-?[0-9]+\.?[0-9]*)\s*(?=\n)', r'\n[ \1, \2, \3 ],', pinnFileText)

	#f1 = open('debug08','w')
	#f1.write(pinnFileText)
	#f1.close()
	
	# Convert Points[] : { N,N } arrays to Points : [ N,N ] (match anything except '}')
	pinnFileText = re.sub( r'"Points\[\]" ?: ?{\n([^}]*)}', r'"Points" : [\n\1]', pinnFileText)

	#f1 = open('debug09','w')
	#f1.write(pinnFileText)
	#f1.close()	
		
	# Remove " from start of lines in a numeric array
	pinnFileText = re.sub(r'\[\n"([0-9]*\.?[0-9]*,[0-9]*.?[0-9]*,)\n', r'[\n\1\n', pinnFileText )

	#f1 = open('debug10','w')
	#f1.write(pinnFileText)
	#f1.close()	
		
	# Convert = \XDR:0\; to = "XDR:0";
	pinnFileText = re.sub(r': \\XDR:([0-9]*)\\', r': "XDR-\1"', pinnFileText)

	# For store objects change syntax slightly : e.g. Float { to : {
	pinnFileText = re.sub(' : Float {', ' : {', pinnFileText)
	pinnFileText = re.sub(' : SimpleString {', ' : {', pinnFileText)
	
	#f1 = open('debug11','w')
	#f1.write(pinnFileText)
	#f1.close()	
	
	# ----------------------------------------------------------------------------------- #
	# Convert ObjectLists from ObjectList = { Object={A}, Object={B} } to ObjectList = [ A, B ]

	# Find matching pairs of brackets	
	sectionStart, sectionEnd, sectionDepth = findSectionBrakes(pinnFileText)

	listStarts = []	
	for listP in re.finditer('List" : {',pinnFileText): 
		listStarts.append(listP.start())
	listStarts = np.array(listStarts)
	
	# Compile a list of pinnacle List arrays such as BeamList, etc.		
	for ll, listSt in enumerate(listStarts):
		#print("List %d at line %d, char %d" % (ll, lineNumber(pinnFileText,listSt), listSt))
		
		# Find the beginning and end of the list section		
		bracketNum = np.where(sectionStart > listSt)[0][0]
		listEnd = sectionEnd[bracketNum]
		
		# Get the name of the pinnacle list type (the part that comes before List)
		# E.g. BeamList becomes Beam, TrialList becomes Trial
		listMatch = re.search('(?<=\n")[\s\w]*?$',pinnFileText[:listSt])
		#print(repr(pinnFileText[listSt-30:listSt]))		
		listName = pinnFileText[listMatch.start():listSt]
		
		matchStr = '"' + listName + '" : {'
		
		# Cut out the list portion from the file text
		extract = pinnFileText[listSt:listEnd] 
		
		# If there are no items in the list then skip it and leave it as it is.		
		if len(re.findall(matchStr, extract))==0 and len(re.findall('"#[0-9]*" : {', extract))==0:
			continue
		
		nCharsRemoved = len(matchStr)-1
		for mm, matchM in enumerate(re.finditer(matchStr,extract)):
			matchPos = matchM.start() + listSt
			if mm == 0: firstMatch = matchPos
			
			listInds = np.where(listStarts > matchPos)[0]
			
			sectionStart[ np.where(sectionStart > matchPos)[0] ] -= nCharsRemoved
			sectionEnd[ np.where(sectionEnd > matchPos)[0] ] -= nCharsRemoved
			listStarts[ listInds ] -= nCharsRemoved
			
		extract = re.sub(matchStr,'{',extract)	
				
		# Set text to previous portion + extract + subsequent portion		
		pinnFileText = pinnFileText[:listSt] + 'List" : [' + extract[9:-1] + "]," + pinnFileText[listEnd+1:]
	
	#f1 = open('debug12','w')
	#f1.write(pinnFileText)
	#f1.close()	
		
	# ObjectLists that have elements named #0, #1 etc. must be changed
	pinnFileText = re.sub('"#[0-9]*" : {', '{', pinnFileText )
	
	#f1 = open('debug13','w')
	#f1.write(pinnFileText)
	#f1.close()	
	
	# Clean up a bit by removing any commas added where we shouldn't have commas
	# Match } or ] following by , some whitespace and then } or ]
	# Replace by the first bracket newline second bracket.	
	#pinnFileText = re.sub(r'([}\]]),\s*([[}\]])', r'\1\n\2', pinnFileText )
	pinnFileText = re.sub(r'([}\]]),\s*([}\]])', r'\1\n\2', pinnFileText )

	#f1 = open('debug14','w')
	#f1.write(pinnFileText)
	#f1.close()	
	
	return pinnFileText

# ----------------------------------------- #

def dotHeirarchyToPinnFormat(fileTxt):
	"""
	Convert dot object heirarchy to bracket heirarchy
		
	E.g. Convert this syntax:
		DoseGrid .VoxelSize .X = 0.4;
	  	DoseGrid .VoxelSize .Y = 0.4;
	  	DoseGrid .Dimension .X = 125;
	  	DoseGrid .Dimension .Y = 112;
	
	to this syntax, which is more consistent with the rest of pinnacle file format  
  	DoseGrid ={
  	  VoxelSize = {
		X = 0.4;
		Y = 0.4;
	  };
	Dimension = {
		X = 125;
		Y = 112;
	  };
	};

	Assume that sub-objects in dot heirarchy are on subsequent lines.
	"""
	prevEnd = 0
	prevSection = ""
	
	charDelta = 0
	
	nBrktsOpen = 0
	nBrktsClose = 0

	# Regular expression explained :
	# match Something.SomethingElse = SomethingElse;\n
	# where Something can have upper or lowercase letters or numbers, spaces, tabs, hyphens or double quotes
	#		SomethingElse can additionally have dots '.'
	# must be preeceded by newline - i.e. rule out comments that start with // or rhs of equals
	# Group match into three parts so the Something, SomethingElse and SomethingElse can all 
	#			be used in constructing the replacement string
	
	for m1 in re.finditer(r'(?<=\n)(["A-Za-z0-9 \t_-]*)\.(["A-Za-z0-9 \t_\.-]*)=(["0-9A-Za-z \t_\.-]*;\n)', fileTxt): 
		grps = m1.groups()
		if m1.lastindex == 3:
			if m1.start() > prevEnd or prevSection != grps[0]:
				if prevEnd > 0:
					txtAdded = "\n};\n"
					fileTxt = fileTxt[:prevEnd+charDelta] + txtAdded + fileTxt[prevEnd+charDelta:]
					charDelta += len(txtAdded)
					prevEnd = m1.end()
					nBrktsClose += 1
	
				txtAdded = grps[0] + "={\n  " + grps[1] + "=" + grps[2]		
				
				#ch1 = m1.start()+charDelta
				#ch2 = m1.end()+charDelta
				#print( str(m1.start()) + "-" + str(m1.end()) + ":" + str(prevEnd) + "***" + \
				#		repr(fileTxt[ch1-50:ch1]) + "***" + repr(fileTxt[ch1:ch2]) + \
				#		"***" + repr(txtAdded) + "***" + repr(fileTxt[ch2:ch2+50]) )
				
				fileTxt = fileTxt[:m1.start()+charDelta] + txtAdded + fileTxt[m1.end()+charDelta:]
				charDelta += len(txtAdded)  + m1.start() - m1.end()
				prevEnd = m1.end()
				prevSection = grps[0]
				nBrktsOpen += 1
			
			else:
				txtAdded = "  " + grps[1] + "=" + grps[2]		
				
				#ch1 = m1.start()+charDelta
				#ch2 = m1.end()+charDelta
				#print( str(m1.start()) + "-" + str(m1.end()) + ":" + str(prevEnd) + "***" + \
				#		repr(fileTxt[ch1-50:ch1]) + "***" + repr(fileTxt[ch1:ch2]) + \
				#		"***" + repr(txtAdded) + "***" + repr(fileTxt[ch2:ch2+50]) )
				
				fileTxt = fileTxt[:m1.start()+charDelta] + txtAdded + fileTxt[m1.end()+charDelta:]
				charDelta += len(txtAdded)  + m1.start() - m1.end()
				prevEnd = m1.end()
		else:
			print("We should have 3 matches here but we don't " )

	if nBrktsOpen > 0:
		txtAdded = "};\n"
		fileTxt = fileTxt[:prevEnd+charDelta] + txtAdded + fileTxt[prevEnd+charDelta:]
		#charDelta += len(txtAdded)
		#nBrktsClose += 1
			
		fileTxt = dotHeirarchyToPinnFormat(fileTxt)
	
	#print("Sections opened = %d, closed = %d" % (nBrktsOpen,nBrktsClose))
	
	return fileTxt
	
# ----------------------------------------- #

def findSectionBrakes(fileTxt):
	"""
	Find matching pairs of curley brackets {} and return their position in the string.
	"""
	opBrkt = []
	for result in re.finditer("{",fileTxt):
		opBrkt.append(result)
	
	clBrkt = []
	for result in re.finditer("}",fileTxt):
		clBrkt.append(result)
	
	nBrackets = len(opBrkt)
	if len(clBrkt) != nBrackets:
		raise Exception("Brackets {} are not balanced in file %d opening and %d closing." % (len(opBrkt), len(clBrkt)))
	
	#print("Brackets {} %d opening and %d closing." % (len(opBrkt), len(clBrkt)))

	sectionStart = []
	sectionEnd = []
	sectionDepth = []
	sectionInd = 0
	while len(opBrkt) > 0:
		findMatchingBrackets(opBrkt,clBrkt,sectionStart,sectionEnd,sectionDepth,0)
	
	return np.array(sectionStart), np.array(sectionEnd), np.array(sectionDepth)

# ----------------------------------------- #

def findMatchingBrackets(opBrkt,clBrkt,sectionStart,sectionEnd,sectionDepth,curDepth):
	"""
	Recursive function to find sections delimited by matching pairs of braces. 
	"""
	curOpBrkt = opBrkt.pop(0)
	sectionInd = len(sectionStart)
		
	sectionStart.append(curOpBrkt.start())
	sectionEnd.append(-1)
	sectionDepth.append(-1)
	
	while len(opBrkt) > 0 and clBrkt[0].start() > opBrkt[0].start():
		findMatchingBrackets(opBrkt,clBrkt,sectionStart,sectionEnd,sectionDepth,curDepth+1)

	curClBrkt = clBrkt.pop(0)
	sectionEnd[sectionInd] = curClBrkt.end()
	sectionDepth[sectionInd] = curDepth

# ----------------------------------------- #

def lineNumber(text, charNum):
	"""
	Convert a given character index in a string to a line number by counting the preceeding newlines
	"""
	ln = 0
	for mm in re.finditer("\n",text[:charNum]):
		ln += 1
	return ln

# ----------------------------------------- #

def test():
	"""
	Run tests.
	"""
	
	# Test dotHeirarchyToPinnFormat()
	testStr = 	"PatientRepresentation ={\n" + \
    			"  PatientVolumeName = \"plan\";\n" + \
    			"  CtToDensityName = \"RMH GE 120kV\";\n" + \
    			"  CtToDensityVersion = \"2012-08-14 10:56:29\";\n" + \
    			"  DMTableName = \"Standard Patient\";\n" + \
    			"  DMTableVersion = \"2003-07-17 12:00:00\";\n" + \
    			"  TopZPadding = 0;\n" + \
    			"  BottomZPadding = 0;\n" + \
    			"  HighResZSpacingForVariable = 0.2;\n" + \
    			"  OutsidePatientIsCtNumber = 0;\n" + \
    			"  OutsidePatientAirThreshold = 0.6;\n" + \
    			"  CtToDensityTableAccepted = 1;\n" + \
    			"  CtToDensityTableExtended = 0;\n" + \
  				"};\n" + \
  				"DoseGrid .VoxelSize .X = 0.4;\n" + \
  				"DoseGrid .VoxelSize .Y = 0.4;\n" + \
  				"DoseGrid .VoxelSize .Z = 0.4;\n" + \
  				"DoseGrid .Dimension .X = 125;\n" + \
  				"DoseGrid .Dimension .Y = 112;\n" + \
  				"DoseGrid .Dimension .Z = 90;\n" + \
  				"DoseGrid .Origin .X = -24.5082;\n" + \
  				"DoseGrid .Origin .Y = -19.3726;\n" + \
  				"DoseGrid .Origin .Z = -18.886;\n" + \
  				"DoseGrid .DisplayAsSecondary = 0;\n" + \
  				"DoseGrid .Display2d = 1;\n" + \
				"PatientRepresentation ={\n" + \
    			"  PatientVolumeName = \"plan\";\n" + \
    			"  CtToDensityName = \"RMH GE 120kV\";\n" + \
    			"  CtToDensityVersion = \"2012-08-14 10:56:29\";\n" + \
    			"};\n" + \
  				"RowLabelList ={\n" + \
                "  #0 ={\n" + \
                "    String = \"  1. Y = -19.50 cm\";\n" + \
                "  };\n" + \
                "  #1 ={\n" + \
                "    String = \"  2. Y = -18.50 cm\";\n" + \
                "  };\n" + \
  				"};\n" + \
				"\n"

	#outStr = dotHeirarchyToPinnFormat(testStr)
	#print(outStr)
	
	#testFile = '/home/dualta/code/python/Patient_27814/Plan_0/plan.Trial'
	#testFile = '/home/dualta/code/python/Patient_27814/Plan_0/plan.roi'
	#writeJson(testFile, testFile+'.json')
	import os
	
	testPath = '/home/dualta/code/python/Patient_27814/Plan_0/'
	for testFile in os.listdir(testPath):
		if 'json' in testFile or 'binary' in testFile:
			continue
		
		msg = "Trying " + testFile + " : "	
		try:		
			writeJson(testPath + testFile, testPath + testFile +'.json')
			print(msg + "ok")
		except:
			print(msg + "PROBLEM")
	
# ----------------------------------------- #

if __name__ == "__main__":
	"""
	Main function
	"""
	# Set up input argument parser
	parser = OptionParser("\nProcess a pinnacle object." + \
						"\n\n%s [options] pinnacle_file" % sys.argv[0])
	
	parser.add_option("-t","--test",dest="runTest",
							action="store_true", default=False, \
							help="Run test by converting a sample plan.Trial file to JSON file.")
	
	#parser.add_option("-n","--name",dest="annonName",
	#						type="string", action="store", default="NO^NAME", \
	#						help="Annonomize images by changing name to annonName.")
	
	(options, args) = parser.parse_args()

		
	if options.runTest:
		test()
	elif len(args) < 1:
		print("No pinnacle file found !!")             
		parser.print_help()
	else:
		filename = args[0]
		pinnObjList = read(filename)
		
		for scriptObj in pinnObjList:
			print scriptObj
