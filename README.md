# Reduce GEMINI GMOS Imaging Data

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

## EXAMPLE:
---------------
```
import os
import sys
import numpy as np
from astropy.io import fits
from astropy import table

import GMOS_imaging_calibration
import GMOS_photometry
import GMOS_precalibration

DATA_DIR = '../data/reduced/2017gmr/epoch1_img_obs/' # Raw observation data to be moved to REDUCE_DIR
CALIB_DIR = '../data/reduced/2017gmr/epoch1_img_calib/'  # Raw calibration data to be moved to REDUCE_DIR
REDUCE_DIR = '../data/reduced/2017gmr/epoch1' #Where data will be reduced
FIG_DIR = '../figures'

#---------------------
#PRECALIBRATION
#---------------------
GMOS_precalibration.check_download([CALIB_DIR, DATA_DIR])
GMOS_precalibration.copy_to_reduction_dir([CALIB_DIR, DATA_DIR], REDUCE_DIR)
GMOS_precalibration.unzip_files([REDUCE_DIR])
GMOS_precalibration.create_observation_database(CODE_DIR, REDUCE_DIR)

#---------------------
#CALIBRATION
#---------------------

qd = {'use_me':1,
      'Instrument':'GMOS-S',
      'CcdBin':'2 2',
      'RoI':'Full',
      'Object':'SN2017gmr%',
      'DateObs':'2018-09-02:2018-09-03' #Code will update to include at least 7 biases and flats
      }
db_file='obsLog.sqlite3'

#BIAS
GMOS_imaging_calibration.create_master_bias(qd, db_file, REDUCE_DIR,
                   master_bias='MCbias.fits', overwrite=True)
                   
#TWILIGHT FLAT
# Select flats obtained contemporaneously with the observations.

qd['DateObs']='2018-09-02:2018-09-03'  ##Code will update to include at least 7 biases and flats
GMOS_imaging_calibration.create_master_twilight_flat(qd, db_file, REDUCE_DIR, overwrite=True)

#SCIENCE IMAGES
qd['DateObs'] = '*'
GMOS_imaging_calibration.calibrate_science_images(qd, os.path.basename(db_file), REDUCE_DIR, overwrite=True)

targets = ['SN2017gmr']
GMOS_imaging_calibration.create_coadd_img(qd, targets, os.path.basename(db_file), REDUCE_DIR, prefix='mrg', overwrite=True)
```