# Bilinear coupling veto (bcv) module
# this module contains functions to read, write and process data obtained from the 
# detector channel and auxilary channels.
# The functions are called by the main script (vetoanalysis.py) to process this data
# based on inputs received by the Event Trigger Generator (ETG) Algorithms

# 

#from pylal import Fr
import sys
import scipy.signal as sig
import numpy as np
import scipy.linalg as linalg
import scipy.interpolate as sinterp
import os
#from gwpy.timeseries import TimeSeries as TS
#from pycbc.frame import frame
import lalframe.frread as fr
class FrameCacheStruct:
  def __init__(self, sites, frameTypes, startTimes, stopTimes, durations, directories ):
    self.sites = sites
    self.frameTypes = frameTypes
    self.startTimes = startTimes
    self.stopTimes  = stopTimes
    self.durations  = durations
    self.directories = directories


def getPSD(data, fs, seglen, overlap):
  # print 'nperseg= ', seglen*fs
  # print 'noverlap = ', overlap*fs 
   f, psd= sig.welch(data, fs=fs, nperseg=seglen*fs, noverlap=overlap*fs)
   return psd

def whiten(data, psd):
  window = sig.get_window('hann', len(data))
  dataf = np.fft.rfft(sig.detrend(data)*window)
  if(len(dataf)!=len(psd)):
    print 'Length of data and psd do not match'
  return np.fft.irfft(dataf/np.sqrt(psd))

def readData(frameCache, channelNames,frameTypes, startTime, stopTime, timeShifts, debugLevel):
  numberOfChannels = len(channelNames)
  if(len(frameTypes)!=numberOfChannels):
    print channelNames, frameTypes
    sys.exit('Number of frame types is inconsistent with number of channels')
  
  # This function reads data from the file frameCache which contains data in channelName
  
  # Permit redundant data
  allowRedundantFlag = True
  # Initializing timeShifts if they are null
  if(len(timeShifts)==0):
    timeShifts = np.zeros(len(numberOfChannels))

  if(len(timeShifts)!=numberOfChannels):
    sys.exit('Number of time shifts inconsistent with number of channels')
  # Making sure stop time greater than start time
  if(stopTime<startTime):
    stopTime = startTime + stopTime
  data = []
  samplFreq = []
  
  #Reading data for all channels one by one and storing them in vectors
  for channelNumber in xrange(numberOfChannels):
    # The function frgetvect is from the python implementation of LALSuite and returns
    # the following
    # frame[0] is an array containing the strains
    # frame[1] is the end time of the data
    # frame[3] is the inverse of the Sampling Frequency
    mData, mSamplFreq = readframedata(frameCache, channelNames[channelNumber],
				       frameTypes[channelNumber], startTime - timeShifts[channelNumber], stopTime - timeShifts[channelNumber],
				       allowRedundantFlag, debugLevel)
    data.append(mData)
    samplFreq.append(mSamplFreq)
  data = np.asarray(data)
  samplFreq = np.asarray(samplFreq)
  return [data, samplFreq]




def resample2(data, samplFreqD, samplFreq):
  totalTime = len(data)/samplFreqD
  new_num = int(totalTime*samplFreq)
  dataInter = sig.resample(data, new_num)
  return dataInter

