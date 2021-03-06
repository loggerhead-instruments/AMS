#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 16:44:41 2018

@author: dmann
"""

import matplotlib.pyplot as plt
import numpy as np
#import scipy.io.wavfile as wav
import soundfile as sf
import scipy.signal as signal
import glob, os
import csv

#path = '/Users/dmann/w/AMS/python/testSignals/'
#path = '/Users/dmann/w/AMS/python/testSignals/echolocation/'
path = '/Users/dmann/Desktop/2017-11/'
#fileName = '2017-11-02T214500_0004e9e500057249_2.0.wav'
#fileName = 'whistleTest.wav'
#Fs, y = wav.read(path + fileName)

### Settings that can be tweaked to change sensitivity

# frequency resolution
fftPts = 256


# frequency range to look for peak
startFreq = 5000
endFreq = 22000

# adjacent bins need to be within x Hz of each other to add to runLength
whistleDelta = 1500.0 # default = 500

# minimum run length to count as whistle
minRunLength = 150.0  # default = 300

# candidate whistle must cover this number of bins
fmThreshold = 500.0 # default = 1000

### End user settings


# run through all files
os.chdir(path)
for fileName in glob.glob('*.wav'):
    print(fileName)
    try:
        #Fs, y = wav.read(path + fileName)
        y, Fs = sf.read(path + fileName)
    except ValueError as e:
        print(e)
        continue
    
    binWidth = Fs / fftPts
    fftDurationMs = 1000.0 / binWidth

    startBin = int(startFreq/binWidth)
    endBin = int(endFreq/binWidth)
    # step through chunks
    index = 0
    peaks = []
    toneIndex = []
    runLength = 0
    whistleCount = 0
    maxPeakFreq = 0
    minPeakFreq = endFreq
    whistles = []
    whistleIndex = []
    rlIndex = []
    rlPoints = []
    highFreqAvg = [] # for echolocation band
    lowFreqAvg = []  # echolocation reference band
    echoIndex = []
    oldPeakFrequency = 0
    
    # no overlap of FFTs
    for start in range(0, len(y)-fftPts, fftPts):
        chunk = y[start:start+fftPts] * np.hanning(len(y[start:start+fftPts]))
        Y = abs(np.fft.fft(chunk)) / fftPts # fft and normalization
        peakFrequency = (Y[startBin:endBin].argmax() + startBin) * binWidth
        peakAmplitude = Y[Y[startBin:endBin].argmax() + startBin]
        refAmplitude = Y[Y[startBin:endBin].argmax() + startBin - 12 : Y[startBin:endBin].argmax() + startBin - 2].max()
        highFreqAvg.append(Y[startBin:endBin].mean())
        lowFreqAvg.append(Y[10:startBin].mean())
        echoIndex.append(Y[startBin:endBin].mean()/Y[10:startBin].mean())
        
        peaks.append(peakFrequency)
        toneIndex.append(peakAmplitude/refAmplitude)
        if(peakFrequency > maxPeakFreq):
            maxPeakFreq = peakFrequency
        if(peakFrequency < minPeakFreq):
            minPeakFreq = peakFrequency
        if(abs(peakFrequency - oldPeakFrequency) < whistleDelta):
            runLength+=1
        else:
            # end of run
            if((runLength>minRunLength) &
                (maxPeakFreq - minPeakFreq > fmThreshold)):
                # store detected whistles
                whistleCount += 1
                whistles.append(peakFrequency)
                whistleIndex.append(index * (fftPts/Fs))
            # store run lengths
            rlIndex.append(index * (fftPts/Fs))
            rlPoints.append(runLength * fftDurationMs)
            maxPeakFreq = 0
            minPeakFreq = endFreq
            runLength = 0
    
        oldPeakFrequency = peakFrequency
        index = index + 1
    
    
#    print(whistles)
#    
    plt.plot(whistles, np.zeros(len(whistles)), 'bo')
    plt.subplot(3,1,2)
    plt.plot(echoIndex)
    plt.subplot(3,1,3)
    plt.plot(toneIndex, '.')
    plt.subplot(3, 1, 1)
    plt.specgram(y, NFFT=fftPts, Fs=Fs, noverlap=0, cmap=plt.cm.gist_heat)
    plt.show()
    #plt.pause(1)
    
    whistleBinCount = np.count_nonzero(np.greater(toneIndex, 10));
    N = 5
    smoothed = np.convolve(toneIndex, np.ones((N,))/N, mode='valid')
    whistleBinCountSmoothed = np.count_nonzero(np.greater(smoothed, 10));
    
    print(np.mean(toneIndex))
    print(np.std(toneIndex))
    print(np.max(toneIndex))
    print(whistleBinCount)

    #wait = input("PRESS ENTER TO CONTINUE.")
    
    #plt.close()
    
    # write to file
    f = open('whistlesRefMaxAmp.csv', 'a')     
    f.write('%s' % fileName)
    f.write(',')
    f.write('%f'% np.mean(toneIndex))
    f.write(',')
    f.write('%f'% np.std(toneIndex))
    f.write(',')
    f.write('%f'% np.max(toneIndex))
    f.write(',')
    f.write('%d'% whistleBinCount)
    f.write(',')
    f.write('%f'% np.mean(smoothed))
    f.write(',')
    f.write('%f'% np.std(smoothed))
    f.write(',')
    f.write('%f'% np.max(smoothed))
    f.write(',')
    f.write('%d'% whistleBinCountSmoothed)
    f.write('\n')
    f.close()