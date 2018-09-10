These script reduces GMOS (N and S) imaging data.

Dependencies:  
obslog.py from http://ast.noao.edu/sites/default/files/GMOS\_Cookbook/\_downloads/obslog.py   
fileSelect.py from http://ast.noao.edu/sites/default/files/GMOS\_Cookbook/\_downloads/fileSelect.py  
geminiconda must be installed: https://www.gemini.edu/node/11823  
astropy (in default anaconda package)  
photutils: conda install -c astropy photutils  

Files:  
- GMOS\_precalibration.py contains functions to check that data was downloaded correctly,
to move it into a reduction directory, to unzip the files, and to create an observation log
using the Gemini script obslog.py
- GMOS\_imaging\_calibration.py creates as Master Bias and Master flat and then uses them to 
reduce the science data. This can also be used to reduce the standard star observations.
- GMOS\_photometry.py identifies the source closest to the RA and DEC of the science image
and performs aperture photometry on it.
- GMOS\_visualization.py displays the master bias, master flat, raw, and science images for
analysis