#!/usr/bin/env python

# import libraries
from datetime import datetime
import os.path
import argparse
import numpy as np
import pandas as pd
import warnings
import math
import mapio.gmt as gmt
from scipy import ndimage
import psutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from copy import deepcopy
from pylab import arccos,argsort,cross,dot,double,eigh,pi,trace,zeros
from sklearn import mixture
from sklearn.metrics import mean_squared_error
import slab2functions as s2f

def main(args):

    slabsbyfile = args.slabsbyfile
    slabsbyslab = args.slabsbyslab
    inputfolder = args.inputfolder
    inputdate = args.inputdate
    origorcentl = args.origorcentl
    origorcentd = args.origorcentd
    if args.minlength is None:
        minlength = 999999999
    else:
        minlength = args.minlength
    maxdep = args.maxdep
    maxdepdiff = args.maxdepdiff
    slaborev = args.slaborev
    
    pd.options.mode.chained_assignment = None
    warnings.filterwarnings("ignore", message="invalid value encountered in less")
    warnings.filterwarnings("ignore", message="invalid value encountered in true_divide")
    warnings.filterwarnings("ignore", message="invalid value encountered in greater")
    warnings.filterwarnings("ignore", message="invalid value encountered in double_scalars")

    
    # list folder names of all slab models to calculate szt from, and move to new folder structure
    filelist = ['kur_slab2_01.03.18','alu_slab2_01.04.18','hel_slab2_01.04.18','hin_slab2_01.04.18','ryu_slab2_01.04.18','ker_slab2_01.08.18','sam_slab2_01.03.18','sum_slab2_01.05.18','man_slab2_01.08.18','sol_slab2_01.08.18','izu_slab2_01.08.18','pam_slab2_01.04.18','him_slab2_01.04.18','cal_slab2_01.04.18','mak_slab2_01.04.18','sco_slab2_01.04.18','car_slab2_01.04.18','mue_slab2_01.04.18','cas_slab2_01.04.18','cam_slab2_01.03.18','puy_slab2_01.04.18','van_slab2_01.04.18','png_slab2_01.04.18','cot_slab2_01.04.18','phi_slab2_01.04.18','sul_slab2_01.04.18','hal_slab2_01.04.18']

    # create new directory system for slab output
    os.system('rm -r %s'%slabsbyfile)
    os.system('mkdir %s'%slabsbyfile)
    os.system('mkdir %s/grids'%slabsbyfile)
    os.system('mkdir %s/supplement'%slabsbyfile)
    os.system('mkdir %s/nodes'%slabsbyfile)
    os.system('mkdir %s/surfacetext'%slabsbyfile)
    os.system('mkdir %s/clippingmasks'%slabsbyfile)
    os.system('mkdir %s/filtereddata'%slabsbyfile)
    os.system('mkdir %s/inputdata'%slabsbyfile)
    os.system('mkdir %s/parameters'%slabsbyfile)
    os.system('mkdir %s/szt'%slabsbyfile)
    os.system('mkdir %s/maps'%slabsbyfile)
    os.system('mkdir %s/crossections'%slabsbyfile)

    printtest = False
    
    figz = plt.figure(figsize=(15, 10))
    ax1z = figz.add_subplot(111)
    n = 0
    clist = ['yellowgreen','yellow','wheat','violet','turquoise','teal','silver','sienna','salmon','red','plum','pink','orchid','orange','olive','navy','magenta','lightgreen','lightblue','green','goldenrod','cyan','blue','darkgreen']

    slabdf = []
    shaldf = []
    deepdf = []
    peakdf = []
    nevsdf = []
    
    for folder in filelist:

        (slab,s2k,date) = folder.split('_')
        
        inFile = '%s/%s_%s_input.csv'%(inputfolder,slab,inputdate)
        fname = '%s/%s/%s_slab2_dep_%s.grd'%(slabsbyslab,folder,slab,date)
        
        thisfolder = '%s/%s/%s_slab2'%(slabsbyslab,folder,slab)
        
        if slab != 'hin' and slab != 'pam' and slab != 'hal':
            eventlistALL = pd.read_table('%s' % inFile, sep=',', dtype={
                    'lon': np.float64, 'lat': np.float64,'depth': np.float64,
                    'unc': np.float64, 'etype': str, 'ID': np.int, 'mag': np.float64,
                    'S1': np.float64, 'D1': np.float64, 'R1': np.float64,
                    'S2': np.float64, 'D2': np.float64, 'R2': np.float64,
                    'src': str, 'time': str, 'mlon': np.float64, 'mlat': np.float64,
                    'mdep': np.float64})

            ogcolumns = ['lat', 'lon', 'depth', 'unc', 'etype', 'ID', 'mag', 'time', \
                        'S1', 'D1', 'R1','S2', 'D2', 'R2', 'src']
            kagancols = ['lat', 'lon', 'depth', 'unc', 'etype', 'ID', 'mag', 'time', \
                        'S1', 'D1', 'R1','S2', 'D2', 'R2', 'src', 'mlon', 'mlat', 'mdep']

            eventlist = eventlistALL[kagancols]

            depgrid = gmt.GMTGrid.load(fname)
            strgrid, dipgrid = s2f.mkSDgrd(depgrid)
            slab1data = s2f.mkSlabData(depgrid, strgrid, dipgrid, printtest)
            
            slab1data.loc[slab1data.lon < 0, 'lon'] += 360
            eventlist.loc[eventlist.lon < 0, 'lon'] += 360
            eventlist.loc[eventlist.mlon < 0, 'mlon'] += 360

            maskdf = pd.read_csv('%s_clp_%s.csv'%(thisfolder,date), delim_whitespace=True, names=['lon','lat'])
            slab1data = s2f.getDFinMask(slab1data,maskdf)
            eventlist = s2f.getDFinMask(eventlist,maskdf)
        
            eventlist = s2f.getReferenceKagan(slab1data, eventlist, origorcentl, origorcentd)

            savedir = '%s/szt'%slabsbyfile
            seismo_thick, taper_start, deplist, normpdfD, lendata = s2f.getSZthickness(eventlist,folder,slab,maxdep,maxdepdiff,origorcentl,origorcentd,slaborev,savedir,minlength)
            print ('slab, seismo_thick:',slab, seismo_thick, lendata)
        
            if lendata > 0:
                ax1z.plot(deplist, normpdfD,label='%s, s:%.1f, d:%.1f'%(slab,taper_start,seismo_thick),linewidth=2,c=clist[n])
                ax1z.plot([seismo_thick,seismo_thick],[0.09,0.1],linewidth=2,linestyle='dashed',c=clist[n])
                ax1z.plot([taper_start,taper_start],[0.09,0.1],linewidth=2,linestyle='dotted',c=clist[n]),
                n+=1
    
            slabdf.append(slab)
            shaldf.append(taper_start)
            deepdf.append(seismo_thick)
            peakdf.append(deplist[np.argmax(normpdfD)])
            nevsdf.append(lendata)
    
        os.system('cp %s %s/inputdata'%(inFile,slabsbyfile))
        os.system('cp %s_dep_%s.grd %s/grids'%(thisfolder,date,slabsbyfile))
        os.system('cp %s_str_%s.grd %s/grids'%(thisfolder,date,slabsbyfile))
        os.system('cp %s_dip_%s.grd %s/grids'%(thisfolder,date,slabsbyfile))
        os.system('cp %s_unc_%s.grd %s/grids'%(thisfolder,date,slabsbyfile))
        os.system('cp %s_thk_%s.grd %s/grids'%(thisfolder,date,slabsbyfile))

        os.system('cp %s_res_%s.csv %s/surfacetext'%(thisfolder,date,slabsbyfile))
        os.system('cp %s_clp_%s.csv %s/clippingmasks'%(thisfolder,date,slabsbyfile))
        os.system('cp %s_dat_%s.csv %s/filtereddata'%(thisfolder,date,slabsbyfile))
        os.system('cp %s_nod_%s.csv %s/nodes'%(thisfolder,date,slabsbyfile))
        os.system('cp %s_sup_%s.csv %s/supplement'%(thisfolder,date,slabsbyfile))
        os.system('cp %s_par_%s.csv %s/parameters'%(thisfolder,date,slabsbyfile))
        os.system('cp %s_figs_%s/* %s/maps'%(thisfolder,date,slabsbyfile))
        os.system('cp %s_xsecs_%s/* %s/crossections'%(thisfolder,date,slabsbyfile))
        os.system('rm %s/maps/dep2.cpt'%slabsbyfile)
        os.system('rm %s/maps/tiltedd.dat'%slabsbyfile)
        os.system('rm %s/maps/tiltedp.dat'%slabsbyfile)
        os.system('rm %s/maps/tilteds.dat'%slabsbyfile)
        os.system('rm %s/maps/tiltedt.dat'%slabsbyfile)
        os.system('rm %s/maps/tiltedu.dat'%slabsbyfile)

    ax1z.set_xlim([0,65])
    ax1z.legend(loc='best')
    ax1z.grid()
    ax1z.set_xlabel('Depths')
    ax1z.set_ylabel('P')
    ax1z.set_title('Slab depth distributions (surfacefilt = %i km, orig = %s, depth = %s, hist= %s)'%(maxdepdiff,origorcentl,origorcentd,slaborev))
    figtitle = '%s/szt/allpdf.png' % (slabsbyfile)
    figz.savefig(figtitle)
    plt.close()
    
    deetsdf = pd.DataFrame({'slab':slabdf,'shallow_lim':shaldf,'deep_lim':deepdf,'peak_depth':peakdf,'number_events':nevsdf})
    
    deetsdf = deetsdf[['slab','shallow_lim','deep_lim','peak_depth','number_events']]
    deetsdf.to_csv('%s/szt/table.csv' % (slabsbyfile),header=True,index=False,na_rep=np.nan,float_format='%0.1f')