def linearCouplingCoeff(dataH, dataX, timeH, timeX, transFnXtoH, segStartTime,
			segEndTime, timeShift, samplFreq, logFid, debugLevel):
  # LINEARCOUPLINGCOEFF - calculate the cross correlation coeff b/w the gravitational
  # ave channel H and the "projected" instrumental channel X. The noise in the
  # instrumental channel X is projected to the domain of the H using a linear coupling
  # function Txh

  MIN_FREQ = 0.1
  MAX_FREQ = 4000.0  
  IFO_LENGTH = 4000
  rXH = np.asarray([])
  rMaxXH = np.asarray([])
  if((len(dataH)==0) | (len(dataX)==0)):
    logFid.write('Error: One or more data vectors are empty..\n')
    logFid.write('Error: len(dataH) = %d len(dataX) = %d..\n' %(len(dataH), len(dataX[0])))
  
  elif(len(dataH)!=len(dataX[0])):
    logFid.write('Error: Different lengths. len(dataH) = %d len(dataX) = %d..\n'%(len(dataH), len(dataX[0])))
  else:
    dataH = dataH - np.mean(dataH)
    dataX = dataX[0] - np.mean(dataX[0])
    
    segIdxH = np.intersect1d(np.where(timeH>=segStartTime)[0], np.where(timeH<segEndTime)[0])
    dataH = dataH[segIdxH]
    
    segIdxX = np.intersect1d(np.where(timeX + timeShift >= segStartTime)[0], np.where(timeX + timeShift < segEndTime)[0])
    dataX = dataX[segIdxX]
    
    nfft = len(dataH)
    
    freqVecH = np.fft.rfftfreq(nfft, 1.0/samplFreq)
    fftChanH = np.fft.rfft(dataH)
    
    nfft = len(dataX)
    freqVecX = np.fft.rfftfreq(nfft, 1.0/samplFreq)
    fftChanX = np.fft.rfft(dataX)
    
    freqBandIdx = np.intersect1d(np.where(transFnXtoH.frequency>MIN_FREQ)[0], np.where(transFnXtoH.frequency <MAX_FREQ)[0])
    if(len(freqBandIdx)!=0):
      transFnXtoH.frequency = transFnXtoH.frequency[freqBandIdx]
      transFnXtoH.Txh = transFnXtoH.Txh[freqBandIdx]
    
    TxhFreqMin = np.min(transFnXtoH.frequency)
    TxhFreqMax = np.max(transFnXtoH.frequency)
    
    
    #if(len(freqBandIdx)!=0):
      #transFnXtoH.frequency = transFnXtoH.frequency[freqBandIdx]
      #transFnXtoH.Txh = transFnXtoH.Txh[freqBandIdx]
    if(len(freqVecH)!=len(freqVecX)):
      logFid.write('ERROR: Unequal size for freq. vectors.\n')
      logFid.write('ERROR: len(freqVecH) = %d len(freqVecX) = %d.\n' %(length(freqVecH), length(freqVecX)))
    else:
      freqBandIdx = np.intersect1d(np.where(freqVecH>=TxhFreqMin)[0], np.where(freqVecH <= TxhFreqMax)[0])
      if(len(freqBandIdx)!=0):
	fftChanH = fftChanH[freqBandIdx]
	fftChanX = fftChanX[freqBandIdx]
	freqVecH = freqVecH[freqBandIdx]
	freqVecX = freqVecX[freqBandIdx]
      
      
      freqResolTxh = np.float(samplFreq)/len(dataX)
      
      [tFreqIntp, tfMagIntp,tfPhaseIntp] = interpolatetransfn(transFnXtoH.frequency,
							     np.abs(transFnXtoH.Txh),
							     np.unwrap(np.angle(transFnXtoH.Txh)), freqResolTxh)
      TxhInterp = tfMagIntp* np.exp(1j*tfPhaseIntp)
      TxhInterp = TxhInterp[0:len(fftChanX)]
      if(len(fftChanX)==len(TxhInterp)):
	xPrime = fftChanX*TxhInterp/IFO_LENGTH
      else:
	logFid.write( 'ERROR: size(fftChanX) = %d size(TxhInterp) = %d\n' %(len(fftChanX), len(TxhInterp)))
	logFid.write('ERROR: fftChanX and TxhInterp have different sizes.\n')
	sys.exit('Inconsistent dimensions of data and transfer function')
      
      
      [a, b] = calCrossCorr(xPrime, fftChanH)
      rXH = np.append(rXH, a)
      rMaxXH = np.append(rMaxXH, b)
      return [rXH, rMaxXH]
    
    
  
  
