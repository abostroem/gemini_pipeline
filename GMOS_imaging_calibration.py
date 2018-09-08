'''
This should be run in the geminiconda environment (not IRAF)

Functional implementation of the Gemini calibration script gmos_img_proc.py
Requires the script fileSelect.py, also produced by Gemini
'''

import os
import glob

import fileSelect
from pyraf import iraf
from pyraf.iraf import gemini, gemtools, gmos

def create_master_bias(qd, rawpath, dbFile, master_bias='MCbias.fits', overwrite=True):
    if os.path.exists(master_bias):
        if overwrite is True:
            remove = raw_input('Remove bias file? (y), n ')
            if remove != 'n':
                os.remove(master_bias)
            else:
                return None
        else:
            print('Master bias, {} already exists and overwrite={}'.format(master_bias, overwrite))
            return None
    print (" --Creating Bias MasterCal--")

    SQL = fileSelect.createQuery('bias', qd)
    bias_files = fileSelect.fileListQuery(dbFile, SQL, qd)
    gmos.gbias.unlearn()
    bias_flags = {'logfile':'biasLog.txt',
                 'rawpath':rawpath,
                 'fl_vardq':'yes',
                 'verbose':'no'}
    if len(bias_files) < 10:
        print('******WARNING less than 10 bias files********')
    if len(bias_files) > 1:
        gmos.gbias(','.join(str(x) for x in bias_files), master_bias, **bias_flags)
        
    # Clean up
    if not os.path.exists(master_bias): #Check that IRAF didn't error
        sys.exit('ERROR creating Master Bias: {}'.format(master_bias))
    #Remove intermediate files
    if qd['Instrument']=='GMOS-N': 
        image_str = 'gN'
    else:
        image_str = 'gS'
    image_str = '{}{}*.fits'.format(image_str, qd['DateObs'][0:4])
    iraf.imdel(image_str)
    flist = glob.glob('tmplist*')
    for ifile in flist:
        os.remove(ifile)
        
def create_master_twilight_flat(qd, dbFile, data_dir, overwrite=True):
    '''
    despite the fact that it looks like this can be run from outside the
    raw directory, it can't be.
    '''
    cur_dir = os.getcwd()
    #os.chdir(data_dir)
    iraf.chdir(data_dir)
    print (" --Creating Twilight Imaging Flat-Field MasterCal--")
    # Set the task parameters.
    gmos.giflat.unlearn()
    flat_flags = {
        'fl_scale':'yes',
        'sctype':'mean',
        'fl_vardq':'yes',
        'rawpath':'',
        'logfile':'giflatLog.txt',
        'verbose':'no'
        }
    if qd['Instrument'] == 'GMOS-N':
        flat_flags['bpm']= 'gmos$data/gmos-n_bpm_HAM_22_12amp_v1.fits'
    else:
        flat_flags['bpm'] = 'gmos$data/gmos-s_bpm_HAM_22_12amp_v1.fits'
    filters = ['Ha', 'HaC', 'SII', 'r', 'i']
    for f in filters:
        print "  Building twilight flat MasterCal for: {}".format(f)

        # Select filter name using a substring of the official designation.
        qd['Filter2'] = f + '_G%'
        mc_name = 'MCflat_{}.fits'.format(f)
        if os.path.exists(mc_name):
            if overwrite is True:
                remove = raw_input('Remove flat file {}? (y), n '.format(mc_name))
                if remove == 'y':
                    os.remove(mc_name)
                else:
                    return None
            else:
                print('Master flat, {} already exists and overwrite={}'.format(mc_name, overwrite))
                return None
        flat_files = fileSelect.fileListQuery(dbFile, fileSelect.createQuery('twiFlat', qd), qd)
        if len(flat_files) > 0:
            gmos.giflat(','.join(str(x) for x in flat_files), mc_name, 
                         bias='MCbias', **flat_flags)
    # Clean up
    if not os.path.exists(mc_name):
        sys.exit('ERROR creating Master Flat Field: {}'.foramt(mc_name))
    if qd['Instrument']=='GMOS-N':
        image_str = 'gN'
    else:
        image_str = 'gS'
    image_str = '{}{}*.fits'.format(image_str, qd['DateObs'][0:4])
    for f in filters:
        del_str = f+image_str
        iraf.imdel(del_str)
    flist = glob.glob('tmpfile*')
    for ifile in flist:
        os.remove(ifile)
    iraf.chdir(cur_dir)
    #os.chdir(cur_dir)
    
