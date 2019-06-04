#@ File inputFile(label='Input File (can contain multiple series')
#@ File psfFile(label='File that contains the PSF')
#@ Integer numIterations(value=30, label = 'Number of iterations')
#@ Boolean combinedChannels
#@ File(style="directory") outputDirectory

#@ OpService ops
#@ UIService ui

# TODO: support Time series

import os
from ij import IJ, ImagePlus, ImageStack
from ij.plugin import ChannelSplitter, HyperStackConverter
from net.imglib2.img.display.imagej import ImageJFunctions
from java.lang import System
from net.imglib2 import FinalDimensions
from loci.plugins.in import ImporterOptions
from loci.plugins import BF

def run():
	imgPath = inputFile.getAbsolutePath()
	psfPath = psfFile.getAbsolutePath()
	
	from loci.plugins import BF
	
	imgPs, psfP = [ bfopenall(im) for im in [imgPath, psfPath] ]

	log('Found {} images in {}'.format(len(imgPs),imgPath))
	
	for seriesNumber, imgP in enumerate(imgPs):
		decon(seriesNumber, imgP, psfP[0])
	
# --- Deconvolve image with psf
def decon(seriesNumber, imgP, psfP):	
	nChannels = imgP.getNChannels()	
	
	if nChannels>1:
		imgPc = ChannelSplitter.split(imgP)
	else:
		imgPc = [imgP]
	
	if psfP.getNChannels()>1:
		psfPc = ChannelSplitter.split(psfP)

		if len(psfPc)<nChannels:
			log("PSF image has fewer channels! Skipping image's trailing channels {} to {}".format(psfP.getNChannels()+1,nChannels))
			imgPc = imgPc[:psfP.getNChannels()]
	else:
		psfPc = [psfP]*nChannels
		
	nChannels = len(imgPc)
	if combinedChannels:
		deconChannels = None
		
	for channelNumber in range(nChannels):
		log("Processing image {} series {} channel {}..".format(inputFile.getAbsolutePath(),seriesNumber,channelNumber))
	
		imgP = imgPc[channelNumber]
		psfP = psfPc[channelNumber]
		
		img = ImageJFunctions.wrap(imgP)
		psf = ImageJFunctions.wrap(psfP)
		
		# convert to float (TODO: make sure deconvolution op works on other types)
		imgF=ops.convert().float32(img)
		psfF=ops.convert().float32(psf)
		
		# make psf same size as image
		psfSize=FinalDimensions([img.dimension(0), img.dimension(1), img.dimension(2)]);
		
		# add border in z direction
		#borderSize=[0,0,psfSize.dimension(2)/2];
		borderSize=[0,0,0];
		
		deconvolved = ops.deconvolve().richardsonLucy(imgF, psfF, numIterations);

		# Create the ImagePlus, copy scale and dimensions
		deconvolvedImp = ImageJFunctions.wrapFloat(deconvolved,inputFile.getName()+'-series{}-channel{}-deconvolvedWith-{}-{}iterations.tiff'.format(seriesNumber,channelNumber,psfFile.getName(),numIterations))
		deconvolvedImp.copyScale(imgP)
		width, height, nChannelz, nSlices, nFrames = imgP.getDimensions()
		deconvolvedImp.setDimensions(nChannelz, nSlices, nFrames)

		if combinedChannels:
			if deconChannels is None:
				deconChannels = ImageStack(width,height)
			
			for z in range(nSlices):
				deconChannels.addSlice(deconvolvedImp.getStack().getProcessor(z))
		else:
			IJ.saveAsTiff(deconvolvedImp,os.path.join(outputDirectory.getAbsolutePath(),deconvolvedImp.getTitle()))
	
	if combinedChannels:
		final = ImageStack(width,height)
		for z in range(nSlices):
			for c in range(nChannels):
				i = c*nSlices+z
				final.addSlice(deconChannels.getProcessor(i+1))
				
		hyperstack = ImagePlus(inputFile.getName()+'-series{}-deconvolvedWith-{}-{}iterations.tiff'.format(seriesNumber,psfFile.getName(),numIterations),final)
		hyperstack = HyperStackConverter.toHyperStack(hyperstack,nChannels,nSlices,1)
		hyperstack.copyScale(imgP)
		IJ.saveAsTiff(hyperstack,os.path.join(outputDirectory.getAbsolutePath(),hyperstack.getTitle()))

	

from datetime import datetime
def log(message):
	msg = "{}\t{}\n".format(datetime.now().isoformat(),message)
	with open(outputDirectory.getAbsolutePath()+"/"+inputFile.getName()+"-log.txt","a") as f:
		f.write(msg)
	print(msg)

# Convenience function to read all images from a series into memory
def bfopenall(path):
	options = ImporterOptions();
	options.setId(path);
	options.setOpenAllSeries(True);
	return BF.openImagePlus(options);
   
run()