def bilinearCouplingCoeff(dataH, dataP, timeH, timeP,
			  segStartTime,segEndTime, timeShift, samplFreq, logFid, debugLevel):
  # This function computes the correlation coefficient between Channel H and al
  # the pseudo channels P.
  #
  # Usage: [rPH, rPHAbs] = bilinearCouplingCoeff(dataH, dataP, timeH, timeP,
  #                               segStartTime, segEndTime, timeShift, samplFreq
  #                               logFid, debugLevel)
  # Set the frequency range of the veto analysis
  
  
  MIN_FREQ = 0.1
  MAX_FREQ = 4000.0
  
  # Meta Data
  segIdxH = np.intersect1d(np.where(timeH>=segStartTime)[0], np.where(timeH<segEndTime)[0])
  dataH = dataH[segIdxH]
  dataH = dataH - np.mean(dataH)

  
  # Set parameters for calculating spectrogram
  nfft = len(dataH)
  wind = np.ones(nfft)
  
  # Calculate spectrogram
  freqVecH = np.fft.rfftfreq(nfft, 1.0/samplFreq)
  fftChanH = np.fft.rfft(dataH)


  [numChanP, lengthP] = np.shape(dataP)
  segIdxP = np.intersect1d(np.where(timeP + timeShift >= segStartTime)[0], np.where(timeP + timeShift < segEndTime)[0])
  rPH = np.asarray([])
  rPHAbs = np.asarray([])
  
  for iChan in xrange(numChanP):
    dataVecP = dataP[iChan]
    dataVecP = dataVecP[segIdxP]
    dataVecP = dataVecP - np.mean(dataVecP)
    
    freqVecP = np.fft.rfftfreq(nfft, 1.0/samplFreq)
    fftChanP = np.fft.rfft(dataVecP)
    
    # Make sure the fft vectors are of the same size
    if(len(freqVecP)!=len(freqVecH)):
      logFid.write('ERROR: Unequal size of freq. vectors. \n')
      logFid.write('ERROR: len(freqVecH) = %d len(freqVecP) = %d\n', len(freqVecH), len(freqVecP))
      return
    else:
      #Select the frequency band
      freqBandIdx = np.intersect1d(np.where(freqVecH>MIN_FREQ)[0], np.where(freqVecP < MAX_FREQ)[0])
      
      # Calculate the cross-correlation statistic for the segment of data in channels h
      # and "projected" P
      [a, b] = calCrossCorr(fftChanP[freqBandIdx], fftChanH[freqBandIdx])
      rPH = np.append(rPH, a)
      rPHAbs = np.append(rPHAbs, b)
  
  return [rPH, rPHAbs]

def linearCouplingCoeff2(dataH, dataX, timeH, timeX, transFnXtoH, segStartTime,
			segEndTime, timeShift, samplFreq, logFid, debugLevel):
  # LINEARCOUPLINGCOEFF - calculate the cross correlation coeff b/w the gravitational
  # ave channel H and the "projected" instrumental channel X. The noise in the
  # instrumental channel X is projected to the domain of the H using a linear coupling
  # function Txh


  rXH = np.asarray([])
  rMaxXH = np.asarray([])
  if((len(dataH)==0) | (len(dataX)==0)):
    logFid.write('Error: One or more data vectors are empty..\n')
    logFid.write('Error: len(dataH) = %d len(dataX) = %d..\n' %(len(dataH), len(dataX[0])))
  
  elif(len(dataH)!=len(dataX[0])):
    logFid.write('Error: Different lengths. len(dataH) = %d len(dataX) = %d..\n'%(len(dataH), len(dataX[0])))
  else:
    dataH = dataH #- np.mean(dataH)
    dataX = dataX[0] #- np.mean(dataX[0])
    
    segIdxH = np.intersect1d(np.where(timeH>=segStartTime)[0], np.where(timeH<segEndTime)[0])
    dataH = dataH[segIdxH]
    
    segIdxX = np.intersect1d(np.where(timeX + timeShift >= segStartTime)[0], np.where(timeX + timeShift < segEndTime)[0])
    dataX = dataX[segIdxX]
    
    
    
    a = np.correlate(dataH, dataX)/(np.sqrt(np.correlate(dataH, dataH)*np.correlate(dataX, dataX)))
    rXH = np.append(rXH, a)
    rMaxXH = np.append(rMaxXH, a)
    return [rXH, rMaxXH]  



