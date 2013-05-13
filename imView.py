#!/usr/bin/env python

from matplotlib import pylab
from matplotlib import widgets
from matplotlib import pyplot
from matplotlib import cm

import numpy as np

# --------------------------------------- #

class slicesView():

	# --------------------------------------- #

	def __init__( self, data=[], figure=-1, slices=[], \
				startP=[0.0,0.0,0.0], voxSize=[1.0,1.0,1.0], cmap=cm.bone, \
				im1_data=-1, im1_startP=-1, im1_voxSize=-1, im1_cmap=-1, \
				im2_data=-1, im2_startP=-1, im2_voxSize=-1, im2_cmap=-1, \
				interpType='linear'):
		"""
		Create a GUI displaying the desired data in 3 orthogonal views.
		The user can click to select a view and then press keys n and p to move between slices
		and press keys a, s and c to switch between views.
		Arguments:
			data	The data as a 3D numpy array to be displayed.
			figure	Plot axes in an existing figure along the right hand side
						(default is to create a new figure window)
			slices	A 3 element list of slice indices to initialize the 3 viewing axes
						(default to centre of data cube in each direction)
			startP	A 3 element list indicating the start position for the slice position axes.
						(default to [0,0,0])
			voxSize	A 3 element list indicating the voxel size along each axes.
						(default to [1,1,1])
			
			cmap	A matplotlib colormap used to display the image (default is cm.bone)
			
		----------------------------------
		When supplying two or three data arrays the following arguments replace the single data equivalents
			im1_data	The data as a 3D numpy array to be displayed as the first imageset.
			im1_startP	A 3 element list for the start position of im1_data
			im1_voxSize	A 3 element list for the voxel size of im1_data
			im1_cmap	A matplotlib colormap to be assigned to im1_data
			
			im2_data	The data as a 3D numpy array to be displayed as the second imageset.
			im2_startP	A 3 element list for the start position of im2_data
			im2_voxSize	A 3 element list for the voxel size of im2_data
			im2_cmap	A matplotlib colormap to be assigned to im2_data
		"""
		
		# If we've been given a figure then use it otherwise make a new figure
		if type(figure) is int and figure < 0:
			self._fig = pylab.figure()
		else:
			self._fig = figure

		# Disable native keyboard shortcuts
		for key in pyplot.rcParams:
			if 'keymap.' in key:
				pyplot.rcParams[key] = ''
		
		figWidth, figHeight = self._fig.get_size_inches()
		
		btmBrdr = 0.02 # 0.05
		topBrdr = 0.02 # 0.05
		midBrdrH = 0.02 # 0.05
		midBrdrW = 0.05 # 0.05
		lftBrdr = 0.2
		rtBrdr = 0.05
		btmFigHeightShare = 0.4
		
		topFigH = 1.0 - topBrdr - btmBrdr - midBrdrH
		btmFigH = topFigH * btmFigHeightShare
		topFigH -= btmFigH
		btmFigW = btmFigH
		topFigW = btmFigW * 2.0 + midBrdrW
		
		self.connect()
		
		self._ax = []
		self._ax.append( self._fig.add_axes([lftBrdr, btmBrdr+btmFigH+midBrdrH, topFigW, topFigH]))
		self._ax.append( self._fig.add_axes([lftBrdr, btmBrdr, btmFigW, btmFigH]))
		self._ax.append( self._fig.add_axes([lftBrdr+btmFigW+midBrdrW, btmBrdr, btmFigW, btmFigH]))
		
		self.processArguments(data, slices, startP, voxSize, cmap, im1_data, im1_startP, im1_voxSize, \
						im1_cmap, im2_data, im2_startP, im2_voxSize, im2_cmap, interpType)
		
		self.initializeImageSlices()
		
		self._widetAx = []
		for aa in self._ax:
			aa.get_xaxis().set_visible( False )
			aa.get_yaxis().set_visible( False )
			self._widetAx.append( widgets.Button(aa,'') )
		
		self._widetAx[0].on_clicked( self.clickAx1 )
		self._widetAx[1].on_clicked( self.clickAx2 )
		self._widetAx[2].on_clicked( self.clickAx3 )
		
		for ax in range(3):
			self.refreshIm(ax)
		self.clickAx1('')
		
		pylab.show()

	# --------------------------------------- #
	
	def refreshIm(self, ax):
		"""
		Refresh the slice image in the desired axes.
		"""
		
		if self._axOrien[ax] == 0:		
			self._im1_dispSlices[ax] = self._im1_data[ self._im1_slice[ax], :, : ]
			self._ax[ax].set_aspect( self._im1_voxSize[1] / self._im1_voxSize[2] )
		elif self._axOrien[ax] == 1:		
			self._im1_dispSlices[ax] = self._im1_data[:,self._im1_slice[ax],:]
			self._ax[ax].set_aspect( self._im1_voxSize[0] / self._im1_voxSize[2] )
		else:		
			self._im1_dispSlices[ax] = self._im1_data[:,:,self._im1_slice[ax]]
			self._ax[ax].set_aspect( self._im1_voxSize[0] / self._im1_voxSize[1] )
		
		self._im1[ax].set_array(self._im1_dispSlices[ax])
		
		if self._plotIm2:
			self._im2_slice[ax] = self.setSecondarySlice(
										self._im2_axes, self._im2_data.shape, ax)
			self._im2_dispSlices[ax] = self.interpSecondary(
										self._im2_data, self._im2_slice, self._im2_voxSize, ax)
			self._im2[ax].set_array(self._im2_dispSlices[ax])
		
		#print('Ax %d - %s : %s' % (ax, str(self._ax[ax].get_aspect()), str(self._im1_voxSize)) )
		pylab.show()
	
	# --------------------------------------- #
	
	def initializeImageSlices(self):
		"""
		Extract the slices to display and initialize the plot arrays
		"""
		
		self._im1_dispSlices = []		
		self._im1 = [] 
		
		for ax in range(3):
			if self._axOrien[ax] == 0:		
				self._im1_dispSlices.append( self._im1_data[ self._im1_slice[ax], :, : ] )
			elif self._axOrien[ax] == 1:
				self._im1_dispSlices.append( self._im1_data[ :, self._im1_slice[ax], : ] )
			else:
				self._im1_dispSlices.append( self._im1_data[ :, :, self._im1_slice[ax] ] )
			
			self._ax[ax].hold(True)
			self._im1.append( self._ax[ax].imshow( self._im1_dispSlices[ax], cmap = self._im1_cmap, \
					vmax=self._im1_max, vmin=self._im1_min ))  
			self._im1[-1].set_extent(self._im1_extent[self._axOrien[ax]])
		
		if self._plotIm2:
			self._im2_slice = np.zeros(3)
			self._im2_dispSlices = []
			self._im2 = []
			
			if ax == 0:
				self._fig.colorbar(self._im2[ax], self._ax[ax])

			for ax in range(3):
				self._im2_slice[ax] = self.setSecondarySlice(
										self._im2_axes, self._im2_data.shape, ax)
				self._im2_dispSlices.append( self.interpSecondary(
										self._im2_data, self._im2_slice, self._im2_voxSize, ax) )
				self._im2.append( self._ax[ax].imshow(self._im2_dispSlices[ax], cmap = self._im2_cmap, \
						vmax=self._im2_max, vmin=self._im2_min ))
				self._im2[-1].set_extent(self._im2_extent[self._axOrien[ax]])
		
	# --------------------------------------- #
	
	def processArguments(self, data, slices, startP, voxSize, cmap, im1_data, im1_startP, \
						im1_voxSize, im1_cmap, im2_data, im2_startP, im2_voxSize, im2_cmap, \
						interpType):
		
		# If there is no data then generate some random test data
		self._plotIm2 = False
		self._imInterpType = interpType
		
		if type(im1_data) is int:
			self._im1_data = data
			self._im1_voxSize = voxSize
			self._im1_startP = startP
			self._im1_cmap = cmap
		else:
			self._im1_data = im1_data
			if type(im1_startP) is int:
				self._im1_startP = startP
			else:
				self._im1_startP = im1_startP
				
			if type(im1_voxSize) is int:
				self._im1_voxSize = voxSize
			else:
				self._im1_voxSize = im1_voxSize
			
			if type(im1_cmap) is int:
				self._im1_cmap = cmap
			else:
				self._im1_cmap = im1_cmap
			
			self._im1_max = self._im1_data.max()
			self._im1_min = self._im1_data.min()

			if not (type(im2_data) is int):
				self._im2_data = im2_data
				self._plotIm2 = True
				if type(im2_startP) is int:
					self._im2_startP = im1_startP
				else:
					self._im2_startP = im2_startP
				
				if type(im2_voxSize) is int:
					self._im2_voxSize = im1_voxSize
				else:
					self._im2_voxSize = im2_voxSize
			
				if type(im2_cmap) is int:
					self._im2_cmap = im1_cmap
				else:
					self._im2_cmap = im2_cmap
				
				self._im2_max = self._im2_data.max()
				self._im2_min = self._im2_data.min()

		# If arguments specify slice indices then use them otherwise set as centre of image
		self._im1_slice = np.zeros(3,dtype='int16')		
		if len(slices) == 3:
			self._im1_slice[0] = slices[0]
			self._im1_slice[1] = slices[1]
			self._im1_slice[2] = slices[2]
		else:
			self._im1_slice[0] = self._im1_data.shape[ 0 ] / 2
			self._im1_slice[1] = self._im1_data.shape[ 1 ] / 2
			self._im1_slice[2] = self._im1_data.shape[ 2 ] / 2
		
		self._axOrien = np.arange(3, dtype='int16')
		
		self._im1_axes = self.setImageAxes(self._im1_data.shape, self._im1_voxSize, self._im1_startP)
		self._im1_extent = [ 	[ self._im1_axes[2][0], self._im1_axes[2][-1], self._im1_axes[1][0], self._im1_axes[1][-1] ], \
								[ self._im1_axes[2][0], self._im1_axes[2][-1], self._im1_axes[0][0], self._im1_axes[0][-1] ], \
								[ self._im1_axes[1][0], self._im1_axes[1][-1], self._im1_axes[0][0], self._im1_axes[0][-1] ] ]
		
		if self._plotIm2:
			self._im2_axes = self.setImageAxes(self._im2_data.shape, self._im2_voxSize, self._im2_startP)
			self._im2_extent = [ 	[ self._im2_axes[2][0], self._im2_axes[2][-1], self._im2_axes[1][0], self._im2_axes[1][-1] ], \
									[ self._im2_axes[2][0], self._im2_axes[2][-1], self._im2_axes[0][0], self._im2_axes[0][-1] ], \
									[ self._im2_axes[1][0], self._im2_axes[1][-1], self._im2_axes[0][0], self._im2_axes[0][-1] ] ]
			
	# --------------------------------------- #
	
	def setImageAxes(self, imData_shape, im_voxSize, im_startP):
		"""
		Calculate the x, y and z axes as numpy ranges.
		"""
		im_ax0 = np.arange(imData_shape[0]) * im_voxSize[0] + im_startP[0]
		im_ax1 = np.arange(imData_shape[1]) * im_voxSize[1] + im_startP[1]
		im_ax2 = np.arange(imData_shape[2]) * im_voxSize[2] + im_startP[2]
		
		im_axes = [im_ax0, im_ax1, im_ax2]
		
		return im_axes
		
	# --------------------------------------- #
	
	def setSecondarySlice(self, im_axes, imData_shape, ax):
		"""
		Calculate slice indices of a secondary image to be overlaid on the current primary slices. 
		"""
		if self._axOrien[ax] == 0:
			im_slice = np.interp(self._im1_axes[0][self._im1_slice[ax]], im_axes[0], np.arange(imData_shape[0]))
		elif self._axOrien[ax] == 1:
			im_slice = np.interp(self._im1_axes[1][self._im1_slice[ax]], im_axes[1], np.arange(imData_shape[1]))
		else:
			im_slice = np.interp(self._im1_axes[2][self._im1_slice[ax]], im_axes[2], np.arange(imData_shape[2]))
		
		return im_slice		
	
	# --------------------------------------- #
	
	def interpSecondary(self, imData, imSlice, voxSize, ax):
		"""
		Interpolate a set of image slices at the required positions 
		"""		
		if self._imInterpType == 'linear':
			return self.interpSecondaryNearNeighbour(imData, imSlice, voxSize, ax)
		elif self._imInterpType == 'neighbour':
			return self.interpSecondaryLinear(imData, imSlice, voxSize, ax)
		else:
			raise InvalidArgumentsException("Unrecognized interpolation type : %s" \
					% str(self._imInterpType) )

	# --------------------------------------- #
	
	def interpSecondaryLinear(self, imData, imSlice, voxSize, ax):			
		"""
		Interpolate a set of image slices at the required positions 
		using linear interpolation.
		"""
		slice_flr = np.floor(imSlice[ax])
				
		if self._axOrien[ax] == 0:
			wt1 = ( imSlice[ax] - slice_flr ) / voxSize[0]
			wt0 = 1.0 - wt1
			dispSlice = imData[int(slice_flr),:,:] * wt0 + imData[int(slice_flr+1),:,:] * wt1
		elif self._axOrien[0] == 1:
			wt1 = ( imSlice[ax] - slice_flr ) / voxSize[1]
			wt0 = 1.0 - wt1
			dispSlice = imData[:,int(slice_flr),:] * wt0 + imData[:,int(slice_flr+1),:] * wt1
		else:
			wt1 = ( imSlice[ax] - slice_flr ) / voxSize[2]
			wt0 = 1.0 - wt1
			dispSlice = imData[:,:,int(slice_flr)] * wt0 + imData[:,:,int(slice_flr+1)] * wt1
		
		return dispSlice

	# --------------------------------------- #
	
	def interpSecondaryNearNeighbour(self, imData, imSlice, voxSize, ax):			
		"""
		Interpolate a set of image slices at the required positions
		using nearest neighbour interpolation.
		"""
		slice_rnd = np.int16(imSlice[ax]+0.5)
		
		if self._axOrien[ax] == 0:
			dispSlice = imData[slice_rnd,:,:]
		elif self._axOrien[ax] == 1:
			dispSlice = imData[:,slice_rnd,:]
		else:
			dispSlice = imData[:,:,slice_rnd]
				
		return dispSlice
		
	# --------------------------------------- #

	def connect(self):		
		'connect to all the events we need'
		self._evkp = self._fig.canvas.mpl_connect('key_press_event', self.keyPress)
	
	# --------------------------------------- #

	def disconnect(self):
		'disconnect all the stored connection ids'
		self._ax1.figure.canvas.mpl_disconnect(self._evkp)
			
	# --------------------------------------- #
		
	def clickAx1(self, event):
		"""
		First axes has been clicked so indicate it as the selected axes.
		"""
		self._curAx = 0
		[brdr.set_linewidth(2.0) for brdr in self._ax[0].spines.itervalues()]
		[brdr.set_linewidth(0.1) for brdr in self._ax[1].spines.itervalues()]
		[brdr.set_linewidth(0.1) for brdr in self._ax[2].spines.itervalues()]
		[brdr.set_color('white') for brdr in self._ax[0].spines.itervalues()]
		[brdr.set_color('black') for brdr in self._ax[1].spines.itervalues()]
		[brdr.set_color('black') for brdr in self._ax[2].spines.itervalues()]
		pylab.show()
		
	# --------------------------------------- #

	def clickAx2(self, event):
		"""
		Second axes has been clicked so indicate it as the selected axes.
		"""
		self._curAx = 1		
		[brdr.set_linewidth(2.0) for brdr in self._ax[1].spines.itervalues()]
		[brdr.set_linewidth(0.1) for brdr in self._ax[0].spines.itervalues()]
		[brdr.set_linewidth(0.1) for brdr in self._ax[2].spines.itervalues()]
		[brdr.set_color('white') for brdr in self._ax[1].spines.itervalues()]
		[brdr.set_color('black') for brdr in self._ax[0].spines.itervalues()]
		[brdr.set_color('black') for brdr in self._ax[2].spines.itervalues()]
		pylab.show()
		
	# --------------------------------------- #
	
	def clickAx3(self, event):
		"""
		Third axes has been clicked so indicate it as the selected axes.
		"""
		self._curAx = 2		
		[brdr.set_linewidth(2.0) for brdr in self._ax[2].spines.itervalues()]
		[brdr.set_linewidth(0.1) for brdr in self._ax[0].spines.itervalues()]
		[brdr.set_linewidth(0.1) for brdr in self._ax[1].spines.itervalues()]
		[brdr.set_color('white') for brdr in self._ax[2].spines.itervalues()]
		[brdr.set_color('black') for brdr in self._ax[0].spines.itervalues()]
		[brdr.set_color('black') for brdr in self._ax[1].spines.itervalues()]
		pylab.show()
		
	# --------------------------------------- #
	
	def keyPress(self,event):
		"""
		Respond to a keyboard button
		"""
		#print("Key %s has been pressed on axes %d" % (event.key, self._curAx))
		if event.key is 'n':
			self.nextIm()
		elif event.key is 'p':
			self.prevIm()
		elif event.key is 'up':
			self.prevIm()
		elif event.key is 'down':
			self.nextIm()
		elif event.key is 'a':
			self.axToAxial()
		elif event.key is 's':
			self.axToSag()
		elif event.key is 'c':
			self.axToCoron()
		
	# --------------------------------------- #
	
	def nextIm(self):
		"""
		Move image in current axes to next slice.
		"""
		self._im1_slice[self._curAx] += 1
		self.refreshIm(self._curAx)
		
	# --------------------------------------- #
	
	def prevIm(self):
		"""
		Move image in current axes to next slice.
		"""
		self._im1_slice[self._curAx] -= 1
		self.refreshIm(self._curAx)
		
	# --------------------------------------- #
	
	def axToAxial(self):
		"""
		Change the slice orientation of the current axes to display an axial slice
		"""
		if self._axOrien[self._curAx] != 0:
			self._axOrien[self._curAx] = 0
			self._im1_slice[self._curAx] = self._im1_data.shape[0] / 2
			self._ax[self._curAx].set_aspect( self._im1_voxSize[1] / self._im1_voxSize[2] )
			self.refreshIm(self._curAx)
		
	# --------------------------------------- #
	
	def axToSag(self):
		"""
		Change the slice orientation of the current axes to display a saggital slice
		"""
		if self._axOrien[self._curAx] != 2:
			self._axOrien[self._curAx] = 2
			self._im1_slice[self._curAx] = self._im1_data.shape[2] / 2
			self._ax[self._curAx].set_aspect( self._im1_voxSize[0] / self._im1_voxSize[1] )
			self.refreshIm(self._curAx)
		
	# --------------------------------------- #
	
	def axToCoron(self):
		"""
		Change the slice orientation of the current axes to display a coronal slice
		"""
		if self._axOrien[self._curAx] != 1:
			self._axOrien[self._curAx] = 1
			self._im1_slice[self._curAx] = self._im1_data.shape[1] / 2
			self._ax[self._curAx].set_aspect( self._im1_voxSize[0] / self._im1_voxSize[2] )
			self.refreshIm(self._curAx)
		
	# --------------------------------------- #
		
	def mouseMove(self,event):
		print("Mouse motion ...")		
		#print("Key %s has been pressed" % event.key)

	# --------------------------------------- #

class InvalidArgumentsException(Exception):
	pass

# --------------------------------------- #

if __name__ == '__main__':
	f1 = slicesView()
	