def calibrate_science_images(qd, dbFile, data_dir, biasfilename='MCbias', overwrite=True):
    '''
    despite the fact that it looks like this can be run from outside the
    raw directory, it can't be.
    
    
    #Bad pixel maps live in /Users/bostroem/anaconda/envs/geminiconda/iraf_extern/gemini/gmos/data
    #You can find this directory with pyraf; cd gmos; cd data; pwd
    '''
    print ("=== Processing Science Images ===")
    cur_dir = os.getcwd()
    iraf.chdir(data_dir)
    prefix = 'rg'

    # Set task parameters.
    # Employ the imaging Static BPM for this set of detectors.
    gmos.gireduce.unlearn()
    sciFlags = {
        'fl_over':'yes', #Overscan subtraction
        'fl_trim':'yes', #Overscan region trimmed
        'fl_bias':'yes', #Subtract Bias residual
        'fl_dark':'no', #Subtract Dark
        'fl_flat':'yes', #Subtract flat
        'logfile':'gireduceLog.txt',
        'rawpath':'',
        'fl_vardq':'yes', #Propagate VAR and DQ extensions
        'verbose':'no'
        }
    if qd['Instrument'] == 'GMOS-N':
       sciFlags['bpm'] = 'gmos$data/gmos-n_bpm_HAM_22_12amp_v1.fits'
    else:
        sciFlags['bpm'] = 'gmos$data/gmos-s_bpm_HAM_22_12amp_v1.fits',

    gemtools.gemextn.unlearn()    # disarms a bug in gmosaic
    gmos.gmosaic.unlearn()
    mosaicFlags = {
        'fl_paste':'no',
        'fl_fixpix':'no',
        'fl_clean':'yes',
        'geointer':'nearest',
        'logfile':'gmosaicLog.txt',
        'fl_vardq':'yes',
        'fl_fulldq':'yes',
        'verbose':'no'
        }
    # Reduce the science images, then mosaic the extensions in a loop
    filters = ['Ha', 'HaC', 'SII', 'r', 'i']
    for f in filters:
        print "    Processing science images for: %s" % (f)
        qd['Filter2'] = f + '_G%'
        flatFile = 'MCflat_' + f
        sciFiles = fileSelect.fileListQuery(dbFile, fileSelect.createQuery('sciImg', qd), qd)
        if len(sciFiles) > 0:
            gmos.gireduce (','.join(str(x) for x in sciFiles), bias=biasfilename, 
                           flat1=flatFile, **sciFlags)
            #Combine multi-extension images into one image
            for file in sciFiles:
                gmos.gmosaic (prefix+file, **mosaicFlags)
    iraf.chdir(cur_dir)
    
def calibrate_standard_images(qd, dbFile, std_name, biasfilename='MCbias', overwrite=True):
    print ("=== Processing Science Images ===")
    prefix = 'rg'
    cur_dir = os.getcwd()
    iraf.chdir(data_dir)
    # Set task parameters.
    # Employ the imaging Static BPM for this set of detectors.
    gmos.gireduce.unlearn()
    sciFlags = {
        'fl_over':'yes',
        'fl_trim':'yes',
        'fl_bias':'yes',
        'fl_dark':'no',
        'fl_flat':'yes',
        'logfile':'gireduceLog.txt',
        'rawpath':'',
        'fl_vardq':'yes',
        #####'bpm':'bpm_gmos-s_EEV_v1_2x2_img_MEF.fits',
        'verbose':'no'
        }
    gemtools.gemextn.unlearn()    # disarms a bug in gmosaic
    gmos.gmosaic.unlearn()
    mosaicFlags = {
        'fl_paste':'no',
        'fl_fixpix':'no',
        'fl_clean':'yes',
        'geointer':'nearest',
        'logfile':'gmosaicLog.txt',
        'fl_vardq':'yes',
        'fl_fulldq':'yes',
        'verbose':'no'
        }
    # Reduce the science images, then mosaic the extensions in a loop
    filters = ['Ha', 'HaC', 'SII', 'r', 'i']
    for f in filters:
        print "    Processing science images for: %s" % (f)
        qd['Filter2'] = f + '_G%'
        flatFile = 'MCflat_' + f
        sql_query = '''SELECT file FROM obslog WHERE Object='{}' AND Filter2 LIKE '{}%' '''.format(std_name, f)
        sciFiles = run_query(sql_query, dbFile)
        sciFiles = [x[0] for x in sciFiles]
        if len(sciFiles) > 0:
            gmos.gireduce (','.join(str(x) for x in sciFiles), bias=biasfilename, 
                           flat1=flatFile, **sciFlags)
            for file in sciFiles:
                gmos.gmosaic (prefix+file, **mosaicFlags)
    iraf.chdir(cur_dir)