def bilinearCouplingCoeff2(dataH, dataP, timeH, timeP,
			  segStartTime,segEndTime, timeShift, samplFreq, logFid, debugLevel):
  # This function computes the correlation coefficient between Channel H and al
  # the pseudo channels P.
  #
  # Usage: [rPH, rPHAbs] = bilinearCouplingCoeff(dataH, dataP, timeH, timeP,
  #                               segStartTime, segEndTime, timeShift, samplFreq
  #                               logFid, debugLevel)
  # Set the frequency range of the veto analysis
  
  
  
  # Meta Data
  segIdxH = np.intersect1d(np.where(timeH>=segStartTime)[0], np.where(timeH<segEndTime)[0])
  dataH = dataH[segIdxH]
  #dataH = dataH - np.mean(dataH)

  
  [numChanP, lengthP] = np.shape(dataP)
  segIdxP = np.intersect1d(np.where(timeP + timeShift >= segStartTime)[0], np.where(timeP + timeShift < segEndTime)[0])
  rPH = np.asarray([])
  rPHAbs = np.asarray([])
  
  for iChan in xrange(numChanP):
    dataVecP = dataP[iChan]
    dataVecP = dataVecP[segIdxP]
    #dataVecP = dataVecP - np.mean(dataVecP)
    
    # Make sure the fft vectors are of the same size
    if(len(dataVecP)!=len(dataH)):
      logFid.write('ERROR: Unequal size of data. vectors. \n')
      logFid.write('ERROR: len(dataVecP) = %d len(dataH) = %d\n', len(dataVecP), len(dataH))
      return
    else:
      a = np.correlate(dataH, dataX)/(np.sqrt(np.correlate(dataH, dataH)*np.correlate(dataX, dataX)))
      rPH = np.append(rPH, a)
      rPHAbs = np.append(rPHAbs, a)
  
  return [rPH, rPHAbs]


def interpolatetransfn(tfFreq, tfMag, tfPhase, reqFreqRes):
  
  # Compute the required frequency resolution.
  tfFRes = tfFreq[1] - tfFreq[0]
  
  # Create a new frequency vector for interpolating the transfer function.
  newFreqVec = np.arange(np.min(tfFreq), np.max(tfFreq)+ reqFreqRes, reqFreqRes)
  #Use the resample command for interpolating the transfer function.
  #tfFreqIntp  = newFreqVec
  #tfMagIntp   = resample(tfMag,tfFRes,reqFreqRes)
  #tfPhaseIntp = resample(tfPhase,tfFRes,reqFreqRes)
  tck = sinterp.splrep(tfFreq, tfFreq, s=0)
  tfFreqIntp = sinterp.splev(newFreqVec, tck, der=0)
  
  tck = sinterp.splrep(tfFreq, tfMag, s=0)
  tfMagIntp = sinterp.splev(newFreqVec, tck, der=0)
  
  tck = sinterp.splrep(tfFreq, tfPhase, s=0)
  tfPhaseIntp = sinterp.splev(newFreqVec, tck, der=0)
  
  return [tfFreqIntp, tfMagIntp,tfPhaseIntp]
  

def calCrossCorr(u,v):
  # Auxlilary function which calculates the cros correlation between two signals
  # The inputs are the spectrograms of the two signals
  if(u.shape!=v.shape):
    sys.exit('Size of u and v mist be the same\n')
      
  uDotu = np.sum(u*np.conj(u))
  vDotv = np.sum(v*np.conj(v))
  uConjv = u*np.conj(v)/(np.sqrt(uDotu)*np.sqrt(vDotv))
  r = np.real(np.sum(uConjv))
  
  xCorr = np.fft.irfft(uConjv)*len(u)
  rMax = np.max(np.real(xCorr))
  rMin = np.min(np.real(xCorr))
  
  rAbs = rMax
  if(np.abs(rMin)>np.abs(rMin)):
    rAbs = np.abs(rMin)
  return [r, rAbs]

def highpass(rawData, samplFreq, highpassCutOff):
  #This function high passes the data with sampling frequency samplFreq with a highpass
  # cut off of highpassCutOff
  #
  # Usage: [highPassedData] = highpass(rawData, samplFreq, highpassCutOff)
  # 
  # rawData : raw time series Data
  # samplFreq: sampling Frequency of Data
  # highpassCutOff: The high pass frequency cut off.
  #
  numberOfChannels = len(rawData)
  dataLength = len(rawData[0])
  duration = dataLength/samplFreq
  
  
  halfDataLength = dataLength/2 + 1
  
  for channelNumber in xrange(numberOfChannels):
    if(len(rawData[channelNumber]) != dataLength):
      sys.exit('Data length not consistent\n')
  
  nyquistFrequency = samplFreq/2.0
  
  lpefOrder  = 0
  
  if(highpassCutOff>0):
    hpfOrder = 12
    hpfZeros, hpfPoles, hpfGain = sig.butter(hpfOrder, highpassCutOff/nyquistFrequency, btype = 'highpass', output = 'zpk' )
    hpfSOS = sig.zpk2sos(hpfZeros, hpfPoles, hpfGain)
    
    #magnitude response of high pass filter
    minimumFrequencyStep = 1.0/duration
    frequencies = np.arange(0, nyquistFrequency, minimumFrequencyStep)
    hpfArgument = np.power((frequencies / highpassCutOff), 2*hpfOrder)
    hpfResponse = hpfArgument/(1 + hpfArgument)
    
    highPassCutOffIndex = np.ceil(highpassCutOff/minimumFrequencyStep)
  
  highPassedData = []
  for channelNumber in xrange(numberOfChannels):
    if(highpassCutOff>0):
      x = sig.sosfilt(hpfSOS, rawData[channelNumber])
      x = np.flipud(x)
      x = sig.sosfilt(hpfSOS, x)
      x = np.flipud(x)
    else:
      x = rawData[channelNumber]
    
    x[0:lpefOrder] = np.zeros(lpefOrder)
    x[dataLength - lpefOrder:dataLength-1] = np.zeros(lpefOrder)
    
    highPassedData.append(x)
  
  highPassedData = np.asarray(highPassedData)
  
  return highPassedData
  


