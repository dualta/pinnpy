#!/usr/bin/env python
# coding=utf-8

# cd /home/dualta/code/python
# from pinnpy import pinn
# pln = pinn.read('./Patient_27814/Plan_0/plan.Trial')

import logging, os, sys, re
import numpy as np
from matplotlib import pylab

import pinn

from optparse import OptionParser

# ----------------------------------------- #

def readPlanTrial(patientPlanDir):
	"""
	Read all the information out of a plan.Trial file for a given patient plan directory.
	"""	
	planTrialFile = os.path.join(patientPlanDir,'plan.Trial')
	planTrial = pinn.read(planTrialFile)
	return planTrial

# ----------------------------------------- #

def getPositions(planTrial, trNum=0, bmNum=0, cpNum=0):
	"""
	Extract the leaf and jaw positions out of the plan.Trial data
	"""
	beam = planTrial.TrialList[trNum].BeamList[bmNum]
	cp = beam.CPManager.CPManagerObject.ControlPointList[cpNum]
	mlcData = cp.MLCLeafPositions

	nLfPairs = mlcData.RawData.NumberOfPoints
	nDim = mlcData.RawData.NumberOfDimensions
	mlcPos = np.array(mlcData.RawData.Points.AsList).reshape((nLfPairs, nDim))
	
	lfOff = np.zeros(nLfPairs)
	for lf in range(nLfPairs):        
		offStr = mlcData.RowLabelList[lf].String
		lfOff[lf] = float( re.search( r'[0-9\.\-]*(?= cm)', offStr ).group() )
	
	jaws = [ cp.LeftJawPosition, cp.RightJawPosition, cp.TopJawPosition, cp.BottomJawPosition ] 
	
	return mlcPos, lfOff, jaws

# ----------------------------------------- #

def getFullPositions(planTrial, trNum=0, bmNum=0, cpNum=0):
	"""
	Get the leaf and jaw vertices data to enable plotting of the field aperture.
	"""
	curBm = planTrial.TrialList[trNum].BeamList[bmNum]
	curCp = curBm.CPManager.CPManagerObject.ControlPointList[cpNum]
	
	mlcPos, lfOff, jawPos = getPositions(planTrial, trNum, bmNum, cpNum)

	lfWidth = abs(lfOff[1]-lfOff[0]) * 0.5
	nLfPairs = len(lfOff)

	# Just plot the leaf edge	
	#lfEdgeOff = np.append(lfOff.reshape(nLfPairs,1)-lfWidth,lfOff.reshape(nLfPairs,1)+lfWidth,axis=1).reshape(nLfPairs*2,1)
	#lfEdge1 = np.append(mlcPos[:,0].reshape(nLfPairs,1),mlcPos[:,0].reshape(nLfPairs,1),axis=1).reshape(nLfPairs*2,1)
	#lfEdge2 = np.append(mlcPos[:,1].reshape(nLfPairs,1),mlcPos[:,1].reshape(nLfPairs,1),axis=1).reshape(nLfPairs*2,1)
	
	# Plot the whole leaf
	lfLength = 20.0
	# Leaf Corners: 
	#	D --- C		Plot in order A1->B1->C1->D1->A1->D1->A2->B2->C2->D2->A2->D2-> ...
	#   |     |
	#	A --- B
	lfEdgeOff = np.append(lfOff.reshape(nLfPairs,1)-lfWidth, lfOff.reshape(nLfPairs,1)-lfWidth, axis=1) # A -> B
	lfEdgeOff = np.append(lfEdgeOff, lfOff.reshape(nLfPairs,1)+lfWidth, axis=1) # B -> C
	lfEdgeOff = np.append(lfEdgeOff, lfOff.reshape(nLfPairs,1)+lfWidth, axis=1) # C -> D
	lfEdgeOff = np.append(lfEdgeOff, lfOff.reshape(nLfPairs,1)-lfWidth, axis=1) # D -> A
	lfEdgeOff = np.append(lfEdgeOff, lfOff.reshape(nLfPairs,1)+lfWidth, axis=1) # A -> D
	lfEdgeOff = lfEdgeOff.reshape(nLfPairs*6,1)

	lfEdge1 = np.append(mlcPos[:,0].reshape(nLfPairs,1)+lfLength, mlcPos[:,0].reshape(nLfPairs,1), axis=1) # A -> B
	lfEdge1 = np.append(lfEdge1, mlcPos[:,0].reshape(nLfPairs,1), axis=1) # B -> C
	lfEdge1 = np.append(lfEdge1, mlcPos[:,0].reshape(nLfPairs,1)+lfLength, axis=1) # C -> D
	lfEdge1 = np.append(lfEdge1, mlcPos[:,0].reshape(nLfPairs,1)+lfLength, axis=1) # D -> A
	lfEdge1 = np.append(lfEdge1, mlcPos[:,0].reshape(nLfPairs,1)+lfLength, axis=1) # A -> D
	lfEdge1 = lfEdge1.reshape(nLfPairs*6,1)
	
	lfEdge2 = np.append(mlcPos[:,1].reshape(nLfPairs,1)+lfLength, mlcPos[:,0].reshape(nLfPairs,1), axis=1) # A -> B
	lfEdge2 = np.append(lfEdge2, mlcPos[:,1].reshape(nLfPairs,1), axis=1) # B -> C
	lfEdge2 = np.append(lfEdge2, mlcPos[:,1].reshape(nLfPairs,1)+lfLength, axis=1) # C -> D
	lfEdge2 = np.append(lfEdge2, mlcPos[:,1].reshape(nLfPairs,1)+lfLength, axis=1) # D -> A
	lfEdge2 = np.append(lfEdge2, mlcPos[:,1].reshape(nLfPairs,1)+lfLength, axis=1) # A -> D
	lfEdge2 = lfEdge2.reshape(nLfPairs*6,1)
	
	lfEdge2 = -lfEdge2
	
	bank1Name = curCp.MLCLeafPositions.LabelList[0].String.split('(')[1].strip(' )')
	bank2Name = curCp.MLCLeafPositions.LabelList[1].String.split('(')[1].strip(' )')
	
	mlc = {}
	
	mlc[bank1Name] = {}
	mlc[bank1Name]['x'] = lfEdge1
	mlc[bank1Name]['y'] = lfEdgeOff
	
	mlc[bank2Name] = {}
	mlc[bank2Name]['x'] = lfEdge2
	mlc[bank2Name]['y'] = lfEdgeOff
	
	jaws = []
	jaws.append(dict(y = [ jawPos[0], jawPos[0] ], x = [ -30.0, 30.0 ]))
	jaws.append(dict(y = [ -jawPos[1], -jawPos[1] ], x = [ -30.0, 30.0 ]))
	jaws.append(dict(x = [ jawPos[2], jawPos[2] ], y = [ -30.0, 30.0 ]))
	jaws.append(dict(x = [ -jawPos[3], -jawPos[3] ], y = [ -30.0, 30.0 ]))
	
	return mlc, jaws
	
