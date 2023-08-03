import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage as ndimage

def plot_eke(lat, eke_avg):
    # smooth array for plotting
    eke_smooth = ndimage.gaussian_filter(eke_avg, sigma=0.9, order=0)

    # create plot
    fig, ax = plt.subplots()
    clevels = np.linspace(-8,8,33) #np.linspace(-14,14,29)  # contour levels
    cmap = plt.cm.PuOr 
    units = '$\mathrm{m}^{2}$ $\mathrm{s}^{-2}$'
    # define pressure levels for vertical cross setion
    p_levels = np.linspace(1000,100,19)
    # mesh the lat and vertical level values
    X,Y = np.meshgrid(lat[:,0],p_levels)  
    plt.xlabel("Latitude")
    plt.ylabel("Pressure (hPa)")
    contours_fill = plt.contourf(X,Y,eke_avg, cmap=cmap, levels=clevels, extend="both")
    ax.set_xlim(-5,25)
    plt.minorticks_on()
    plt.gca().invert_yaxis()  # invert y axis, gca stands for "get current axis" and is a helper function

    cbar = plt.colorbar(contours_fill,  shrink = .58, orientation='horizontal') #, pad=.09) #shrink = .75,

    # square up plot axes
    ax.set_aspect(1./ax.get_data_ratio())

    # save figure as a PDF
    fig.savefig('WRF_TCM_M-O_2001-2010avg_' + scenario_type + '_EKE.pdf', bbox_inches='tight')