def loadframecache(cachePath):
  #loadframecache loads frame file cache information
  
  #This function reads the lal/frame file cache information stored in the 
  #specified file. The resulting cache structure is used to locate frame data
  #during subsequent calls to readframedata
  
  #usage: cache = loadframecache(cachePath)
  
  #cachePath: path to lal/frame cachef file
  #cache: lal/frame cache structure
  
  #formats:
    
  #FRAMECACHE: The frame cache file should consist of whitespace delimited ASCII
  #text and contains one line for each contiguous data segment with a common site, frame
  #type, duration and directory. Each line should consist of the following six columns
  
    #* site designator (e.g 'H' or 'L')
    #* frame file type (e.g 'RDS_R_L3')
    #* GPS start time of segment
    #* GPS stop time of segment
    #* frame file duration in seconds
    #* full path name of directory
  #The resulting cache frame structure consists of the following six fields.
  
    #* .sites              numpy array of segment site designators
    #* .frameTypes         numpy array of segment frame file frameTypes
    #* .startTimes         numpy array of segment GPS start times
    #* .stopTimes          numpy array of segment GPS stop times
    #* .durations          numpy array of segment frame file durations
    #* .directories        numpy array of segment directory names
    
  sites     = np.genfromtxt(cachePath,delimiter=' ',usecols=(0), dtype=None,unpack=True)
  frameTypes = np.genfromtxt(cachePath,delimiter=' ',usecols=(1), dtype=None,unpack=True)
  startTimes = np.genfromtxt(cachePath,delimiter=' ',usecols=(2), dtype=None,unpack=True)
  stopTimes = np.genfromtxt(cachePath,delimiter=' ',usecols=(3), dtype=None,unpack=True)
  durations = np.genfromtxt(cachePath,delimiter=' ',usecols=(4), dtype=None,unpack=True)
  directories =np.genfromtxt(cachePath,delimiter=' ',usecols=(5), dtype=None,unpack=True)
  
  cache = FrameCacheStruct(sites, frameTypes, startTimes, stopTimes,durations, directories)
  
  return cache
  
# Function to check if the file exists AND is non-empty
def is_non_zero_file(fpath):
    return True if os.path.isfile(fpath) and os.path.getsize(fpath) > 0 else False

