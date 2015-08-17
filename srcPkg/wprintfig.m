function [figPath, thumbPath] = ...
    wprintfig(figureHandle,basePath,printFigs,vers)
% WPRINTFIG print a figure to a png file, with thumbnail
%
% WPRINTFIG(figureHandle, basePath, printFigs, version)
%
% If printFigs is false, this function returns immediately.
% version 0: print fig to png (requires X or Xvfb)
% version 1: print fig to eps directly (X not necessary)

%%% OMEGA FUNCTIONS EXPECT '.png' and '.thumb.png' extensions.

if (nargin < 3),
    printFigs = true;
end
if (nargin < 4),
    vers = 0;
end

% return if printFigs not set to true
if ~printFigs,
    return
end

% image and thumb sizes
figDPI = 200;
fullSize = '600x';
thumbSize = '300x';

% image paths
figPath = [basePath '.png'];
thumbPath = [basePath '.thumb.png'];

% plot version
switch vers
  case 0
    % create png, requires Xvfb
    print(figureHandle,'-dpng', ['-r' int2str(figDPI)], figPath);
  
  otherwise
    % eps path
    figEPS = [basePath '.eps'];
    figPDF = [basePath '.pdf'];

    % create eps of figure
    print(figureHandle,'-depsc2', figEPS);
	
	% convert to PDF
    system(['/usr/local/bin/convert ', figEPS, ' ', figPDF]); 

    % convert to png
    system(['convert ' ...
          '-density ' int2str(figDPI) ' -resize ' fullSize ' ' ...
          figPDF, ' ', figPath]);

    % remove the old eps file
    %system(['rm -rf ', figEPS, ' ', figPDF]);

end

% create a thumbnail
system(['/usr/local/bin/convert ' ...
      '-resize ' thumbSize ' -strip -depth 16 -colors 256 ' ...
      figPath ' ' thumbPath]);
