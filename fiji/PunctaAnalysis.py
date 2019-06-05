#@ File(label='Input filename') sipmm_inputFile
#@ File(label='Output directory',style='directory') sipmm_outputFile
#@ Integer(label='Minimum punctum size',value=4) minPSize
#@ Integer(label='Minimum punctum size',value=80) maxPSize
#@ Boolean (value=false) debugging
#@ Boolean (value=false) two_channels

#@OpService ops
#@UIService ui
#@DatasetService ds

import os 
import math
from ij import IJ, ImagePlus
from loci.plugins import BF
from ij.plugin import ChannelSplitter
from net.imglib2.img.display.imagej import ImageJFunctions
from net.imglib2.type.numeric.real import FloatType,DoubleType
from net.imglib2.type.numeric.integer import UnsignedByteType
from net.imglib2.algorithm.neighborhood import HyperSphereShape
from net.imglib2.view import Views
from net.imglib2.roi import Regions, Masks
from net.imglib2.roi.labeling import LabelRegions
from net.imglib2.algorithm.labeling.ConnectedComponents import StructuringElement

### UTILITY FUNCTIONS
from net.imagej.ops import Ops
from datetime import datetime

def log(message):
	msg = "{}\t{}\n".format(datetime.now().isoformat(),message)
	with open(sipmm_outputFile.getAbsolutePath()+"/"+sipmm_inputFile.getName()+"-log.txt","a") as f:
		f.write(msg)
	print(msg)

def getMIP(imp): 
	if isinstance(imp,ImagePlus):
		im = ImageJFunctions.wrap(imp)
	else:
		im = imp	
	
	projected = ops.create().img([ im.dimension(d) for d in [0,1] ])
	
	# Create the op and run it
	proj_op = ops.op(getattr(Ops.Stats, "Max"), im)
	ops.transform().project(projected, im, proj_op, 2)
	
	return projected

def roi(mask, image):
	# Convert ROI from R^n to Z^n.
	#discreteROI = Views.raster(Masks.toRealRandomAccessible(mask))
	# Apply finite bounds to the discrete ROI.
	boundedDiscreteROI = Views.interval(mask, image)
	# Create an iterable version of the finite discrete ROI.
	iterableROI = Regions.iterable(boundedDiscreteROI)
	return iterableROI

def countTrue(mask):
	n = 0
	for px in Regions.iterable(mask):
		n=n+1
	return n

### END UTILITY FUNCTIONS

outdir = sipmm_outputFile.getAbsolutePath()

#imps = BF.openImagePlus()

from ij import IJ
if debugging:
	IJ.run("Close All")

from loci.formats import ImageReader
from loci.formats import MetadataTools
from loci.plugins.in import ImporterOptions
reader = ImageReader()
omeMeta = MetadataTools.createOMEXMLMetadata()
reader.setMetadataStore(omeMeta)
reader.setId(sipmm_inputFile.getAbsolutePath())
seriesCount = reader.getSeriesCount()
reader.close()

log('Found {} series'.format(seriesCount))

outfile = os.path.join(outdir,'results.csv')
h = 'Name,path,Rarea,Rmean,Rstd,Garea,Gmean,Gstd,GQarea,GQmean,GQintden,GQstd,nPunctae,RMregions,maxxxxx'
with open(outfile,'a') as of:
		of.write(h+'\n')