def  readframedata(frameCache, channelName, frameType, startTime, stopTime,
		   allowRedundantFlag, debugLevel):
  #READFRAMEDATA Read a single channel of data from frame files
  #
  #READFRAMEDATA finds and retrieves the requested time series data from a
  #set of frame files.  The data is specified by the frame file type,
  #channel name, start time, and duration or stop time.  The necessary frame
  #files are located using a file name caching scheme.
  #%
  #usage: [data, sampleFrequency, time] = ...
  #readframedata(frameCache, channelName, frameType, ...
  #startTime, stopTime, allowRedundantFlag, ...
  #debugLevel);
  #%
  #frameCache           file name cache
  #channelName          channel name
  #frameType            frame file type
  #startTime            GPS start time
  #stopTime             GPS stop time (or duration)
  #allowRedundantFlag   permit redundant frame data
  #debugLevel           verboseness of debug output
  #%
  #data                 data vector
  #sampleFrequency      sample frequency [Hz]
  #time                 time vector
  #%
  #READFRAMEDATA expects frame cache information in the format produced by
  #LOADFRAMECACHE which contains the site, frame type, duration, time, and
  #location of available frame data files.
  #%
  #The requested site designator is determined from the first character of
  #the requested channel name.  The frame file type may contain wildcards.
  #Unless redundant frame data is permitted, it is an error if the same
  #frame file appears more than once in the frame cache file.  If redundant
  #frame data is permitted, the first matching frame file from the cache is
  #used.  It is always an error if two frame files overlap but do not cover
  #the same time range or differ in type.  By default, redundant frame data
  #is permitted.
  #%
  #READFRAMEDATA retrieves data from the requested start time up to, but not
  #including, the requested stop time, such that stop minus start seconds
  #are retrieved.  Alternatively, the desired duration in seconds may be
  #specified instead of the GPS stop time parameter.
  #%
  #The resulting time series is returned as two row vectors containing the
  #data sequence and the corresponding GPS timestamps, as well as the scalar
  #sample frequency.  To protect against roundoff error, an integer sample
  #frequency is assumed.
  #%
  #If it is unable to load the requested data, READFRAMEDATA returns empty
  #result vectors and zero sample frequency as well as a warning if
  #debugLevel is set to 1 or higher.  By default, a debugLevel of unity is
  #assumed.
  #%
  #READFRAMEDATA is built on top of the FRGETVECT function from the FrameL
  #library, which is available from the following URL.
  #%
  #
  #%
  #
  #
  #Shourov K. Chatterji <shourov@ligo.mit.edu>
  #Jameson Rollins <jrollins@phys.columbia.edu>
  #
  #$Id: readframedata.m 2326 2009-09-21 08:37:42Z jrollins $
  #
  # Rewritten in Python by Sudarshan Ghonge <sudu.ghonge@gmail.com>
  # 2015-09-04
  # 
  # Update 217-11-30 Ported to gwpy. The pipeline now uses lal-cache and 
  # now does away with the need of the functions loadframecache

  #
  # if specified stop time precedes start time,
  if(stopTime<startTime):
    # treat stop time as a duration
    stopTime = startTime + stopTime
  
  # determine site designator from channel name
  site = channelName[0]
  
  #if specified frame cache is invalid
  if(not is_non_zero_file(frameCache)):
    if(debugLevel>=1):
      # Issue warning
      print 'Warning: Empty lal cache file ' + frameCache 
    
    data = []
    time = []
    sampleFrequency = 0
    return [data, sampleFrequency]
    # return empty results
  data = np.array([])
  time = np.array([])
  sampleFrequency = None

  try:
     #outputStruct  = TS.read(frameCache, channelName, start=startTime, end=stopTime, format='gwf.lalframe')
     #outputStruct = frame.read_frame(frameCache, channelName, start_time=startTime, end_time=stopTime, check_integrity=False)
     outputStruct = fr.read_timeseries(frameCache, channelName, start=startTime, duration = stopTime-startTime)
     readData = np.array(outputStruct.data.data)
     readSampleFrequency = 1/outputStruct.deltaT
  except Exception as inst:
     readData=[]
     if(debugLevel>=1):
       print  inst.message
  if((len(readData)==0) | np.any(np.isnan(readData))):
    if(debugLevel>=1):
      print 'Warning: Error reading %s from %s.' %(channelName, frameCache)
    data = []
    time = []
    sampleFrequency = 0
    return [data, sampleFrequency]
  if(sampleFrequency==None):
    sampleFrequency = readSampleFrequency
  elif(sampleFrequency!=readSampleFrequency):
    if(debugLevel>=1):
      print 'Warning: Inconsistent sample frequency for %s in frameCache.' %(channelname, frameCache)
    data = []
    time = []
    sampleFrequency = 0
    return [data, sampleFrequency]

  data = np.append(data, readData)

  return [data, sampleFrequency]

    
  
# Python module which contains the following functions
# mcoinc, mhighpass mSpecgram

