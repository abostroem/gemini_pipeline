'''
Visualize steps of the calibration process to ensure everything went according to plan
'''
from matplotlib import pyplot as plt
from astropy.io import fits

from visualization import zscale #https://github.com/abostroem/utilities

overscan_size = 32 #pixels
unusable_bottom = 48//2 #pixels

def visualize_bias(biasfile, out_filename):
    fig, ax_list = plt.subplots(nrows=1, ncols=12, sharey=True, figsize=[10, 7])
    ofile = fits.open(biasfile)
    object_name = ofile[0].header['OBJECT']
    fig.suptitle(object_name)
    if len(ofile) > 13:
        ofile = ofile[1::3]
    else:
        ofile = ofile[1:]
    extnum = 1
    for ax, ext in zip(ax_list, ofile):
        img = ext.data
        #remove overscan region
        if extnum%2 == 0:
            img = img[unusable_bottom//2:, overscan_size:]
        else:
            img = img[unusable_bottom:, :-overscan_size]
        vmin, vmax = zscale(img)
        ax.imshow(img, cmap='bone', vmin=vmin, vmax=vmax)
        ax.set_xticks([])
        ax.set_title('EXT {}'.format(extnum))
        extnum+=1
    plt.subplots_adjust(wspace=0)
    plt.savefig(out_filename)
        
    

def visualize_flat(flatfile, out_filename):
    fig, ax_list = plt.subplots(nrows=1, ncols=12, sharey=True, figsize=[10, 7])
    ofile = fits.open(flatfile)
    object_name = ofile[0].header['OBJECT']
    fig.suptitle(object_name)
    extnum = 1
    for ax, ext in zip(ax_list, ofile[1:]):
        img = ext.data
        vmin, vmax = zscale(img)
        ax.imshow(img, cmap='bone', vmin=vmin, vmax=vmax)
        ax.set_xticks([])
        ax.set_title('EXT {}'.format(extnum))
        extnum += 1
    plt.subplots_adjust(wspace=0)
    plt.savefig(out_filename)

def visualize_science(sciencefile, out_filename, remove_overscan=False):
    fig, ax_list = plt.subplots(nrows=1, ncols=12, sharey=True, figsize=[10, 7])
    ofile = fits.open(sciencefile)
    object_name = ofile[0].header['OBJECT']
    fig.suptitle(object_name)
    extnum=1
    for ax, ext in zip(ax_list, ofile[1:]):
        img = ext.data
        #remove overscan region
        if remove_overscan is True:
            if extnum%2 == 0:
                img = img[:, overscan_size:]
            else:
                img = img[:, :-overscan_size]
            img = img[unusable_bottom:, :]
        vmin, vmax = zscale(img)
        ax.imshow(img, cmap='bone', vmin=vmin, vmax=vmax)
        ax.set_xticks([])
        ax.set_title('EXT {}'.format(extnum))
        extnum += 1
    plt.savefig(out_filename)

def comp_to_science(biasfile, flatfile, sciencefile, out_filename, remove_overscan=False):
    fig, ax_list = plt.subplots(nrows=1, ncols=36, sharey=True, figsize=[25, 7])
    #BIAS
    ofile = fits.open(biasfile)
    extnum = 1
    for ax, ext in zip(ax_list[0::3], ofile[1::3]):
        img = ext.data
        #remove overscan region
        if extnum%2 == 0:
            img = img[unusable_bottom//2:, overscan_size:]
        else:
            img = img[unusable_bottom//2:, :-overscan_size]
        vmin, vmax = zscale(img)
        ax.imshow(img, cmap='bone', vmin=vmin, vmax=vmax)
        ax.set_xticks([])
        ax.set_title('BIA {}'.format(extnum))
        extnum+=1
    #FLAT
    ofile = fits.open(flatfile)
    extnum = 1
    for ax, ext in zip(ax_list[1::3], ofile[1:]):
        img = ext.data
        vmin, vmax = zscale(img)
        ax.imshow(img, cmap='bone', vmin=vmin, vmax=vmax)
        ax.set_xticks([])
        ax.set_title('FLT {}'.format(extnum))
        extnum += 1
        
    #Science
    ofile = fits.open(sciencefile)
    object_name = ofile[0].header['OBJECT']
    fig.suptitle(object_name)
    extnum=1
    for ax, ext in zip(ax_list[2::3], ofile[1:]):
        img = ext.data
        #remove overscan region
        if remove_overscan is True:
            if extnum%2 == 0:
                img = img[unusable_bottom:, overscan_size:]
            else:
                img = img[unusable_bottom:, :-overscan_size]
        vmin, vmax = zscale(img)
        ax.imshow(img, cmap='bone', vmin=vmin, vmax=vmax)
        ax.set_xticks([])
        ax.set_title('SCI {}'.format(extnum))
        extnum += 1
    plt.savefig(out_filename)



