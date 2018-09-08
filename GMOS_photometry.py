import os

from matplotlib import pyplot as plt
import numpy as np

import photutils as pu
from astropy.wcs import WCS
from astropy.stats import sigma_clipped_stats
from astropy import table
from astropy.io import fits

import visualization as vis

def find_obj_center(filename, x=None, y=None, plot=True, fig_dir='./'):
    ofile = fits.open(filename)
    if (x is None) and (y is None):
        ra = ofile[0].header['ra']
        dec = ofile[0].header['dec']
        x, y = WCS(ofile[1].header).all_world2pix(ra, dec, 1)
    xlow, xhigh = int(x-50), int(x+50)
    ylow, yhigh = int(y-50), int(y+50)
    stamp = ofile[1].data[ylow:yhigh, xlow:xhigh]
    mean, median, std = sigma_clipped_stats(stamp, sigma=3.0, iters=5)  
    daofind = pu.DAOStarFinder(fwhm=4, threshold=5*std)
    sources = daofind(stamp)
    x_sources = sources['xcentroid']+xlow
    y_sources = sources['ycentroid']+ylow

    nearest = np.argmin(np.sqrt((x_sources-x)**2 + (y_sources-y)**2))
    xcen, ycen = x_sources[nearest], y_sources[nearest]
    if plot is True:
        plot_obj_center(ofile, xcen, ycen, x_sources, y_sources, stamp, 
                        xlow, xhigh, ylow, yhigh, fig_dir=fig_dir)
    return xcen, ycen
    
def plot_obj_center(ofile, xcen, ycen, x_sources, y_sources, stamp, xlow, xhigh, ylow, yhigh,
                    fig_dir='./'):
    fig, (ax1, ax2) = plt.subplots(1,2)
    vmin, vmax = vis.zscale(stamp)
    ax1.set_title('Check Correct Star')
    ax1.imshow(ofile[1].data, cmap='bone', vmin=vmin, vmax=vmax, interpolation='nearest')
    ax1.set_xlim(xlow, xhigh)
    ax1.set_ylim(ylow, yhigh)
    ax1.plot(x_sources, y_sources, 'r.')
    ax1.plot(xcen, ycen, '*', mfc='c', mec='b')
    
    ax2.set_title('Check centering')
    ax2.imshow(ofile[1].data, cmap='bone', vmin=vmin, vmax=vmax, interpolation='nearest')
    ax2.set_xlim(xcen-15, xcen+15)
    ax2.set_ylim(ycen-15, ycen+15)
    ax2.plot(xcen, ycen, '*', mfc='c', mec='b')
    plt.savefig(os.path.join(fig_dir, '{}_id_confirm.pdf'.format(ofile[0].header['object'])))
    
def perform_aperture_photometry(xcen, ycen, filename, aperture_radii = np.arange(2, 15), bkg_r_in=16., bkg_r_out=20):
    ofile = fits.open(filename)
    apertures = [pu.CircularAperture((xcen, ycen), r=r) for r in aperture_radii]
    annulus_apertures = pu.CircularAnnulus((xcen, ycen), r_in=bkg_r_in, r_out=bkg_r_out)
    apertures.append(annulus_apertures)
    phot_table = pu.aperture_photometry(ofile[1].data, apertures )
    bkg_colname = phot_table.colnames[-1]
    bkg_mean = phot_table[bkg_colname] / annulus_apertures.area()
    for aper, icol in zip(apertures, phot_table.colnames[3:]):
        bkg_sum = bkg_mean*aper.area()
        phot_table.add_column(phot_table[icol]-bkg_sum, name='{}_bkg_sub'.format(icol))
    return phot_table, apertures

def find_std_zeropoint(file_dir, file_list, k, m_std, use_aperture, 
                       x=None, y=None, plot=True, fig_dir='./'):
    phot_tab_std = None
    for ifile in file_list: 
        filename = os.path.join(file_dir, ifile)
        xcen, ycen = find_obj_center(filename, x=x, y=y, plot=plot, fig_dir=fig_dir)
        aperture = np.arange(2, 20, 2)
        phot_tab_std_tmp, apertures_std = perform_aperture_photometry(xcen, ycen, filename, aperture_radii=aperture)
        airmass = fits.getval(filename, 'airmass', 0)
        phot_tab_std_tmp.add_column(table.Column(data=[ifile], name='filename'))
        phot_tab_std_tmp.add_column(table.Column(data=[airmass], name='airmass'))
        aper_indx = np.where(aperture==use_aperture)[0][0]
        N = phot_tab_std_tmp['aperture_sum_{}_bkg_sub'.format(aper_indx)]
        t = fits.getval(filename, 'exptime', 0)
        m_inst = 28 - 2.5*np.log10(N/t) - k*(airmass-1)
        phot_tab_std_tmp.add_column(table.Column(data=[m_inst], name='m_inst_{}'.format(aper_indx)))
        if phot_tab_std:
            phot_tab_std = table.vstack((phot_tab_std, phot_tab_std_tmp))
        else:
            phot_tab_std = phot_tab_std_tmp
        if plot is True:
            plt.figure()
            for indx, aper in enumerate(apertures_std[:-1]):
                colname = 'aperture_sum_{}_bkg_sub'.format(indx)
                plt.plot(aper.r, phot_tab_std[-1][colname], 'o')
            plt.grid()

    m_zpt = np.median(m_std - phot_tab_std['m_inst_{}'.format(aper_indx)] + 28)  
    return m_zpt