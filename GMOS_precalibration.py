import os
import shutil
import subprocess
import glob
import sys
import stat
from astropy.io import ascii as asc

def check_download(directory_list):
    '''
    Run md5sum on files and compare to gemini file to make sure nothing was corrupted in the
    download. (Note macs natively come with md5 which, with the -r flag reproduced the 
    md5sum hash)
    
    It is assumed that each directory has a md5sums.txt file with 2 columns. The first
    column is the hash and the second is the filename. Each file in the filename column
    is run through md5sum and if the hash is different, then a message is printed to the 
    screen
    
    Input:
        directory_list: list
            list of directories to check. 
    Output:
        if all files are uncorrupted, None, otherwise a message is printed to the screen
    '''
    for idir in directory_list:
        tbdata = asc.read(os.path.join(idir, 'md5sums.txt'), names=['md5_hash', 'filename'])

        for ihash, ifile in tbdata:
            if os.path.exists(os.path.join(idir, ifile)):
                if sys.platform=='darwin':
                    x = subprocess.check_output('md5 -r {}'.format(os.path.join(idir, ifile)), shell=True)
                else:
                    x = subprocess.check_output('md5sum {}'.format(os.path.join(idir, ifile)), shell=True)
                if x.split()[0] != ihash:
                    print(ifile, x.split()[0], ihash)

                
def unzip_files(directory_list):
    '''
    Unzip *.bz2 files in each directory in the directory_list
    
    Input:
        directory_list: list
            list of directories with to .bz2 files to unzip
    Output:
        unzipped files
    '''
    for idir in directory_list:
        subprocess.call('bunzip2 {}'.format(os.path.join(idir, '*.bz2')), shell=True)
    
def copy_to_reduction_dir(input_directory_list, output_directory):
    '''
    Copy all files to a new directory for calibration and reduction
    Input:
        input_directory_list: list
            list of directories with files to copy. These can be .fits or .bz2
        output_directory: str
            name of directory where all files will be copied to
    Output:
        transfer of all files from directories in input_directory_list to output_directory
    '''
    for idir in input_directory_list:
        print('COPYING .fits and .bz2 files from {} to {}'.format(idir, output_directory))
        flist = glob.glob(os.path.join(idir, '*.fits')) + \
                glob.glob(os.path.join(idir, '*.bz2'))
        for ifile in flist:
            shutil.move(ifile, os.path.join(output_directory, os.path.basename(ifile)))

        
def create_observation_database(code_directory, output_directory, database_filename='obsLog.sqlite3'):
    '''
    The calibration pipeline requires the creation of a database like file to 
    create lists of the files required for each calibration step. 
    
    Input:
        input_directory_list: list
            list of directories with files to copy. These can be .fits or .bz2
        output_directory: str
            name of directory where all files will be copied to
    Output:
        database file: a sqlite3 database with the name given in database_filename
    '''
    cur_dir = os.getcwd()
    shutil.copyfile(os.path.join(code_directory, 'obslog.py'), os.path.join(output_directory, 'obslog.py'))
    os.chdir(output_directory)
    cmd = '{} {}'.format(os.path.join(code_directory, 'obslog.py'),
                         os.path.join(output_directory, database_filename))
    os.chmod('obslog.py', stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH|stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH|stat.S_IWUSR|stat.S_IWGRP|stat.S_IWOTH)
    subprocess.call('ls -l obslog.py', shell=True)
    command_run = subprocess.call('./obslog.py {}'.format(database_filename), shell=True)
    if command_run == 0:
        pass
    else:
        sys.exit('Error running obslog.py')
    #obslog.obsLog(['obslog.py', 'obsLog.sqlite3']) #I can't figure out why this doesn't work!!!
    os.chdir(cur_dir)
    print('CREATED obsLog.sqlite3 observation database')
    
if __name__ == "__main__":
    DATA_DIR = '../data/reduced/2017eaw/gemini_data.GN-2018B-Q-204/'
    CALIB_DIR = '../data/reduced/2017eaw/gemini_calibs.GN-2018B-Q-204/'
    REDUCE_DIR = '../data/reduced/2017eaw'
    CODE_DIR = '../code'

    
    check_download([CALIB_DIR, DATA_DIR])
    copy_to_reduction_dir([CALIB_DIR, DATA_DIR], REDUCE_DIR)
    unzip_files([REDUCE_DIR])
    create_observation_database(CODE_DIR, REDUCE_DIR)