# Help/description and command line argument parser
if __name__=='__main__':
    desc = '''
        this can be used to move individual slab files (grids, parameters, 
        data, nodes, etc.) to a new file structure organized by file type 
        instead of by slab. This also calculates seismogenic zone thickness 
        for each slab using the Slab2 model.
        
        Required arguments include: 
            directory leading to where the original slab2 output folders are stored (-s slabsbyslab)
            a new directory to save the new file structure to (-f slabsbyfile)
            a directory listing the original input folders (-i inputfolder)
            the date of all of the input folders as MM-YY (-t inputdate)
            a flag indicating whether to use event origin or cmt origin for slab reference (-l origorcentl)
            a flag indicating whether to use event depth or cmt depth for depth histogram (-d origorcentd)
            a minimum length to use for 5th and 95th percentiles instead of 10th and 90th (-n minlength)
            depth distance around slab2 to filter events by (-m maxdepdiff)
            maximum depth to extend distribution to (-x maxdep)
            a flag indicating whether to make histogram of slab depths or event depths (-b slaborev)
            
        The list of slab folders/versions must be changed manually in the code.
        
        '''
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('-s', '--slabsbyslab', dest='slabsbyslab', type=str,
                        required=True, help='directory containing Slab2 output folders')
                        
    parser.add_argument('-f', '--slabsbyfile', dest='slabsbyfile', type=str,
                        required=True, help='new directory to save file structure to')
                        
    parser.add_argument('-i', '--inputfolder', dest='inputfolder', type=str,
                        required=True, help='directory containing Slab2 input files')
                        
    parser.add_argument('-t', '--inputdate', dest='inputdate', type=str,
                        required=True, help='date of input files (MM-YY)')
                        
    parser.add_argument('-l', '--origorcentl', dest='origorcentl', type=str,
                        required=True, help='flag indicating origin (o) or cmt (c) lon lat for slab reference')
                        
    parser.add_argument('-d', '--origorcentd', dest='origorcentd', type=str,
                        required=True, help='flag indicating origin (o) or cmt (c) depth for slab reference')
                        
    parser.add_argument('-n', '--minlength', dest='minlength', type=int,
                        help='minimum length for 5th and 95th percentile calculations (optional)')
                        
    parser.add_argument('-m', '--maxdepdiff', dest='maxdepdiff', type=int,
                        required=True, help='depth distance around slab2 to filter events by')
                        
    parser.add_argument('-x', '--maxdep', dest='maxdep', type=int,
                        required=True, help='maximum depth to extend distribution to')
                        
    parser.add_argument('-b','--slaborev', dest='slaborev', type=str,
                        required=True, help='make histogram of slab depths (s) or event depths (e)')
                        
    pargs = parser.parse_args()
    
    #cProfile.run('main(pargs)')
    main(pargs)
