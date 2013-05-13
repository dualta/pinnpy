#!/usr/bin/env python
# coding=utf-8

import sys, os
import numpy as np
from optparse import OptionParser
from matplotlib import cm, pylab
from matplotlib.colors import LinearSegmentedColormap, colorConverter

import pinn
import imView

# ----------------------------------------- #

def readDose(planTrialFile, trNum, chooseBmInd=-1):
	"""
	Read a dose cube for a trial in a given plan and return as a numpy array

	Need to test reading dose for a variety of different prescriptions	
	
	Currently tested for:
		Dose is prescribed to a norm point, 
			beam weights are proportional to point dose 
			and control point dose is not stored.
	"""

	pln1 = pinn.read(os.path.join( os.path.dirname(planTrialFile),'plan.Trial'))
	pts = pinn.read(os.path.join( os.path.dirname(planTrialFile),'plan.Points'))
	
	nTrials = 1
	if pln1.has_key('TrialList'):
		nTrials = len(pln1.TrialList)
	
	assert( trNum >= 0 )
	assert( trNum < nTrials )

	if pln1.has_key('TrialList'):
		curTr = pln1.TrialList[trNum]
	else:
		curTr = pln1.Trial
	
	doseHdr = curTr.DoseGrid
	
	dose = np.zeros((doseHdr.Dimension.Z, doseHdr.Dimension.Y, doseHdr.Dimension.X))

	prescriptionPoint = []
	prescriptionDose = []
	prescriptionPointDose = []
	prescriptionPointDoseFactor = []
			
	for bInd, bm in enumerate(curTr.BeamList):
		if chooseBmInd >= 0 and bInd != chooseBmInd: 
			continue
		try:		
			# Get the name of the file where the beam dose is saved - PREVIOUSLY USED DoseVarVolume ? 		
			doseFile = os.path.join( os.path.dirname(planTrialFile), \
					"plan.Trial.binary.%03d" % int(bm.DoseVolume.split('-')[1]))

			# Read the dose from the file
			bmDose = np.fromfile(doseFile,dtype='float32')
		
			if bmDose.nbytes == 0:
				raise DoseInvalidException('')
		except:
			raise DoseInvalidException('Beam %d in trial %d has no stored dose. Try other trial [0-%d]' \
					% (bInd, trNum, nTrials-1))
		
		# Reshape to a 3D array		
		bmDose = bmDose.reshape(( doseHdr.Dimension.Z, doseHdr.Dimension.Y, doseHdr.Dimension.X ))
		
		# Solaris uses big endian schema. Almost everything else is little endian		
		if sys.byteorder == 'little':
			bmDose = bmDose.byteswap(True)
		
		doseFactor = 1.0
		
		# Weight the dose cube by the beam weight
		# Assume dose is prescribed to a norm point and beam weights are proportional to point dose
		doseAtPoint = 0.0
		
		for pp in curTr.PrescriptionList:
			if pp.Name == bm.PrescriptionName:
				prescriptionDose.append(pp.PrescriptionDose * pp.NumberOfFractions)
				if pp.WeightsProportionalTo == 'Point Dose':
					for pt in pts.PoiList:
						if pt.Name == pp.PrescriptionPoint:
							doseAtPoint = doseAtCoord(bmDose, doseHdr, pt.XCoord, pt.YCoord, pt.ZCoord)
							doseFactor = pp.PrescriptionDose * pp.NumberOfFractions * ( bm.Weight * 0.01 / doseAtPoint )
							
							prescriptionPoint.append([pt.XCoord, pt.YCoord, pt.ZCoord])
							prescriptionPointDose.append(doseAtPoint)
							prescriptionPointDoseFactor.append(doseFactor)
		
		dose += ( bmDose * doseFactor )

	for bm, pD, pp in zip(range(len(prescriptionPointDose)), prescriptionPointDose, prescriptionPoint):
		indPP = coordToIndex(doseHdr, pp[0], pp[1], pp[2])
		
	return dose, doseHdr

# ----------------------------------------- #