# ----------------------------------------- #

def plot(planTrial, trNum=0, bmNum=0, cpNum=0):
	"""
	Create a plot for a given 
	"""
	mlc, jaws = getFullPositions(planTrial, trNum=0, bmNum=0, cpNum=0)
		
	fig = pylab.figure()
	ax1 = fig.gca()
	ax1.hold(True)
	for bnk in mlc.keys():
		mlc[bnk]['plot'] = ax1.plot(mlc[bnk]['x'], mlc[bnk]['y'], '-k')
	
	xlim1, xlim2 = ax1.get_xlim()
	ylim1, ylim2 = ax1.get_ylim()
	xlim1 = max( xlim1, -20.0 )
	xlim2 = min( xlim2, 20.0 )
	ylim1 = max( ylim1, -20.0 )
	ylim2 = min( ylim2, 20.0 )

	for jw in jaws:
		jw['plot'] = ax1.plot(jw['x'], jw['y'],'-b')
		
	ax1.set_xlim( xlim1, xlim2 )
	ax1.set_ylim( ylim1, ylim2 )
	
	pylab.show()

# ----------------------------------------- #

if __name__ == '__main__':
	"""
	Main function
	"""
	# Set up input argument parser
	parser = OptionParser("\nPlot MLC aperture." + \
						"\n\t%s [options] <pinnacle_plan_path>" % sys.argv[0])
	
	parser.add_option("-t","--trial",dest="trNum",
							type="int", action="store", default=0, \
							help="Trial Index.")
	
	parser.add_option("-b","--beam",dest="bmNum",
							type="int", action="store", default=0, \
							help="Beam Index.")
	
	parser.add_option("-c","--cp",dest="cpNum",
							type="int", action="store", default=0, \
							help="Control Point Index.")
	
	(options, args) = parser.parse_args()

	if len(args) < 1:
		print("No pinnacle plan path found !!")   
		parser.print_help()
	else:
		if os.path.isdir(args[0]):
			patientPlanDir = args[0]
		else:
			os.path.realpath(args[0])

		planTrial = readPlanTrial(patientPlanDir)
		plot(planTrial, options.trNum, options.bmNum, options.cpNum)

