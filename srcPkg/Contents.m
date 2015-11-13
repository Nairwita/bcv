% Q Transform Toolbox
% Version 3.0 2007-Jan-21
%
% This toolbox contains the following functions for searching for transient
% events in gravitational-wave data.
%
% The following top level matlab functions and shell scripts are provided
%
% WSEARCH           Continuously search for bursts in time series data
% WSCAN             Study multiple channels during an interesting event
% WEVENT            Apply network consistency tests to an interesting event
% WTUNE             Benchmark performance for a variety of simulated signals
%
% The following top level matlab function is also provided for reference
%
% WEXAMPLE          Example application of q transform related functions
%
% The following functions comprise the code base for the Q transform.
%
% WTILE             Find time, frequency, and Q tiling for the Q transform
% WRESAMPLE         Resample time series data at a common sample frequency
% WCONDITION        High pass filter and whiten time series data
% WSCANCONDITION    Modified conditioning function for use by wscan
% WTRANSFORM        Project data onto bases of constant Q windowed sinusoids
% WTHRESHOLD        Identify statistically significant Q transform tiles
% WSELECT           Identify statistically significant non-overlapping tiles
% WCOINCIDE         Compare triggers for coincidence or vetoing
% WWRITETRIGGERS    Output Q pipeline trigger properties to a file
% WPARAMETERIZE     Estimate the signal parameters of an interesting event
%
% The following functions are provided for visulation of Q transform results
%
% WTIMESERIES       Display time series data for Q transform analysis
% WSPECTROGRAM      Display time-frequency Q transform spectrograms
% WEVENTGRAM        Display statistically significant time-frequency events
% WSKYMAP           Display likelihood and consistency maps of the sky
%
% The following functions are provided for simulating data
%
% WSIMULATENOISE    Produce simulated gravitational wave detector noise
% WSIMULATEBURST    Inject simulated gravitational wave bursts into data
%
% The following functions are provided for reading frame data
%
% WREADDATA         Read multiple channels of data from frame files
% READFRAMEDATA     Extract a single channel of data from frame files
% LOADFRAMECACHE    Load cache of frame file location information
% FRGETVECT         Extract a single channel from a single frame file
%
% The following Perl scripts are provided for use with READFRAMEDATA.
%
% CREATEFRAMECACHE  Create frame cache file for a specified directory
% CONVERTLALCACHE   Convert LAL formated frame cache to READFRAMEDATA format
%
% The following shell scripts have been provided for support.
%
% WSETUP            Sets up the necessary environment for Q transform tools
% BUILD             Compile top level functions into stand alone executables
% WCONTEXT          Query detector status and data quality for use by wscan
% WUPDATE           Update existing wscan reports with new context information
% WCONFIGURE        Automatically generate wscan configuration file
%
% The following resource files are provided.
%
% WSTYLE            Cascading style sheet for html based wscan reports
%
% The following functions are provided for one-sided frequency domain data.
%
% WFFT              One-sided Fourier transform of time domain data
% WIFFT             Inverse Fourier transform one-sided frequency domain data
%
% The following signal processing function is provided to support conditioning.
%
% SOSFILTFILT       Zero phase filtering with second-order sections
%
% Modified versions of the following Matlab toolbox functions are also
% provided.  They have been modified to permit compilation.
%
% SOSFILT           Apply IIR filter specified by second-order sections
% SOSFILTMEX        Apply IIR filter specified by second-order sections
% ZP2SOS            Convert zero-pole-gain model to second-order sections
%
% The private subdirectory contains modified copies of numerous figure
% plotting functions.  They have also been modified to permit compilation.

% Shourov K. Chatterji
% shourov@ligo.caltech.edu

% Leo C. Stein
% lstein@ligo.mit.edu

% $Id: Contents.m 656 2008-04-16 18:48:55Z jrollins $