def readCT(planTrialFile):
	"""
	Read a CT cube for a plan
	"""	
	fp1 = open(os.path.join( os.path.dirname(planTrialFile),'plan.defaults'))
	imFile = fp1.readline().split(':')[1].strip()
	fp1.close()
	
	imFile = os.path.join( os.path.dirname(planTrialFile),imFile)
	imHdr = pinn.read(imFile+'.header')

	# Read the data from the file
	imData = np.fromfile(imFile+'.img',dtype='int16')

	# Reshape to a 3D array
	imData = imData.reshape((imHdr.z_dim,imHdr.y_dim,imHdr.x_dim))

	# Solaris uses big endian schema. Almost everything else is little endian		
	if sys.byteorder == 'little':
		if imHdr.byte_order == 1:
			imData = imData.byteswap(True)
	else:
		if imHdr.byte_order == 0:
			imData = imData.byteswap(True)
		 	
	return imData, imHdr

# ----------------------------------------- #

def plotCT(planTrialFile):
	"""
	Display the CT in a 3 plane image view gui
	"""
	ctData, ctHdr = readCT(planTrialFile)
	
	ctVoxSize = [ctHdr.z_pixdim,ctHdr.y_pixdim,ctHdr.x_pixdim]
	
	f1 = imView.slicesView( ctData, voxSize = ctVoxSize)
	
# ----------------------------------------- #

def plotDose(planTrialFile, trNum=0):
	"""
	Display the dose distribution in a 3 plane view gui
	"""
	doseData, doseHdr = readDose(planTrialFile, trNum)
	
	doseStartP = [ doseHdr.Origin.Z, doseHdr.Origin.Y, doseHdr.Origin.X ]
	doseVoxSize = [ doseHdr.VoxelSize.Z, doseHdr.VoxelSize.Y, doseHdr.VoxelSize.X ]

	print('Dose data dim = %s Max / Min Value = [%f/%f]' % (str(doseData.shape), np.max(doseData), np.min(doseData)))	
		
	cmapDose = cm.jet
	cmapDose.set_gamma(2.0)
	
	f1 = imView.slicesView( doseData, voxSize = doseVoxSize, cmap=cmapDose)
	
# ----------------------------------------- #

def plotDoseProfile(planTrialFile, trNum=0, dir='A', indX=-1, indY=-1, indZ=-1, bmInd=-1):
	"""
	Display a plot of a dose profile 
	"""
	doseData, doseHdr = readDose(planTrialFile, trNum, bmInd)
	
	if indX<0:
		indX = doseData.shape[2] / 2
	if indY<0:
		indY = doseData.shape[1] / 2
	if indZ<0:
		indZ = doseData.shape[0] / 2
		
	fig = pylab.figure()
	fig.hold(True)
	
	if dir == 'A':
		ax0 = fig.add_subplot(3,1,1)
		ax1 = fig.add_subplot(3,1,2)
		ax2 = fig.add_subplot(3,1,3)
	else:
		ax0 = fig.add_subplot(111)
			
	curAx = ax0
	if dir == 'X' or dir == 'A':
		profileX = profileAlongX(doseData, indZ, indY)
		curAx.plot(profileX)
		curAx.set_xlabel('X [pixels]')	
		if dir == 'A':
			dotX = curAx.plot(indX, profileX[indX], '.r', markersize=10)			
			curAx = ax1

	if dir == 'Y' or dir == 'A':
		profileY = profileAlongY(doseData, indZ, indX)
		curAx.plot(profileY)
		curAx.set_xlabel('Y [pixels]')	
		if dir == 'A':
			dotY = curAx.plot(indY, profileY[indY], '.r', markersize=10)			
			curAx = ax2

	if dir == 'Z' or dir == 'A':
		profileZ = profileAlongZ(doseData, indY, indX)
		curAx.plot(profileZ)		
		curAx.set_xlabel('Z [pixels]')	
		if dir == 'A':
			dotZ = curAx.plot(indZ, profileZ[indZ], '.r', markersize=10)			
		
	pylab.show()

# ----------------------------------------- #

def plotDoseOnCT(planTrialFile, trNum=0):
	"""
	Display the dose distribution overlaid on the CT in a 3 plane view gui
	"""
	ctData, ctHdr = readCT(planTrialFile)
	ctStartP = [ ctHdr.z_start, ctHdr.y_start, ctHdr.x_start ]
	ctVoxSize = [ ctHdr.z_pixdim,ctHdr.y_pixdim,ctHdr.x_pixdim ]
	cmapCT = cm.bone
	cmapCT.set_gamma(1.0)
	
	doseData, doseHdr = readDose(planTrialFile, trNum)
	doseStartP = [ doseHdr.Origin.Z, doseHdr.Origin.Y, doseHdr.Origin.X ]
	doseVoxSize = [ doseHdr.VoxelSize.Z, doseHdr.VoxelSize.Y, doseHdr.VoxelSize.X ]
	
	cmapDose = cm.jet	# Use jet colormap to paint dose
	cmapDose.set_gamma(3.0)	# Bias spread of colors to higher doses

	# Make dose transparent with lower does more transparent.
	cmapDose._lut[:-3,-1] = np.linspace(0.0, 0.8, cmapDose.N)
					
	f1 = imView.slicesView(
			im1_data=ctData, im1_startP=ctStartP, im1_voxSize=ctVoxSize, im1_cmap=cmapCT, 
			im2_data=doseData, im2_startP=doseStartP, im2_voxSize=doseVoxSize, im2_cmap=cmapDose)