def create_coadd_img(qd, targets, dbFile, data_dir, prefix='mrg', overwrite=True):
    '''
    despite the fact that it looks like this can be run from outside the
    raw directory, it can't be.
    
    Caveats:
    * It takes a lot of patience and trial-and-error tweaking of parameters 
        to get good results
    * There is little control over sky background
    * The output image is no bigger than the first (reference) image, 
        rather than the union of the image footprints
    
    '''
    ## Co-add the images, per position and filter.
    print (" -- Begin image co-addition --")
    cur_dir = os.getcwd()
    iraf.chdir(data_dir)

    # Use primarily the default task parameters.
    gemtools.imcoadd.unlearn()
    coaddFlags = {
        'fwhm':3,
        'datamax':6.e4,
        'geointer':'nearest',
        'logfile':'imcoaddLog.txt'
        }
    
    filters = ['Ha', 'HaC', 'SII', 'r', 'i']
    for f in filters:
        print "  - Co-addding science images in filter: {}".format(f)
        qd['Filter2'] = f + '_G%'
        for t in targets:
            qd['Object'] = t + '%'
            print "  - Co-addding science images for position: {}".format(t)
            outImage = t + '_' + f + '.fits'
            coAddFiles = fileSelect.fileListQuery(dbFile, fileSelect.createQuery('sciImg', qd), qd)
            if len(coAddFiles) > 1:
                gemtools.imcoadd(','.join(prefix+str(x) for x in coAddFiles),
                    outimage=outImage, **coaddFlags)

    iraf.delete ("*_trn*,*_pos,*_cen")
    iraf.imdelete ("*badpix.pl,*_med.fits,*_mag.fits")
    #iraf.imdelete ("mrgS*.fits")

    print ("=== Finished Calibration Processing ===")
    iraf.chdir(cur_dir)
    
if __name__ == "__main__":
    '''
    An example of running the script on the first imaging observations of SN2017eaw
    in r and i band
    '''

    qd = {'use_me':1,
          'Instrument':'GMOS-N',
          'CcdBin':'2 2',
          'RoI':'Full',
          'Object':'SN2017eaw%',
          'DateObs':'2018-06-10:2018-07-09' #2 months prior to observation
          }
    db_file='obsLog.sqlite3'

    #BIAS
    GMOS_imaging_calibration.create_master_bias(qd, REDUCE_DIR, os.path.join(REDUCE_DIR, db_file), 
                       master_bias=os.path.join(REDUCE_DIR,'MCbias.fits'), overwrite=True)
                   
    #TWILIGHT FLAT
    # Select flats obtained contemporaneously with the observations.
    qd['DateObs']='2018-06-01:2018-07-09'
    GMOS_imaging_calibration.create_master_twilight_flat(qd, db_file, REDUCE_DIR, overwrite=True)

    qd['DateObs'] = '*'
    GMOS_imaging_calibration.calibrate_science_images(qd, os.path.basename(db_file), REDUCE_DIR, overwrite=True)

    targets = ['SN2017eaw (first visit)']
    GMOS_imaging_calibration.create_coadd_img(qd, targets, os.path.basename(db_file), REDUCE_DIR, prefix='mrg', overwrite=True)