for impi in range(seriesCount):
	log('Analyzing series {}/{}...'.format(impi+1,seriesCount))
	options = ImporterOptions()
	options.setId(sipmm_inputFile.getAbsolutePath())
	options.clearSeries()
	options.setSeriesOn(impi,True)

	imp, = BF.openImagePlus(options)

	#Separate Green, Red
	chans = ChannelSplitter.split(imp)
	if two_channels:
		if len(chans)!=2:
			log('ERROR! Expecting a 2-channel images and got {}'.format(len(chans)))
		green, red = chans
	else:
		if len(chans)!=3:
			log('ERROR! Expecting a 3-channel images and got {}'.format(len(chans)))
		green, red, nuc = chans
		
	
	# MIP Green
	green_mip = getMIP(green)
	if debugging:
		ui.show('GREEN_MIP',green_mip)

	# MIP Red
	red_mip = getMIP(red)
	if debugging:
		ui.show('RED_MIP',red_mip)

	# Calculate T = Mean+Std*.25
	# Set threshold (T,65k)
	# Convert to Mask
	Rmean = ops.stats().mean(red_mip).getRealDouble()
	Rstd = ops.stats().stdDev(red_mip).getRealDouble()
	T = Rmean*.25
	# D for particlemask
	D = Rmean + Rstd*0.25
	log('Calculated threshold for the red is {}'.format(T))
	red_mask = ops.threshold().apply(ops.convert().float32(red_mip),FloatType(T))
	
	particlemask = ops.threshold().apply(ops.convert().float32(red_mip),FloatType(D))

	# "Opening" with "Area"=5 px^2
	# "Dilation" with Neighb=1, Count=1
	red_mask = ops.morphology().open(red_mask,[HyperSphereShape(2)])
	red_mask = ops.morphology().dilate(red_mask,HyperSphereShape(1))
	
	particlemask = ops.morphology().open(particlemask,[HyperSphereShape(2)])
	particlemask = ops.morphology().dilate(particlemask,HyperSphereShape(1))

	# Perform Top Hat with area=maxPSize
	r = math.ceil(math.sqrt(maxPSize/3.141593))
	green_tophat = ops.morphology().topHat(green_mip,[HyperSphereShape(long(r))])
	if debugging:
		ui.show('GREEN_TOPHAT',green_tophat)
	
	# "MASK"
	# AND operation between MIP Green and "MASK"
	green_masked_tophat = ops.eval("g * uint8(m)", {"g":green_tophat,"m":red_mask})
	if debugging:
		ui.show('GREEN_MASKED_TOPHAT',green_masked_tophat)
	
	# Threshold (1,65k)
	v = green_masked_tophat.firstElement().copy()
	v.set(1)
	green_mask = ops.create().img(red_mask)
	ops.threshold().apply(green_mask,green_masked_tophat,v)

	# Region statistics
	# Threshold T = Mean+Std*1.5
	# Convert to Mask
	R = Regions.sample(Regions.iterable(green_mask),green_masked_tophat)
	Gmean = ops.stats().mean(R).getRealDouble()
	Gstd = ops.stats().stdDev(R).getRealDouble()
	T = Gmean + Gstd*3.5
	log('Calculated threshold for the green is {}'.format(T))
	green_mask = ops.create().img(red_mask)
	ops.threshold().apply(green_mask,ops.convert().float32(green_masked_tophat),FloatType(T))

	if debugging:
		print green_mask
		ui.show('GREEN_MASK',green_mask)
	
	# Analyze particles (minPSize-maxPSize) (default: 4-80)
	# Create new object mask
	log('Creating cleaned mask and counting....')
	green_mask_new = ops.create().img(green_mask)
	from jarray import array
	pp = array([0,0],'l')
	nPunctae=0
	green_mask_labeling = ops.labeling().cca(green_mask,StructuringElement.FOUR_CONNECTED)
	if debugging:
		log('Green max is : {}'.format(ops.stats().max(green_mask)))
		ui.show('GREEN_MASK_LABEL',green_mask_labeling.getIndexImg())
	for r in LabelRegions(green_mask_labeling):
		print r.size()
		if r.size()>=minPSize and r.size()<=maxPSize:
			nPunctae=nPunctae+1
			rc = r.localizingCursor()
			gc = green_mask_new.randomAccess()
			while rc.hasNext():
				rc.fwd()
				rc.localize(pp)
				gc.setPosition(pp)
				gc.get().set(1)

	log('Done! Found {} punctae within range'.format(nPunctae))
	
	if debugging:
		ui.show('RED_MASK',red_mask)
		ui.show('GREEN_MASK_CLEANED',green_mask_new)

	#analyzing particles from non inverted mask
	mask_labeling = ops.labeling().cca(particlemask,StructuringElement.EIGHT_CONNECTED)	
	maxxxxp = 0
	labelingIndex=mask_labeling.getIndexImg()
	regionsxx=LabelRegions(mask_labeling)
	region_labels = list(regionsxx.getExistingLabels())
	for region in regionsxx:
			regionsssss=region.size()
			if regionsssss>maxxxxp:
				maxxxxp = int(regionsssss)
	extravar = 10
	log('Number of particles from mask is :{}'.format(len(region_labels)))
	
	Name = imp.title
	path = sipmm_inputFile.getAbsolutePath()
	parent = sipmm_inputFile.getParentFile().getName()
	Rarea = countTrue(red_mask)
	Garea = countTrue(green_mask)
	Rmean = ops.stats().mean(Regions.sample(Regions.iterable(red_mask),red_mip))
	GQarea = countTrue(green_mask_new)
	GQmean = ops.stats().mean(Regions.sample(Regions.iterable(green_mask_new),green_mip))
	GQintden = ops.stats().sum(Regions.sample(Regions.iterable(green_mask_new),green_mip))
	GQstd = ops.stats().stdDev(Regions.sample(Regions.iterable(green_mask_new),green_mip))
	RMregions= len(region_labels)

	h = 'Name,path,Rarea,Rmean,Rstd,Garea,Gmean,Gstd,GQarea,GQmean,GQintden,GQstd,nPunctae,RMregions,maxxxxx'
	s = str([Name,path,Rarea,Rmean,Rstd,Garea,Gmean,Gstd,GQarea,GQmean,GQintden,GQstd,nPunctae,RMregions,maxxxxp, extravar])
	
	#outfile = os.path.join(outdir,'{}_{}_results.csv'.format(path.replace('\\','__').replace('/','__').replace(':','_'),Name))
	# outfile = os.path.join(outdir,'{}_{}_results.csv'.format(parent,Name))

	log("Writing to : "+outfile)
	log("content : "+s)
	with open(outfile,'a') as of:
		of.write(s+'\n')

if debugging:
	IJ.run("Tile")
