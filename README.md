# ASIA-pipelines
ASIA analysis is designed to detect and count the number of synapses (or puncta) in virally transduced fluorescently-labeled live neurons as documented in Green et al., (TBD). The analysis is built in three software, Fiji, MetaMorph, and CellProfiler as outlined below. Images can be collected with either confocal or widefield microscopy, with widefield needing a deconvolution step in the analysis. A script for batch deconvolution of widefield images is provided for use in Fiji. After deconvolution, widefield images can be processed for puncta in Fiji, CellProfiler, or MetaMorph.  

Fiji- Two scripts are provided to run in Fiji
          
- The first script labeled "DeconExhaustivetoSingleFile" is to run batch deconvolution of widefield images
         
 - The second script labeled "PunctaAnalysis" is to analyze puncta and the cell death marker as described in Green et al., (TBD). This can be used for either deconvolved widefield images, or confocal images, though the exact parameters in the script may need to be changed (see Green et al., (TBD)). 

CellProfiler- Two pipelines are provided for CellProfiler
          
- The first pipeline labeled "MakeMIP(redandgreen)" is to create Maximum Intensity Projection (MIP) images and to save them as tif files to run in the second pipeline. It is currently set up to take .nd2 files but can be changed to accept other file types.
          
- The second pipeline called "AnalyzePunctaAndParticles" analyzes puncta and the cell death marker from the MIP images as described in Green et al., (TBD).

MetaMorph- Three files are provided to run in MetaMorph that are all used in conjunction to analyze puncta. The steps for setting up these files to run the journal are described below. 


## Installation
Clone this repository by running:

```
git clone https://github.com/thayerlab/ASIA-pipelines.git
```

You can download example datasets (here)[https://drive.google.com/drive/u/0/folders/1cvp9BJBP7wS6xC2l9PYFGajeoDADxxNp]

### FIJI 
These instructions are for the Fiji version of the pipeline.

These were tested with Fiji, version ImageJ 2.0.0-rc691/1.52n, Java 1.8.0_172 (64-bit).

  1. Download Fiji from https://fiji.sc/Download
  2. Open the script in the script editor [Key shortcut "["] and open the script "PunctaAnalysis.py" or "DeconExhaustive_toSingleFile.py", or drag the script files into Fiji.
  3. To run "DeconExhaustive_toSingleFile.py" click run and specify input files, output folders, a single PSF file, and number of iterations (we used 10). A PSF file needs to be generated corresponding to exact microscope acquisition parameters used. We used the PSF Generator plugin found at http://bigwww.epfl.ch/algorithms/psfgenerator/.
  A single PSF file should be used that contains PSF images generated for both red and green channels merged into a single tif file. The order of the channels in the PSF file should match the order of the channels in the images to be deconvolved.
  4. To run "PunctaAnalysis.py" click run and specify the input files, output folder, and min and max puncta size. Debugging can be checked to see the image outputs and to test parameters before running a large batch. Two channels should be checked if the images do not contain brightfield or a third channel, such as images generated from the "DeconExhaustive_toSingleFile.py" script. 
  - the number of puncta will be the nPunctae variable and the cell death marker will be the RMregions variable.

### CellProfiler

These were tested with CellProfiler, version 3.1.5

  1. Download CellProfiler from https://cellprofiler.org/releases/
  2. Open the pipeline to use: either "MakeMIP(redandgreen).cpproj" or "AnalyzePunctaAndParticles.cpproj"
  3. Drag files to the "Images" step and make sure MetaData and NamesAndTypes steps work with file format. 
  4. Can run test mode on single images before running large batch to make sure settings are appropriate
  5. Specify Output folders
  6. Run files

### MetaMorph

These were tested with MetaMorph version 7.10.0.119

  1. Create folder on Desktop that will contain the input and output images
  2. In MetaMorph, edit the journal "Loop-for-JOBS_Puncta-Sizes.JNL"
         
- Under "Loop for all Images in Directory" make sure to input appropriate Directory path for input images location
          
- Under "Loop for all Images in Directory" select "Puncta-Count-for-JOBS" as journal
          
- Make sure the "Integrated Morphometry- Load State" step is calling the "IMA_File.IMA"
  
  3. Run journal