# ----------------------------------------- #

def coordToIndex(imHdr, xCoord, yCoord, zCoord):
	"""
	Convert corrdinate positions to coordinate indices
	"""
	
	# coord in cm from primary image centre
	xCoord -= imHdr.Origin.X
	yCoord = imHdr.Origin.Y + imHdr.Dimension.Y * imHdr.VoxelSize.Y - yCoord
	zCoord -= imHdr.Origin.Z
	
	# coord now in cm from start of dose cube
	xCoord /= imHdr.VoxelSize.X
	yCoord /= imHdr.VoxelSize.Y
	zCoord /= imHdr.VoxelSize.Z
	
	# coord now in pixels from start of dose cube
	return xCoord, yCoord, zCoord

# ----------------------------------------- #

def doseAtCoord(doseData, doseHdr, xCoord, yCoord, zCoord):
	"""
	Linearly interpolate the dose at a set of coordinates
	"""
	xCoord, yCoord, zCoord = coordToIndex(doseHdr, xCoord, yCoord, zCoord)
	
	xP = np.floor(xCoord)
	yP = np.floor(yCoord)
	zP = np.floor(zCoord)

	xF = xCoord - xP
	yF = yCoord - yP
	zF = zCoord - zP

	dose = 	doseAtIndex(doseData, zP, yP, xP) * (1.0-zF) * (1.0-yF) * (1.0-xF) + \
			doseAtIndex(doseData, zP, yP, xP+1) * (1.0-zF) * (1.0-yF) * xF + \
			doseAtIndex(doseData, zP, yP+1, xP) * (1.0-zF) * yF * (1.0-xF) + \
			doseAtIndex(doseData, zP, yP+1, xP+1) * (1.0-zF) * yF * xF + \
			doseAtIndex(doseData, zP+1, yP, xP) * zF * (1.0-yF) * (1.0-xF) + \
			doseAtIndex(doseData, zP+1, yP, xP+1) * zF * (1.0-yF) * xF + \
			doseAtIndex(doseData, zP+1, yP+1, xP) * zF * yF * (1.0-xF) + \
			doseAtIndex(doseData, zP+1, yP+1, xP+1) * zF * yF * xF

	return dose

# ----------------------------------------- #

def doseAtIndex(dose, indZ, indY, indX):
	"""
	Return dose at indices.
	Beyond end of dose array return zero
	"""
	try:
		dd = dose[indZ,indY,indX]
		if indZ > 0 and indY > 0 and indX > 0:
			return dd
		else:
			return 0.0
	except IndexError:
		return 0.0

# ----------------------------------------- #

def profileAlongX(dose, indZ, indY):
	"""
	Return a 1D array of dose values along a profile in the 
	X axis direction at a specified Z and Y position given by array indices.
	"""
	
	profile1 = np.zeros(dose.shape[2])
	print("%s : %s" % (str(dose.shape),str(profile1.shape)))	
	for dd in xrange(dose.shape[2]):
		profile1[dd] = dose[indZ][indY][dd]

	return profile1

# ----------------------------------------- #

def profileAlongY(dose, indZ, indX):
	"""
	Return a 1D array of dose values along a profile in the 
	Y axis direction at a specified Z and X position given by array indices.
	"""
	profile1 = np.zeros(dose.shape[1])
	for dd in xrange(dose.shape[1]):
		profile1[dd] = dose[indZ][dd][indX]

	return profile1

# ----------------------------------------- #

def profileAlongZ(dose, indY, indX):
	"""
	Return a 1D array of dose values along a profile in the 
	Z axis direction at a specified Y and X position given by array indices.
	"""
	profile1 = np.zeros(dose.shape[0])
	for dd in xrange(dose.shape[0]):
		profile1[dd] = dose[dd][indY][indX]

	return profile1

# ----------------------------------------- #

class DoseInvalidException(Exception):
	pass

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