def mcoinc(maxCoinc, A, B, P, seglen, *args):
  # This function looks for coincident triggers b/w X and H channels
  # Assumes first row of A and B are time vectors
  # The matrices are then split in to submatrices of length seglen for processing.
  # This results in large speed
  # usage : [aidx, bidx] = mcoinc(maxcoinc, A, B, P, seglen)
  
  # A - Vector containing the central time co-ordinates of the triggers in H channel
  # B - Vector containing the central time co-ordinates of the triggers in X channel
  # P - Scalar describing the coincidence time window vector
  #
  # Example
  #
  # [hldx, xldx] = mcoinc(maxcoinc, hTimeVec, xTimeVec, timeWind, 3600, 'nonunique')
  #
  # In the above example, xTimeVec(xldx) will give the triggers in X that are coincident with the triggers in H.
  # timeWind is the time window usually, 0.5 seconds
  # maxCoinc is the max no of coincidences that are allowed (usually for logistical reasons)
  # such as memory limitations
  # If there are no such limitions, set it to 
  # maxCoinc = max(length(xTimeVec, length(hTimeVec)))
  #
  # Sudarshan Ghonge <sudu.ghonge@gmail.com>
  # Based on code written by
  # M. Hewitson
  # Aaron B. Pearlman <aaronpl@umbc.edu>
  # P. Ajith
  
  
  
  # Find the minimum of time contained in the first row of the matrices A and B
  t0 = np.int(np.floor(min(np.min(A), np.min(B) ) ))
  # Find the max of time contained in the first row of the matrices A and B
  tmax = np.int(np.round(max(np.max(A), np.max(B))))
  if(t0==tmax):
    tmax = t0+seglen
  
  # Initialize the output row vectors that will indicate coincident trigger
  # columns b/w matrices A and B
  c1 = np.empty([0, 1], dtype=int)
  c2 = np.empty([0, 1], dtype=int)
  
  # Uniqueness argument defaulted to False
  nu = False
  
  if(len(args)>0):
    if(args[0]=='nonunique'):
      nu = True
    elif(args[0]=='unique'):
      nu = False
    else:
      sys.exit('Invalid option for variable argument in mocoinc(maxCoinc, A, B, P, seglen, *args)')
  
  for ts in xrange(t0, tmax, seglen):
    
    # get the index of this segment of the A matrix
    idxa = np.intersect1d(np.where(A >= ts)[0], np.where(A < ts + seglen)[0])
    ATemp = A[idxa]
    # get the index for this segment of the B matrix
    idxb = np.intersect1d(np.where(B >= ts)[0], np.where(B< ts + seglen)[0])
    BTemp = B[idxb]
    
    # Use the mfindcoinc function to identify coincident trigger columns
    # between matrices ATemp and BTemp
    [C1, C2] = mfindcoinc(maxCoinc, ATemp, BTemp, P)
    
    if(len(C1)>0):
      if nu:
	c1 = np.append(c1, C1 + idxa[0])
      else:
	c1 = np.append(c1, np.unique(C1) + idxa[0])
    if(len(C1)>0):
      if nu:
	c2 = np.append(c2, C2 + idxb[0])
      else:
	c2 = np.append(c2, np.unique(C2) + idxb[0])
  
  return [c1, c2]
	
	
def mfindcoinc(maxCoinc, A, B, P):
  # Auxilary function used by mcoinc() to find co-incidences between time vectors
  # A and B which are usually segments of the larger H and X channel trigger time
  # co-ordniates
  #
  # Inputs: 
  # maxCoinc - the maximum number of co-incidences
  # A  - segment of the vector containing the time coordinates (seconds) triggers from a channel
  # B  - same as above
  # P - size of the coincidence window
  
  n=0
  cont=True
  C1 = []
  C2 = []
  # Iterate through triggers in vector A
  for j in xrange(len(B)):
    # Iterate through triggers in vector B
    for i in xrange(len(A)):
      # Check if the difference is less than the time window
      if(np.abs(A[i] - B[j]) <=P):
	# If number of triggers is more than maxCoinc, exit.
	if(n<=maxCoinc):
	  # Add those indexes to the list
	  C1.append(i)
	  C2.append(j)
	  n+=1
	else:
	  print "! Max num coincidences exceeded. Not recording further.\n"
	  cont=False
	  break
    if(cont==False):
      break
  C1 = np.asarray(C1)
  C2 = np.asarray(C2)
  return [C1, C2]
        

def roundtopowertwo(segments, roundPower):
  numRound =  np.power(2.0, np.ceil(np.log2(segments)))
  
  numRoundMin = np.power(2.0, np.ceil(np.log2(roundPower)))
  
  if(numRound < numRoundMin):
    numRound = numRoundMin
  return numRound

def printvar(*varagarin):
  for i in range(0, len(varagarin), 2):
    print "%s %s\n" %(varagarin[i], varagarin[i+1])      

      
      
      
      
      
      
      
      
    




  
  
  
