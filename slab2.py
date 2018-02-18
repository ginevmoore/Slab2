#!/usr/bin/env python


### Up to date as of 4.17.2017 GLM ###
'''Section 0: Import python libraries
    This code has a number of dependencies, listed below.
    They can be installed using the virtual environment "slab23"
        that is setup using script 'library/setup3env.sh'.
    Additional functions are housed in file 'slab2functions.py' 
        and imported below.
    There are some additional dependencies used by the function file 
        that do not need to be installed separately.
'''
# stdlib imports
from datetime import datetime #**
import os.path
import argparse
import numpy as np #**
from pandas import DataFrame #**
import pandas as pd #**
import warnings
import slab2functions as s2f #**
import math
import mapio.gmt as gmt #**
from functools import partial #**
from multiprocess import Pool #**
import loops as loops #**
from scipy import ndimage
import psutil
import cProfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main(args):

    '''Section 1: Setup
	In this section:
	    (1) Identify necessary input files
	    (2) Load parameters from '[slab]input.par'
        (3) Define optional boxes for PDF/print testing
	    (4) Define output file names
        (5) Gathering optional arguments, setting defaults
        (6) Define search ellipsoid parameters
        (7) Define Average active source profiles
	    (8) Define reference model (Slab1.0 and/or slab guides)
        (9) Define Trench Locations
        (10) Open and modify input dataset
        (11) Calculate seismogenic zone thickness
        (12) Record variable parameters used for this model
        (13) Define search grid
        (14) Identify tomography datasets
        (15) Initialize arrays for Section 2 '''

    print('Start Section 1 of 7: Setup')

    print('    Loading inputs...')

    ''' ------ (1) Identify necessary input files ------ '''
    
    trenches = 'library/misc/trenches_usgs_2017_depths.csv'
    agesFile = 'library/misc/interp_age.3.2g.nc'
    ageerrorsFile = 'library/misc/interp_ageerror.3.2g.nc'
    polygonFile = 'library/misc/slab_polygons.txt'
    #badFile = 'library/misc/remove0718.csv'
    addFile = 'library/misc/addagain.csv'
    parFile = args.parFile
    pd.options.mode.chained_assignment = None
    warnings.filterwarnings("ignore", message="invalid value encountered in less")
    warnings.filterwarnings("ignore", message="invalid value encountered in true_divide")
    warnings.filterwarnings("ignore", message="invalid value encountered in greater")
    warnings.filterwarnings("ignore", message="invalid value encountered in double_scalars")

    ''' ------ (2) Load parameters from '[slab]input.par' ------'''

    for line in open(parFile):
        plist = line.split()
        if len(plist)>2:
            if plist[0] == 'inFile':
                inFile = plist[2]
            if plist[0] == 'use_box':
                use_box = plist[2]
            if plist[0] == 'latmin':
                latmin = np.float64(plist[2])
            if plist[0] == 'latmax':
                latmax = np.float64(plist[2])
            if plist[0] == 'lonmin':
                lonmin = np.float64(plist[2])
            if plist[0] == 'lonmax':
                lonmax = np.float64(plist[2])
            if plist[0] == 'slab':
                slab = plist[2]
            if plist[0] == 'grid':
                grid = np.float64(plist[2])
            if plist[0] == 'radius1':
                radius1 = np.float64(plist[2])
            if plist[0] == 'radius2':
                radius2 = np.float64(plist[2])
            if plist[0] == 'sdr':
                sdr = np.float64(plist[2])
            if plist[0] == 'ddr':
                ddr = np.float64(plist[2])
            if plist[0] == 'taper':
                taper = np.float64(plist[2])
            if plist[0] == 'T':
                T = np.float64(plist[2])
            if plist[0] == 'node':
                node = np.float64(plist[2])
            if plist[0] == 'filt':
                filt = np.float64(plist[2])
            if plist[0] == 'maxdist':
                maxdist = np.float64(plist[2])
            if plist[0] == 'minunc':
                minunc = np.float64(plist[2])
            if plist[0] == 'mindip':
                mindip = np.float64(plist[2])
            if plist[0] == 'minstk':
                minstk = np.float64(plist[2])
            if plist[0] == 'maxthickness':
                maxthickness = np.float64(plist[2])
            if plist[0] == 'seismo_thick':
                seismo_thick = np.float64(plist[2])
            if plist[0] == 'dipthresh':
                dipthresh = np.float64(plist[2])
            if plist[0] == 'fracS':
                fracS = np.float64(plist[2])
            if plist[0] == 'kdeg':
                kdeg = np.float64(plist[2])
            if plist[0] == 'knot_no':
                knot_no = np.float64(plist[2])
            if plist[0] == 'rbfs':
                rbfs = np.float64(plist[2])

    # loop through to find latest slab input file if specified
    
    polyname = slab
    if slab == 'kur' or slab == 'izu':
        polyname = 'jap'
    if inFile == 'latest':
        monthmax = 0
        daymax = 0
        for filename in os.listdir('Input'):
            if filename.endswith('.csv'):
                try:
                    slabname,datei,instring = filename.split('_')
                except:
                    continue
                if slabname == polyname and instring == 'input.csv':
                    try:
                        monthi, dayi = datei.split('-')
                    except:
                        continue
                    monthi = int(monthi)
                    dayi = int(dayi)
                    if monthi >= monthmax and dayi > daymax:
                        inFile = 'Input/%s'%filename
    print ('       using input file: %s'%inFile)
    
    if slab == 'mue' or slab == 'phi' or slab == 'cot' or slab == 'sul' or slab == 'ryu':
        if args.undergrid is None:
            if slab == 'mue':
                print ('This slab is truncated by the Caribbean (car) slab, argument -u cardepgrid is required')
                print ('Exiting .... ')
                exit()
            if slab == 'cot':
                print ('This slab is truncated by the Halmahera (hal) slab, argument -u haldepgrid is required')
                print ('Exiting .... ')
                exit()
            if slab == 'sul':
                print ('This slab is truncated by the Halmahera (hal) slab, argument -u haldepgrid is required')
                print ('Exiting .... ')
                exit()
            if slab == 'phi':
                print ('This slab is truncated by the Halmahera (hal) slab, argument -u haldepgrid is required')
                print ('Exiting .... ')
                exit()
            if slab == 'ryu':
                print ('This slab is truncated by the Kurils-Japan (kur) slab, argument -u kurdepgrid is required')
                print ('Exiting .... ')
                exit()
        else:
            undergrid = args.undergrid

    ''' ------ (4) Define output file names ------ '''
    date = datetime.today().strftime('%m.%d.%y')
    now = datetime.now()
    time = '%s.%s' % (now.hour, now.minute)
    
    folder = '%s_slab2_%s' % (slab, date)
    os.system('mkdir Output/%s'%folder)

    outFile = 'Output/%s/%s_slab2_res_%s.csv' % (folder, slab, date)
    dataFile = 'Output/%s/%s_slab2_dat_%s.csv' % (folder, slab, date)
    nodeFile = 'Output/%s/%s_slab2_nod_%s.csv' % (folder, slab, date)
    rempFile = 'Output/%s/%s_slab2_rem_%s.csv' % (folder, slab, date)
    clipFile = 'Output/%s/%s_slab2_clp_%s.csv' % (folder, slab, date)
    these_params = 'Output/%s/%s_slab2_par_%s.csv' % (folder, slab, date)
    datainfo = 'Output/%s/%s_slab2_din_%s.csv' % (folder, slab, date)
    nodeinfo = 'Output/%s/%s_slab2_nin_%s.csv' % (folder, slab, date)
    suppFile = 'Output/%s/%s_slab2_sup_%s.csv' % (folder, slab, date)
    nodexFile = 'Output/%s/%s_slab2_nox_%s.csv' % (folder, slab, date)
    nodeuFile = 'Output/%s/%s_slab2_nou_%s.csv' % (folder, slab, date)
    
    depTextFile = 'Output/%s/%s_slab2_dep_%s.txt' % (folder, slab, date)
    depGridFile = 'Output/%s/%s_slab2_dep_%s.grd' % (folder, slab, date)
    strTextFile = 'Output/%s/%s_slab2_str_%s.txt' % (folder, slab, date)
    strGridFile = 'Output/%s/%s_slab2_str_%s.grd' % (folder, slab, date)
    dipTextFile = 'Output/%s/%s_slab2_dip_%s.txt' % (folder, slab, date)
    dipGridFile = 'Output/%s/%s_slab2_dip_%s.grd' % (folder, slab, date)
    uncTextFile = 'Output/%s/%s_slab2_unc_%s.txt' % (folder, slab, date)
    uncGridFile = 'Output/%s/%s_slab2_unc_%s.grd' % (folder, slab, date)
    thickTextFile = 'Output/%s/%s_slab2_thk_%s.txt' % (folder, slab, date)
    thickGridFile = 'Output/%s/%s_slab2_thk_%s.grd' % (folder, slab, date)
    savedir = 'Output/%s'%folder

    ''' ------ (3) Define optional boxes for PDF/print testing ------'''
    if args.test is not None:
        testlonmin = args.test[0]
        testlonmax = args.test[1]
        testlatmin = args.test[2]
        testlatmax = args.test[3]
        if testlonmin < 0:
            testlonmin += 360
        if testlonmax < 0:
            testlonmax += 360
        testarea = [testlonmin, testlonmax, testlatmin, testlatmax]
        printtest = True
        
        os.system('mkdir Output/PDF%s' % (slab))
        os.system('mkdir Output/multitest_%s' % (slab))
        
        f = open(datainfo, 'w+')
        f.write('dataID, nodeID, used_or_where_filtered')
        f.write('\n')
        f.close()
        
        f = open(datainfo, 'w+')
        f.write('nodeID, len(df), status, details')
        f.write('\n')
        f.close()

    else:
        # an area not in range of any slab polygon
        testarea = [220, 230, 15, 20]
        printtest = False

    ''' --- (5) Gathering optional arguments, setting defaults ---'''
    if use_box == 'yes':
        check = 1
        slab = s2f.rectangleIntersectsPolygon(lonmin, lonmax, latmin,
                                                latmax, polygonFile)
        if isinstance(slab, str):
            slab = slab
        else:
            try:
                slab = slab[0]
            except:
                print('System exit because box does not intersect slab polygon')
                raise SystemExit()
    elif use_box == 'no':
        check = 0
        lon1, lon2, lat1, lat2 = s2f.determine_polygon_extrema(slab,
                                                                polygonFile)
        lonmin = float(lon1)
        lonmax = float(lon2)
        latmin = float(lat1)
        latmax = float(lat2)
    else:
        print('use_box in slab2input.par must be "yes" or "no"')
        raise SystemExit()
    
    ''' ------ (6) Define search ellipsoid parameters ------'''
    alen = radius1
    blen = radius2
    ec = math.sqrt(1-((math.pow(blen, 2))/(math.pow(alen, 2))))
    mdist = alen * ec
    
    ''' ------ (7) Define Average active source profiles ------'''
    
    # Different because alu is variable E/W
    if slab == 'alu':
        AA_data = pd.read_csv('library/avprofiles/alu_av5.csv')
        global_average = False
    elif slab == 'him':
        AA_data = pd.read_csv('library/avprofiles/him_av.csv')
        global_average = False
    elif slab == 'kur' or slab == 'izu':
        AA_source = 'library/avprofiles/%s_av.txt' % 'jap'
        AA_data = pd.read_table(AA_source, delim_whitespace=True,\
                                header=None, names=['dist', 'depth'])
        AA_data = AA_data[AA_data.dist < 125]
        global_average = False
    
    # Use RF data like AA data to constrain flat slab in Mexico
    elif slab == 'cam':
        AA_source = 'library/avprofiles/%s_av.txt' % slab
        AA_data = pd.read_table(AA_source, delim_whitespace=True,\
                                header=None, names=['dist', 'depth'])
        RF_data = pd.read_csv('library/avprofiles/cam_RF_av.csv')
        AA_data = pd.concat([AA_data,RF_data])
        global_average = False

    else:
        global_average = False
        # See if there is a averace active source profile for this slab
        try:
            AA_source = 'library/avprofiles/%s_av.txt' % slab
            AA_data = pd.read_table(AA_source, delim_whitespace=True,\
                                    header=None, names=['dist', 'depth'])
        
        # If there is no profile for this slab, use the global profile
        except:
            AA_global = pd.read_csv('library/avprofiles/global_as_av2.csv')
            AA_data = AA_global[['dist', 'depth']]
            global_average = True
            if slab == 'phi' or slab == 'mue':
                AA_data = AA_data[AA_data.dist < 10]
            if slab == 'cot':
                AA_data = AA_data[AA_data.dist < 10]
            if slab == 'ita' or slab == 'puy':
                AA_data = AA_data[AA_data.dist < 1]

    ''' ------ (8) Define reference model (Slab1.0 and/or slab guides) ------'''

    polyname = slab
    if slab == 'kur' or slab == 'izu':
        polyname = 'jap'
    # Search for slab guides in library/slabguides
    slabguide = None
    slabguide2 = None
    for SGfile in os.listdir('library/slabguides'):
        if SGfile[0:3] == polyname:
            #print ('SGfile',SGfile)
            SGfile1 = SGfile
            slabguide = gmt.GMTGrid.load('library/slabguides/%s'%SGfile1)
            
            # Find secondary slab guide for regions where there are two
            if polyname == 'sum' or polyname == 'man' or polyname == 'phi' or polyname =='sam' or polyname == 'sco' or polyname == 'mak' or polyname == 'jap':
                for f in os.listdir('library/slabguides'):
                    if f[0:3] == polyname and f != SGfile:
                        print ('f',f)
                        SGfile2 = f
                        slabguide2 = gmt.GMTGrid.load('library/slabguides/%s'%SGfile2)
                        break
                break

    # Get Slab1.0 grid where applicable
    try:
        depgrid = s2f.get_grid(slab, 'depth')
    except:
        print ('       Slab1.0 does not exist in this region, using slab guide')
        depgrid = gmt.GMTGrid.load('library/slabguides/%s'%SGfile1)
        slabguide = None

    
    # Calculate strike and dip grids
    strgrid, dipgrid = s2f.mkSDgrd(depgrid)
    slab1data = s2f.mkSlabData(depgrid, strgrid, dipgrid, printtest)

    # Add slab guide data to Slab1.0 grids where necessary
    if slabguide is not None:
        print ('slab guide for this model:',slabguide)
        guidestr, guidedip = s2f.mkSDgrd(slabguide)
        guidedata = s2f.mkSlabData(slabguide, guidestr, guidedip, printtest)
        if SGfile1 == 'phi_SG_north':
            guidedata = guidedata[guidedata.lat>14]
        
        elif slab == 'ryu':
            guidedata = guidedata[guidedata.lon>137]
            slab1data = slab1data[slab1data.lat<=137]

        slab1data = pd.concat([slab1data, guidedata])
        slab1data = slab1data.reset_index(drop=True)

    if slabguide2 is not None:
        print ('secondary slab guide for this model:',slabguide2)
        guidestr, guidedip = s2f.mkSDgrd(slabguide2)
        guidedata = s2f.mkSlabData(slabguide2, guidestr, guidedip, printtest)
        if SGfile2 == 'phi_SG_north':
            guidedata = guidedata[guidedata.lat>14]
        slab1data = pd.concat([slab1data, guidedata])
        slab1data = slab1data.reset_index(drop=True)
        
    #slab1data.to_csv('slab1data.csv',header=True,index=False)
    ''' ------ (9) Define Trench Locations ------'''
    TR_data = pd.read_csv(trenches)
    if slab == 'izu' or slab == 'kur':
        TR_data = TR_data[TR_data.slab == 'jap']
    else:
        TR_data = TR_data[TR_data.slab == slab]
    TR_data = TR_data.reset_index(drop=True)
    TR_data.loc[TR_data.lon < 0, 'lon']+=360

    ''' ------ (10) Open and modify input dataset ------'''
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

    if printtest:
        lat65 = eventlist[eventlist.lat>65]
        if len(lat65)>0:
            s2f.addToDataInfo(lat65, 0, 'eventlist = eventlist[eventlist.lat <= 65]', datainfo,'df')

        dataGP = eventlist[eventlist.etype == 'GP']
        if len(dataGP>0):
            s2f.addToDataInfo(dataGP, 0, 'eventlist = eventlist[eventlist.etype != GP]', datainfo,'df')

    eventlist = eventlist[eventlist.lat <= 65]
    eventlist = eventlist[eventlist.etype != 'GP']
    maxID = eventlistALL['ID'].max()

    # Add/Remove manually identified points that don't follow general rules
    remdir = 'library/points_to_remove/current_files'
    for badFile in os.listdir(remdir):
        if badFile[0:3] == slab or badFile[0:3] == 'ALL' or ((slab == 'izu' or slab == 'kur') and badFile[0:3] == 'jap'):
            print ('       manually removing points listed in:',badFile)
            donotuse = pd.read_csv('%s/%s'%(remdir,badFile))
            eventlist = s2f.removePoints(donotuse, eventlist, lonmin,
                                        lonmax, latmin, latmax, printtest, datainfo, True, slab)
    doubleuse = pd.read_csv(addFile)
    eventlist, maxID = s2f.doublePoints(doubleuse, eventlist, maxID)
    
    if slab == 'kur':
        eventlist.loc[eventlist.etype == 'TO', 'unc'] = 100

    if slab == 'sul' or slab == 'man':
        eventlist = eventlist[eventlist.etype != 'CP']

    if slab == 'him':
        eventlist = eventlist[eventlist.src != 'schulte']
    
    if slab == 'sumz' or slab == 'kur' or slab == 'jap' or slab == 'izu':
    
        if printtest:
            lat65 = eventlist[eventlist.etype=='TO']
            if len(lat65)>0:
                s2f.addToDataInfo(lat65, 0, 'eventlist = eventlist[eventlist.etype != TO]', datainfo,'df')
        
        eventlist = eventlist[eventlist.etype != 'TO']

    if slab == 'kurz':
    
        if printtest:
            lat65 = eventlist[eventlist.etype=='ER']
            if len(lat65)>0:
                s2f.addToDataInfo(lat65, 0, 'eventlist = eventlist[eventlist.etype != ER]', datainfo,'df')
        
        eventlist = eventlist[eventlist.etype != 'ER']

    if slab == 'sol':
    
        if printtest:
            lat65 = eventlist[(eventlist.etype == 'BA') & (eventlist.lon <= 149)]
            if len(lat65)>0:
                s2f.addToDataInfo(lat65, 0, 'eventlist[(eventlist.etype != BA) | (eventlist.lon > 149)]', datainfo,'df')
        
        eventlist = eventlist[(eventlist.etype != 'BA') | (eventlist.lon > 149)]
        TR_data = TR_data[TR_data.lon>149]

    if slab == 'man':
    
        if printtest:
            lat65 = eventlist[(eventlist.etype == 'BA') & (eventlist.lon >= 120)]
            if len(lat65)>0:
                s2f.addToDataInfo(lat65, 0, 'eventlist[(eventlist.etype == BA) & (eventlist.lon >= 120)]', datainfo,'df')
        
        eventlist = eventlist[(eventlist.etype != 'BA') | ((eventlist.lon < 120)|(eventlist.lat > 15))]

    if slab == 'sum':
    
        if printtest:
            lat65 = eventlist[(eventlist.etype == 'BA') & (eventlist.lat > 21)]
            if len(lat65)>0:
                s2f.addToDataInfo(lat65, 0, 'eventlist[(eventlist.etype != BA) | (eventlist.lon > 149)]', datainfo,'df')
        
        eventlist = eventlist[(eventlist.etype != 'BA') | (eventlist.lat <= 21)]

    if slab == 'ryu':
        ryutodata = eventlist[(eventlist.etype == 'TO')&(eventlist.lon>133)]

    if slab == 'hel':
        eventlist.loc[eventlist.etype == 'RF', 'etype'] = 'CP'

    if slab == 'puyz' or slab == 'mak':
        eventlist = eventlist[eventlist.src != 'ddgap']

    # Set default uncertainties for events without uncertainties
    eventlist.loc[eventlist.etype == 'EQ', 'unc'] = 15.0
    eventlist.loc[eventlist.etype == 'CP', 'unc'] = 5.0
    eventlist.loc[eventlist.etype == 'BA', 'unc'] = 1.0
    eventlist.loc[eventlist.etype == 'TO', 'unc'] = 40.0
    eventlist.loc[(eventlist.etype == 'ER') & (eventlist.unc <5), 'unc'] = 5.0
    if slab == 'puy':
        eventlist.loc[(eventlist.etype == 'ER') & (eventlist.unc <15), 'unc'] = 15.0
    eventlist.loc[eventlist.mlon < 0, 'mlon'] += 360

    # Ensure all data are within longitudes 0-360
    eventlist.loc[eventlist.lon < 0, 'lon']+=360

    # Define mean depth of bathymetry (for constraining interp outboard trench)
    meanBAlist = eventlist[eventlist.etype == 'BA']
    meanBA = meanBAlist['depth'].mean()
    del eventlistALL
    
    ''' ----- (11) Calculate seismogenic zone thickness ------ '''

    # define seismogenic thickness parameters. change if needed
    maxdep = 65
    maxdepdiff = 20
    origorcentl = 'c'
    origorcentd = 'c'
    slaborev = 'e'
    lengthlim = -50
    
    ogcolumns = eventlist.columns
    eventlist = s2f.getReferenceKagan(slab1data, eventlist, origorcentl, origorcentd)
    if slab != 'hin':
        seismo_thick, taper_start = s2f.getSZthickness(eventlist,folder,slab,maxdep,maxdepdiff,origorcentl,origorcentd,slaborev,savedir,lengthlim)
    else:
        seismo_thick = 20
        taper_start = 20
    if slab == 'hel' or slab == 'car' or slab == 'mak':
        seismo_thick = 40
    if slab == 'sol':
        seismo_thick = 40
    if slab == 'alu' or slab == 'cot':
        seismo_thick = 10
    
    #exit()
    
    #taper = seismo_thick-taper_start
    if slab == 'sol':
        eventlistE = eventlist[eventlist.lon>148]
        eventlistW = eventlist[eventlist.lon<=148]
        eventlistE = s2f.cmtfilter(eventlistE,seismo_thick,printtest,datainfo,slab)
        eventlist = pd.concat([eventlistE,eventlistW])
    if slab == 'sum':
        eventlistS = eventlist[eventlist.lat<=22]
        eventlistN = eventlist[eventlist.lat>22]
        eventlistS = s2f.cmtfilter(eventlistS,seismo_thick,printtest,datainfo,slab)
        eventlist = pd.concat([eventlistS,eventlistN])
    if slab != 'hal' and slab != 'him' and slab != 'pam' and slab != 'hin' and slab != 'sol' and slab != 'sum' and slab != 'cas':
        eventlist = s2f.cmtfilter(eventlist,seismo_thick,printtest,datainfo,slab)

    eventlist = eventlist[ogcolumns]

    ''' ------ (12) Record variable parameters used for this model ------'''
    f = open(these_params, 'w+')
    f.write('Parameters used to create file for slab_Date_time: %s_%s_%s \n' \
            %(slab, date, time))
    f.write('\n')
    f.close()

    f = open(these_params, 'a')
    f.write('inFile: %s \n' % inFile)
    f.write('use_box: %s \n' % use_box)
    f.write('latmin: %s \n' % str(latmin))
    f.write('latmax: %s \n' % str(latmax))
    f.write('lonmin: %s \n' % str(lonmin))
    f.write('lonmax: %s \n' % str(lonmax))
    f.write('slab: %s \n' % slab)
    f.write('grid: %s \n' % str(grid))
    f.write('radius1: %s \n' % str(radius1))
    f.write('radius2: %s \n' % str(radius2))
    f.write('alen: %s \n' % str(alen))
    f.write('blen: %s \n' % str(blen))
    f.write('sdr: %s \n' % str(sdr))
    f.write('ddr: %s \n' % str(ddr))
    f.write('taper: %s \n' % str(taper))
    f.write('T: %s \n' % str(T))
    f.write('node: %s \n' % str(node))
    f.write('filt: %s \n' % str(filt))
    f.write('maxdist: %s \n' % str(maxdist))
    f.write('mindip: %s \n' % str(mindip))
    f.write('minstk: %s \n' % str(minstk))
    f.write('maxthickness: %s \n' % str(maxthickness))
    f.write('seismo_thick: %s \n' % str(seismo_thick))
    f.write('dipthresh: %s \n' % str(dipthresh))
    f.write('fracS: %s \n' % str(fracS))
    f.write('knot_no: %s \n' % str(knot_no))
    f.write('kdeg: %s \n' % str(kdeg))
    f.write('rbfs: %s \n' % str(rbfs))
    if slab == 'mue' or slab == 'phi' or slab == 'cot' or slab == 'sul' or slab == 'ryu':
        f.write('undergrid: %s \n' % str(undergrid))
    f.close()
    
    ''' ------ (13) Define search grid ------ '''

    print('    Creating search grid...')
    #Creates a grid over the slab region 

    regular_grid = s2f.create_grid_nodes3(grid, lonmin, lonmax, latmin, latmax)
    grid_in_polygon = s2f.createGridInPolygon2(regular_grid, slab, polygonFile)
    lons = grid_in_polygon[:, 0]
    lats = grid_in_polygon[:, 1]
    lons = np.round(lons,decimals=1)
    lats = np.round(lats,decimals=1)
    lons[lons <0] += 360

    slab1guide,slab1query = s2f.makeReference(slab1data,lons,lats,grid,printtest,slab)

    ''' ------ (14) Identify tomography datasets ------ '''
    ## Identify how many tomography datasets are included
    tomo_data = eventlist[eventlist.etype == 'TO']
    if len(tomo_data) > 0 and slab != 'sam':
        sources = tomo_data.src
        TOsrc = set()
        for x in sources:
            TOsrc.add(x)
        tomo_sets = TOsrc
        tomo = True
    else:
        tomo_sets = 0
        tomo = False

    premulti = pd.DataFrame()
    postmulti = pd.DataFrame()
    OGmulti = pd.DataFrame()
    elistAA = pd.DataFrame()

    loncuts,latcuts,elistcuts = s2f.getlatloncutoffs(lons,lats,eventlist,printtest)

    ''' ------ (15) Initialize arrays for Section 2 ------ '''
    # Creates list of events that were used for the model based on ID
    used_all = np.zeros((1, 2))
    used_TO = np.zeros((1, 2))

    warnings.filterwarnings('ignore', 'Mean of empty slice.')
    pd.options.mode.chained_assignment = None

    '''Section 2: First loop
    
    This Accomplishes:
    
    1) Calculate error for each used tomography model.
        This is accomplished by determining the difference between measured 
        depths for tomography and earthquake data, which will be used 
        outside of the loop.
    2) Identify data to constrain depth/coordinate of center of Benioff Zone.
    
        2a) Identify local strike, dip, and depth of Slab1.0.
            If Slab 1.0 does not exist, acquire strike from closest trench
                location with a strike oriented perpendicularly to this lon/lat.
            If extending beyond Slab1.0 depths perpendicularly, find nearest and
                most perpendicular point on Slab1.0, and define depth to
                search from based on dip and depth of that point on Slab1.0. The
                dip is defined as the dip of the local Slab1.0 point.
            If extending along strike from Slab1.0, define depth to search from 
                based on mean depth of data within defined radius of node. The
                dip of the node is defined as 0.
                
        2b) Filter by ellipsoid oriented perpendicularly to Slab1.0.
            If the local dip is less than mindip, orient ellipsoid vertically
                and along strike found in (2a).
            If the local dip is greater than mindip, orient ellipsoid 
                perpendicular to strike/dip found in (2a). 
            The long axis of the ellipse is defined as radius1, the short axis
                is defined as radius2.
            The shallow extent of the ellipsoid is defined as sdr at depths
                above seismo_thick, and is tapered to 3*sdr at depths greater
                than seismo_thick.
            The deep extent of the ellipsoid is defined as sdr at depths above
                seismo_thick, and is tapered to ddr at depths greater than 
                seismo_thick.
        
        2c) Nodes outboard of the trench are only constrained by bathymetry.
            Nodes inboard of the trench are constrained by all but bathymetry.
        
        2d) Conditionally add average active source/average reciever functions.
            If within the distance of the longest AS profile from the trench
                identify the average AS profile depth at that distance from
                trench. If there is no active source point within the search
                ellipsoid defined in (2b), add an average active source data
                point to the set of data to constrain the depth at this node.
            Reciever functions in cam and alu are being utilized similarly with
                defined distances from trench and distances along strike from
                key profiles that need to be utilized in the absence of 
                seismicity.
                
        2e) If information other than tomography is available above 300 km
                depth, all tomography is filtered at that node.
                
        2f) If less than two data points are available to constrain a node, no
                depth is resolved at that node.
                
        2g) If |strike of Slab1.0 at node - strike of Slab1.0 at farthest data|
            > minstrk, filter data at ends until < minstrk.
            If this node is outside of Slab1.0, reduce long axis of search
                ellipsoid prior to starting filters.
        
            
	The output of this loop is two numpy arrays and list of nodes with data:
	    used_TO: local difference between tomography and earthquake depths and 
            a tomography dataset identifier
	    used_all: indices for the data used and their associated nodes
            This one is created to prevent the need for re-filtering 
            in later loops
    '''

    print("Start Section 2 of 7: First loop")

    lons1, lats1, deps1, strs1, dips1, nIDs1, farpt = [], [], [], [], [], [], []
    lons1 = (np.ones(len(lons))*-9999).astype(np.float64)
    lats1 = (np.ones(len(lons))*-9999).astype(np.float64)
    deps1 = (np.ones(len(lons))*-9999).astype(np.float64)
    strs1 = (np.ones(len(lons))*-9999).astype(np.float64)
    dips1 = (np.ones(len(lons))*-9999).astype(np.float64)
    nIDs1 = (np.ones(len(lons))*-9999).astype(np.float64)
    aleng = (np.ones(len(lons))*-9999).astype(np.float64)
    bleng = (np.ones(len(lons))*-9999).astype(np.float64)
    cleng = (np.ones(len(lons))*-9999).astype(np.float64)
    
    
    if args.nCores is not None:
        if args.nCores > 1 and args.nCores < 8:
            pooling = True
        elif args.nCores == 1:
            pooling = False
        else:
            pooling = False
    else:
        pooling = False

    cutcount = 1
    allnewnodes = None
    for cut in range(len(loncuts)):
    
        theselats = latcuts[cut]
        theselons = loncuts[cut]
        theseevents = elistcuts[cut]
        indices = range(len(theselats))
        
        if cut == 0:
            i2 = 0
        
        cutcount+=1
        
        if pooling:
        
            pool1 = Pool(args.nCores)
            partial_loop1 = partial(loops.loop1, theselons, theselats, testarea, slab,
                                    depgrid, strgrid, dipgrid, slab1query, theseevents,
                                    seismo_thick, alen, blen, mdist, sdr, ddr, mindip, maxID,
                                    AA_data, TR_data, maxdist, maxthickness, minstk,
                                    tomo_sets, meanBA,slab1guide,grid,slab1data,dipthresh,datainfo,nodeinfo)

            pts = pool1.map(partial_loop1, indices) #$$#
            pool1.close()
            pool1.join()
            
            for i in range(len(indices)):
                thisnode = pts[i]
                if np.isfinite(thisnode[2]):
                
                    lons1[i2] = thisnode[0]
                    lats1[i2] = thisnode[1]
                    deps1[i2] = thisnode[2]
                    strs1[i2] = thisnode[3]
                    dips1[i2] = thisnode[4]
                    nIDs1[i2] = thisnode[5]
                    aleng[i2] = thisnode[6]
                    bleng[i2] = thisnode[7]
                    cleng[i2] = thisnode[8]

                    nused_TO = thisnode[9]
                    if len(nused_TO) > 0:
                        if used_TO is not None:
                            used_TO = np.vstack((used_TO, nused_TO))
                    nused_all = thisnode[10]
                    if len(nused_all) > 0:
                        if used_all is not None:
                            used_all = np.vstack((used_all, nused_all))
                    AAadd = thisnode[11]
                    if len(AAadd)>0:
                        if AAadd['unc'].mean() > 5:
                            AAadd['etype'] = 'RF'
                        elistAA = pd.concat([elistAA, AAadd])
                    newnodes = thisnode[12]
                    if len(newnodes)>0:
                        if allnewnodes is not None:
                            allnewnodes = np.vstack((allnewnodes,newnodes))
                        else:
                            allnewnodes = newnodes
            
                elif len(thisnode[12]) > 0:
                    newnodes = thisnode[12]
                    if len(newnodes)>0:
                        if allnewnodes is not None:
                            allnewnodes = np.vstack((allnewnodes,newnodes))
                        else:
                            allnewnodes = newnodes
        
                i2 += 1
            
        else:
        
            for nodeno in range(len(theselons)):
                alon, alat, alocdep, alocstr, alocdip, anID, aaleng, ableng, acleng, aused_TO, aused_tmp, atrimmedAA, newnodes = loops.loop1(theselons, theselats, testarea, slab, depgrid, strgrid, dipgrid, slab1query, theseevents, seismo_thick, alen, blen, mdist, sdr, ddr, mindip, maxID, AA_data, TR_data, maxdist, maxthickness, minstk, tomo_sets, meanBA, slab1guide, grid, slab1data, dipthresh, datainfo, nodeinfo, nodeno)
                
                if np.isfinite(alocdep):
                    
                    lons1[i2] = alon
                    lats1[i2] = alat
                    deps1[i2] = alocdep
                    strs1[i2] = alocstr
                    dips1[i2] = alocdip
                    nIDs1[i2] = anID
                    aleng[i2] = aaleng
                    bleng[i2] = ableng
                    cleng[i2] = acleng
                    
                    nused_TO = aused_TO
                    if len(nused_TO) > 0:
                        if used_TO is not None:
                            used_TO = np.vstack((used_TO, nused_TO))
                    nused_all = aused_tmp
                    if len(nused_all) > 0:
                        if used_all is not None:
                            used_all = np.vstack((used_all, nused_all))
                    AAadd = atrimmedAA
                    if len(AAadd)>0:
                        if AAadd['unc'].mean() > 5:
                            AAadd['etype'] = 'RF'
                        elistAA = pd.concat([elistAA, AAadd])
                    if len(newnodes)>0:
                        if allnewnodes is not None:
                            allnewnodes = np.vstack((allnewnodes,newnodes))
                        else:
                            allnewnodes = newnodes
            
                elif len(newnodes)>0:
                    if allnewnodes is not None:
                        allnewnodes = np.vstack((allnewnodes,newnodes))
                    else:
                        allnewnodes = newnodes
                
                i2 += 1
    
    lons1 = lons1[lons1>-999]
    lats1 = lats1[lats1>-999]
    deps1 = deps1[deps1>-999]
    strs1 = strs1[strs1>-999]
    dips1 = dips1[dips1>-999]
    nIDs1 = nIDs1[nIDs1>-999]
    aleng = aleng[aleng>-999]
    bleng = bleng[bleng>-999]
    cleng = cleng[cleng>-999]
    

    if allnewnodes is not None:
        theseIDs = []
        for i in range(len(allnewnodes)):
            if allnewnodes[i,1]>0:
                thisnID = int('%i%i'%(allnewnodes[i,0]*10,allnewnodes[i,1]*10))
            else:
                thisnID = int('%i0%i'%(allnewnodes[i,0]*10,allnewnodes[i,1]*-10))
            theseIDs.append(thisnID)

        newlonsdf1 = pd.DataFrame({'lon':allnewnodes[:,0],'lat':allnewnodes[:,1],'nID':theseIDs})
        newlonsdf = newlonsdf1.drop_duplicates(['nID'])
        theselons = newlonsdf['lon'].values
        theselats = newlonsdf['lat'].values

        if grid == 0.2:
            grid2 = 0.1
        elif grid == 0.1:
            grid2 = 0.05
        else:
            grid2 = grid

        slab1guide,slab1query = s2f.makeReference(slab1data,theselons,theselats,grid2,printtest,slab)
        newlats = []
        newlons = []
        newdeps = []
        newstrs = []
        newdips = []
        newnIDs = []
        newalen = []
        newblen = []
        newclen = []

        if pooling:
            indices = range(len(theselons))
            pool1 = Pool(args.nCores)
            partial_loop1 = partial(loops.loop1, theselons, theselats, testarea, slab,
                                    depgrid, strgrid, dipgrid, slab1query, eventlist,
                                    seismo_thick, alen, blen, mdist, sdr, ddr, mindip, maxID,
                                    AA_data, TR_data, maxdist, maxthickness, minstk,
                                    tomo_sets, meanBA,slab1guide,grid,slab1data,dipthresh,datainfo,nodeinfo)

            pts = pool1.map(partial_loop1, indices) #$$#
            pool1.close()
            pool1.join()
            
            for i in range(len(indices)):
                thisnode = pts[i]
                if np.isfinite(thisnode[2]):

                    newlons.append(thisnode[0])
                    newlats.append(thisnode[1])
                    newdeps.append(thisnode[2])
                    newstrs.append(thisnode[3])
                    newdips.append(thisnode[4])
                    newnIDs.append(thisnode[5])
                    newalen.append(thisnode[6])
                    newblen.append(thisnode[7])
                    newclen.append(thisnode[8])

                    nused_TO = thisnode[9]
                    if len(nused_TO) > 0:
                        if used_TO is not None:
                            used_TO = np.vstack((used_TO, nused_TO))
                    nused_all = thisnode[10]
                    if len(nused_all) > 0:
                        if used_all is not None:
                            used_all = np.vstack((used_all, nused_all))
                    AAadd = thisnode[11]
                    if len(AAadd)>0:
                        if AAadd['unc'].mean() > 5:
                            AAadd['etype'] = 'RF'
                        elistAA = pd.concat([elistAA, AAadd])

        else:
            for nodeno in range(len(theselons)):
                
                alon, alat, alocdep, alocstr, alocdip, anID, aalen, ablen, aclen, aused_TO, aused_tmp, atrimmedAA, newnodes = loops.loop1(theselons, theselats, testarea, slab, depgrid, strgrid, dipgrid, slab1query, eventlist, seismo_thick, alen, blen, mdist, sdr, ddr, mindip, maxID, AA_data, TR_data, maxdist, maxthickness, minstk, tomo_sets, meanBA, slab1guide, grid, slab1data, dipthresh, datainfo, nodeinfo, nodeno)
                
                if np.isfinite(alocdep):
                    
                    newlons.append(alon)
                    newlats.append(alat)
                    newdeps.append(alocdep)
                    newstrs.append(alocstr)
                    newdips.append(alocdip)
                    newnIDs.append(anID)
                    newalen.append(aalen)
                    newblen.append(ablen)
                    newclen.append(aclen)
                    
                    nused_TO = aused_TO
                    if len(nused_TO) > 0:
                        if used_TO is not None:
                            used_TO = np.vstack((used_TO, nused_TO))
                    nused_all = aused_tmp
                    if len(nused_all) > 0:
                        if used_all is not None:
                            used_all = np.vstack((used_all, nused_all))
                    AAadd = atrimmedAA
                    if len(AAadd)>0:
                        if AAadd['unc'].mean() > 5:
                            AAadd['etype'] = 'RF'
                        elistAA = pd.concat([elistAA, AAadd])

        #np.savetxt('%s_diptest.csv'%slab, allnewnodes, header='lon,lat,depth,strike,dip',fmt='%.2f', delimiter=',',comments='')

        if printtest:
            fig = plt.figure(figsize=(20, 10))
            ax1 = fig.add_subplot(131)
            con = ax1.scatter(lons1,lats1,c=dips1,s=10,edgecolors='none',cmap='plasma')
            ax1.set_ylabel('Latitude')
            ax1.axis('equal')
            plt.grid()
            title = 'Diptest'
            ax1.set_title(title)
            cbar = fig.colorbar(con)
            cbar.set_label('Dip')

            ax2 = fig.add_subplot(132)
            con = ax2.scatter(allnewnodes[:,0], allnewnodes[:,1],c=allnewnodes[:,1],s=10,edgecolors='none',cmap='plasma')
            ax2.set_xlabel('Longitude')
            ax2.set_ylabel('Latitude')
            ax2.axis('equal')
            plt.grid()

            cbar = fig.colorbar(con)
            cbar.set_label('Dip')
            
            ax3 = fig.add_subplot(133)
            con = ax3.scatter(newlons, newlats,c=newdips,s=10,edgecolors='none',cmap='plasma')
            ax3.set_xlabel('Longitude')
            ax3.set_ylabel('Latitude')
            ax3.axis('equal')
            plt.grid()

            cbar = fig.colorbar(con)
            cbar.set_label('Dip')

            figtitle = 'diptest.png'

            fig.savefig(figtitle)
            plt.close()

        lons1 = np.append(lons1, [newlons])
        lats1 = np.append(lats1, [newlats])
        deps1 = np.append(deps1, [newdeps])
        strs1 = np.append(strs1, [newstrs])
        dips1 = np.append(dips1, [newdips])
        nIDs1 = np.append(nIDs1, [newnIDs])
        aleng = np.append(aleng, [newalen])
        bleng = np.append(bleng, [newblen])
        cleng = np.append(cleng, [newclen])

    if global_average:
        ''' # need to fix this after adjusting based on BA depth at trench
        AA_global['depthtest'] = (AA_global['depth'].values*100).astype(int)
        for index, row in elistAA.iterrows():
            depthAA = row['depth']
            depthtestAA = int(100*row['depth'])
            thisdepth = AA_global[AA_global.depthtest == depthtestAA]
            uncAA = thisdepth['unc'].values[0]
            elistAA.loc[elistAA.depth == depthAA, 'unc'] = uncAA*2
        '''
        elistAA['unc'] = 10.0

    elistcuts.append(elistAA)
    eventlist2 = pd.concat(elistcuts)
    eventlist = eventlist2.reset_index(drop=True)
    del eventlist2
    eventlist = eventlist.drop_duplicates(['ID'])
    eventlist = eventlist.reset_index(drop=True)

    # Remove first line of zeros
    used_TO = used_TO[~np.all(used_TO ==0, axis=1)]
    used_all = used_all[~np.all(used_all ==0, axis=1)]

    '''Section 3: Calculate tomography uncertainties
	Here we use the output from the first loop to calculate tomography uncertainties.
	For each tomography dataset, we calculate the standard deviation of the distribution of "differences".
	We apply this standard deviation as the uncertainty value for each tomography datum from that dataset.
    '''
    
    print("Start Section 3 of 7: Assigning tomography uncertainties")

    if tomo:
        for idx, src in enumerate(tomo_sets):
            tomog = used_TO[:][used_TO[:, 1] == idx]
            tmp_std = np.std(tomog[:, 0])
            if tmp_std > 40.:
                tmp_std = 40.
            elif tmp_std < 15.:
                tmp_std = 15.
            elif np.isnan(tmp_std):
                tmp_std = 40
            eventlist['unc'][eventlist['src'] == src] = tmp_std
    	
    '''Section 4: Second loop
	The purpose of this loop is to determine a set of "pre-shifted" slab points that do not utilize receiver function data.
	This output dataset will represent a transition from slab surface at shallow depths to slab center at deeper depths.
	The only output from this loop is an array of the form [ lat lon dep unc nodeID ]
    '''

    print("Start Section 4 of 7: Second loop")

    bzlons, bzlats, bzdeps, stds2, nIDs2 = [], [], [], [], []
    lats2, lons2, str2, dip2, centsurf = [], [], [], [], []
    bilats, bilons, binods, bistds = [], [], [], []
    biindx, bistrs, bidips, bideps = [], [], [], []
    baleng, bbleng, bcleng, onlyto = [], [], [], []

    rlist = pd.DataFrame()
    if pooling:
        pool2 = Pool(args.nCores)
        npass = args.nCores

        partial_loop2 = partial(loops.loop2, testarea, lons1, lats1, nIDs1, deps1, strs1, dips1, used_all, eventlist, sdr, ddr, seismo_thick, slab, maxthickness, rlist, mindip, aleng, bleng, cleng)
        indices = range(len(lats1))
        pts2 = pool2.map(partial_loop2, indices)
        pool2.close()
        pool2.join()

        for i in range(len(indices)):
            thisnode = pts2[i]
            if np.isfinite(thisnode[0]):
                bzlons.append(thisnode[0])
                bzlats.append(thisnode[1])
                bzdeps.append(thisnode[2])
                stds2.append(thisnode[3])
                nIDs2.append(thisnode[4])
                lats2.append(thisnode[5])
                lons2.append(thisnode[6])
                str2.append(thisnode[7])
                dip2.append(thisnode[8])
                centsurf.append(thisnode[9])
                baleng.append(thisnode[20])
                bbleng.append(thisnode[21])
                bcleng.append(thisnode[22])
                onlyto.append(thisnode[23])
            if np.isfinite(thisnode[10]):
                bilats.append(thisnode[10])
                bilons.append(thisnode[11])
                binods.append(thisnode[12])
                bistds.append(thisnode[13])
                biindx.append(thisnode[14])
                bistrs.append(thisnode[15])
                bidips.append(thisnode[16])
                bideps.append(thisnode[17])
            rlist = thisnode[18]
            if len(rlist) > 0:
                removeIDs = np.array(rlist.ID)
                thisID = np.ones(len(removeIDs))*thisnode[4]
                removearray = list(zip(thisID, removeIDs))
                removeIDID = np.array(removearray)
                used_all = used_all[~(np.in1d(used_all[:, 1], removeIDID) & np.in1d(used_all[:, 0], thisID))]
            multi = thisnode[19]
            if len(multi) > 0:
                premulti = pd.concat([premulti, multi])

        del pts2
        
    else:
        npass = 1
        for nodeno in range(len(lats1)):
            bpeak_lon, bpeak_lat, bpeak_depth, bstd, bnID, blat, blon, bcstr, bcdip, bcentsurf, bbilats, bbilons, bbinods, bbistds, bbiindx, bbistrs, bbidips, bbideps, brlist, bpremulti, alen, blen, clen, onlyt = loops.loop2(testarea, lons1, lats1, nIDs1, deps1, strs1, dips1, used_all, eventlist, sdr, ddr, seismo_thick, slab, maxthickness, rlist, mindip, aleng, bleng, cleng, nodeno)
            if np.isfinite(bpeak_lon):
                bzlons.append(bpeak_lon)
                bzlats.append(bpeak_lat)
                bzdeps.append(bpeak_depth)
                stds2.append(bstd)
                nIDs2.append(bnID)
                lats2.append(blat)
                lons2.append(blon)
                str2.append(bcstr)
                dip2.append(bcdip)
                centsurf.append(bcentsurf)
                baleng.append(alen)
                bbleng.append(blen)
                bcleng.append(clen)
                onlyto.append(onlyt)
            if np.isfinite(bbilats):
                bilats.append(bbilats)
                bilons.append(bbilons)
                binods.append(bbinods)
                bistds.append(bbistds)
                biindx.append(bbiindx)
                bistrs.append(bbistrs)
                bidips.append(bbidips)
                bideps.append(bbideps)
            rlist = brlist
            if len(rlist) > 0:
                removeIDs = np.array(rlist.ID)
                thisID = np.ones(len(removeIDs))*bnID
                removearray = list(zip(thisID, removeIDs))
                removeIDID = np.array(removearray)
                used_all = used_all[~(np.in1d(used_all[:, 1], removeIDID) & np.in1d(used_all[:, 0], thisID))]
            multi = bpremulti
            if len(multi) > 0:
                premulti = pd.concat([premulti, multi])


    tmp_res = pd.DataFrame({'bzlon':bzlons,'bzlat':bzlats,'depth':bzdeps,'stdv':stds2,'nID':nIDs2,'lat':lats2,'lon':lons2,'ogstr':str2,'ogdip':dip2,'centsurf':centsurf,'alen':baleng,'blen':bbleng,'clen':bcleng,'onlyto':onlyto})

    for j in range(len(bilats)):
        lon = bilons[j]
        lat = bilats[j]
        nID = binods[j]
        stdv = bistds[j]
        stk = bistrs[j]
        dep = bideps[j]
        dip = bidips[j]
        
        if dip <= mindip:
            peak_depth = s2f.findMultiDepth(lon, lat, nID, tmp_res, grid, premulti, stk, slab, dep, alen, printtest)
            peak_lon = lon
            peak_lat = lat
        else:
            peak_lon, peak_lat, peak_depth = s2f.findMultiDepthP(lon, lat, nID, tmp_res, grid, premulti, stk, slab, dep, dip, alen, printtest)

        tmp_res.loc[tmp_res.nID == nID, 'bzlon'] = peak_lon
        tmp_res.loc[tmp_res.nID == nID, 'bzlat'] = peak_lat
        tmp_res.loc[tmp_res.nID == nID, 'depth'] = peak_depth

    tmp_res = s2f.addGuidePoints(tmp_res, slab)

    if slab == 'sol':
        tmp_res = tmp_res[(tmp_res.bzlon>142) & (tmp_res.bzlon<164)]
    
    if slab == 'sul':
        tmp_res = tmp_res[(tmp_res.bzlon<123.186518923) | (tmp_res.depth<100)]
        tmp_res = tmp_res[(tmp_res.bzlon<122.186518923) | (tmp_res.depth<200)]

    # Save data used to file
    used_IDs = used_all[:, 1]
    used_data = eventlist[eventlist['ID'].isin(used_IDs)]
    used_data = used_data[['lat', 'lon', 'depth', 'unc', 'etype', 'ID', 'mag', 'time', 'S1', 'D1', 'R1', 'S2', 'D2', 'R2', 'src']]
    used_data = used_data.drop_duplicates(['ID'])
    used_data.loc[used_data.lon < 0, 'lon']+=360
    if slab == 'hel':
        used_data.loc[used_data.etype == 'CP', 'etype']='RF'
    used_data.to_csv(dataFile, header=True, index=False, float_format='%0.2f', na_rep = float('nan'), chunksize=100000)
    #tmp_res.to_csv('nodetest.csv', header=True, index=False, float_format='%0.2f', na_rep = float('nan'), chunksize=100000)

    '''Section 5: Calculate shifts
	Here we use the output of the second loop to calculate shifting locations for non-RF results.
	The shift is calculated using the 1/2 of the thickness of the plate, as calculated using the nearest oceanic plate age.
	Shift direction is determined by the strike and dip of a surface created using the output from the second loop.
	A clipping mask is also created in this section using the shifted output data.
    '''

    print("Start Section 5 of 7: Calculate shifts")
    # Calculate shift for each node
    print("    Calculating shift...")

    surfnode = 0.5
    data0 = tmp_res[(tmp_res.stdv > -0.000001)&(tmp_res.stdv < 0.000001)]
    tmp_res = tmp_res[(tmp_res.stdv < -0.000001)|(tmp_res.stdv > 0.000001)]

    if use_box == 'yes':
        if lonmin<0:
            lonmin+=360
        if lonmax<0:
            lonmax+=360
        TR_data = TR_data[(TR_data.lon<lonmax)&(TR_data.lon>lonmin)]
        TR_data = TR_data[(TR_data.lat<latmax)&(TR_data.lat>latmin)]
        TR_data = TR_data.reset_index(drop=True)

    # Read in age grid files
    ages = gmt.GMTGrid.load(agesFile)
    ages_error = gmt.GMTGrid.load(ageerrorsFile)

    shift_out, maxthickness = s2f.slabShift_noGMT(tmp_res, node, T, TR_data, seismo_thick, taper, ages, ages_error, filt, slab, maxthickness, grid, 'bzlon', 'bzlat', 'depth', fracS, npass, meanBA, printtest, kdeg, knot_no, rbfs, use_box)
    del ages
    del ages_error

    tmp_res['pslon'] = tmp_res['lon'].values*1.0
    tmp_res['pslat'] = tmp_res['lat'].values*1.0
    tmp_res['psdepth'] = tmp_res['depth'].values*1.0
    tmp_res = tmp_res[['pslon', 'pslat', 'bzlon', 'bzlat', 'psdepth', 'stdv', 'nID', 'ogstr', 'ogdip', 'centsurf', 'alen', 'blen', 'clen']]
    shift_out = shift_out.merge(tmp_res)
    shift_out.loc[shift_out.pslon < 0, 'pslon']+=360
    shift_out['avstr'] = np.nan
    shift_out['avdip'] = np.nan
    shift_out['avrke'] = np.nan

    '''Section 6: Third loop
	The purpose of this loop is to produce the final location measurements for the slab.
	Here we edit the input data by adding the shift to the depths, then calculate a PDF with receiver functions included.
	The only output from this loop is a 10 column array with all results necessary to build the output.
	Output is of the format [ lat lon dep unc shift_mag shift_unc avg_str avg_dip avg_rak pre-shift_dep pre-shift_str pre-shift_dip nodeID ] 
    '''
    print("Start Section 6 of 7: Third (final) loop")

        
    bilats, bilons, binods, bistds = [], [], [], []
    biindx, bistrs, bidips, bideps = [], [], [], []

    if pooling:
        pool3 = Pool(args.nCores)
        partial_loop3 = partial(loops.loop3, shift_out, testarea, used_all, eventlist, sdr, ddr, seismo_thick, these_params, slab, maxthickness, mindip, taper)
        indices = shift_out['nID'].values
        pts3 = pool3.map(partial_loop3, indices)
        pool3.close()
        pool3.join()
        
        for i in range(len(indices)):
            thisnode = pts3[i]
            if np.isfinite(thisnode[0]):
                nID = thisnode[13]
                shift_out.loc[shift_out.nID == nID, 'depth'] = thisnode[0]
                shift_out.loc[shift_out.nID == nID, 'stdv'] = thisnode[1]
                shift_out.loc[shift_out.nID == nID, 'avstr'] = thisnode[2]
                shift_out.loc[shift_out.nID == nID, 'avdip'] = thisnode[3]
                shift_out.loc[shift_out.nID == nID, 'avrke'] = thisnode[4]
                shift_out.loc[shift_out.nID == nID, 'lon'] = thisnode[15]
                shift_out.loc[shift_out.nID == nID, 'lat'] = thisnode[16]
            if np.isfinite(thisnode[5]):
                bilats.append(thisnode[5])
                bilons.append(thisnode[6])
                binods.append(thisnode[7])
                bistds.append(thisnode[8])
                biindx.append(thisnode[9])
                bistrs.append(thisnode[10])
                bidips.append(thisnode[11])
                bideps.append(thisnode[12])
            multi = thisnode[14]
            if len(multi) > 0:
                postmulti = pd.concat([postmulti, multi])

        del pts3
        
    else:
        for nodeno in shift_out['nID'].values:
            crdepth, crstd, crstrike, crdip, crrake, cbilats, cbilons, cbinods, cbistds, cbiindx, cbistrs, cbidips, cbideps, cnID, cpostmulti, cpeak_lon, cpeak_lat = loops.loop3(shift_out, testarea, used_all, eventlist, sdr, ddr, seismo_thick, these_params, slab, maxthickness, mindip, taper, nodeno)
            if np.isfinite(crdepth):
                nID = cnID
                shift_out.loc[shift_out.nID == nID, 'depth'] = crdepth
                shift_out.loc[shift_out.nID == nID, 'stdv'] = crstd
                shift_out.loc[shift_out.nID == nID, 'avstr'] = crstrike
                shift_out.loc[shift_out.nID == nID, 'avdip'] = crdip
                shift_out.loc[shift_out.nID == nID, 'avrke'] = crrake
                shift_out.loc[shift_out.nID == nID, 'lon'] = cpeak_lon
                shift_out.loc[shift_out.nID == nID, 'lat'] = cpeak_lat
            if np.isfinite(cbilats):
                bilats.append(cbilats)
                bilons.append(cbilons)
                binods.append(cbinods)
                bistds.append(cbistds)
                biindx.append(cbiindx)
                bistrs.append(cbistrs)
                bidips.append(cbidips)
                bideps.append(cbideps)
            multi = cpostmulti
            if len(multi) > 0:
                postmulti = pd.concat([postmulti, multi])
        
    shift_out.loc[shift_out.lon < 0, 'lon']+=360
    
    for j in range(len(bilats)):
        lon = bilons[j]
        lat = bilats[j]
        nID = binods[j]
        stdv = bistds[j]
        stk = bistrs[j]
        dep = bideps[j]
        dip = bidips[j]
        
        if dip <= mindip:
            peak_depth = s2f.findMultiDepth(lon, lat, nID, shift_out, grid, postmulti, stk, slab, dep, alen, printtest)
            peak_lon = lon
            peak_lat = lat
        else:
            peak_lon, peak_lat, peak_depth = s2f.findMultiDepthP(lon, lat, nID, shift_out, grid, postmulti, stk, slab, dep, dip, alen, printtest)

        shift_out.loc[shift_out.nID == nID, 'lon'] = peak_lon
        shift_out.loc[shift_out.nID == nID, 'lat'] = peak_lat
        shift_out.loc[shift_out.nID == nID, 'depth'] = peak_depth

    # Save nodes to file
    shift_out.loc[shift_out.lon < 0, 'lon']+=360
    dip90s = 90.0-shift_out['ogdip'].values
    vertunc = shift_out['stdv'].values * (np.sin(np.radians(dip90s)))
    horzunc = shift_out['stdv'].values * (np.cos(np.radians(dip90s)))
    shift_out['vstdv'] = vertunc
    shift_out['hstdv'] = horzunc
    
    if slab != 'sol' and slab != 'phi' and slab != 'sul' and slab != 'alu' and slab != 'sum':
        shift_out, rempts = s2f.removeSZnodes(shift_out, fracS, 0.1, seismo_thick)
        rempts = rempts[['lon', 'lat', 'depth', 'stdv', 'smag', 'shiftstd', 'avstr', 'avdip', 'avrke', 'psdepth', 'sstr', 'sdip', 'nID', 'pslon', 'pslat', 'bzlon', 'bzlat', 'centsurf','thickness', 'alen', 'blen', 'clen', 'ogstr', 'ogdip','hstdv','vstdv']]
        rempts.to_csv(rempFile, header=True, index=False, na_rep=np.nan, float_format='%.2f')
    elif slab == 'sum' or slab == 'kur':
        shift_out, rempts = s2f.removeSZnodes(shift_out, fracS, 0.4, seismo_thick)
        rempts = rempts[['lon', 'lat', 'depth', 'stdv', 'smag', 'shiftstd', 'avstr', 'avdip', 'avrke', 'psdepth', 'sstr', 'sdip', 'nID', 'pslon', 'pslat', 'bzlon', 'bzlat', 'centsurf','thickness', 'alen', 'blen', 'clen', 'ogstr', 'ogdip','hstdv','vstdv']]
        rempts.to_csv(rempFile, header=True, index=False, na_rep=np.nan, float_format='%.2f')
    
    shift_out = shift_out[['lon', 'lat', 'depth', 'stdv', 'smag', 'shiftstd', 'avstr', 'avdip', 'avrke', 'psdepth', 'sstr', 'sdip', 'nID', 'pslon', 'pslat', 'bzlon', 'bzlat', 'centsurf','thickness', 'alen', 'blen', 'clen', 'ogstr', 'ogdip','hstdv','vstdv']]
    shift_out.to_csv(nodeFile, header=True, index=False, na_rep=np.nan, float_format='%.2f')


    if slab == 'manz' or slab == 'solz' or slab == 'phiz':
        lowernodes, shift_out = s2f.nodesift(shift_out, grid)
    
    if slab == 'izuz':
        midshiftout = shift_out[(shift_out.lat > 15)&(shift_out.lat < 28)]
        outshiftout = shift_out[(shift_out.lat <= 15)|(shift_out.lat >= 28)]
        midshiftout = midshiftout[midshiftout.depth<300]
        shift_out = pd.concat([midshiftout,outshiftout])
    
    if slab == 'solz' or slab == 'sumz':
        nodesOG, projnodes = s2f.extendEdges(shift_out,grid,slab)
        shift_out = pd.concat([projnodes, shift_out])
        
    '''Section 7: Create output
    Here we put together all of the output data into the correct form for saving to output files.
    First we create a surface with fine spacing of the final data, then we filter it and apply the clipping mask.
    Second we populate the output array, and finally we save it.
    The output file is of the format [ lon lat dep_raw str_raw dip_raw shift_mag dep_shift dep_shift_smooth str_shift_smooth dip_shift_smooth dz1 dz2 dz3 avg_str avg_dip avg_rak ]
        This file has a regular spacing of fine nodes corresponding to the final surface
        The columns for shift_mag, avg_str, avg_dip, and avg_rak are only populated where there was a pre-shift datum.
    '''
    print("Start Section 7 of 7: Create output")

    # Create final surfaces for output
    print("    Creating surfaces...")

    shift_out = shift_out[(shift_out.nID != 2642178)& (shift_out.nID != 2646182)& (shift_out.nID != 2646184)& (shift_out.nID != 2646186)& (shift_out.nID != 1454068)& (shift_out.nID != 1122062)& (shift_out.nID != 1123062)&(shift_out.nID !=1454068)& (shift_out.nID != 16790448) & (shift_out.nID != 16790449)]
    if slab == 'man':
        shift_out = shift_out[(shift_out.bzlat > 13.5)|(shift_out.bzlon < 121)]
    surfdata = np.zeros((len(shift_out), 4))
    surfdata[:, 0], surfdata[:, 1], surfdata[:, 2], surfdata[:, 3] = shift_out['lon'].values, shift_out['lat'].values, shift_out['depth'].values, shift_out['stdv'].values
    
    errordata = np.zeros((len(shift_out), 4))
    errordata[:, 0], errordata[:, 1], errordata[:, 2], errordata[:, 3] = shift_out['lon'].values, shift_out['lat'].values, shift_out['stdv'].values, np.ones(len(shift_out))
    
    errordataB = np.zeros((len(shift_out), 4))
    errordataB[:, 0], errordataB[:, 1], errordataB[:, 2], errordataB[:, 3] = shift_out['lon'].values, shift_out['lat'].values, shift_out['shiftstd'].values, np.ones(len(shift_out))
    
    thickdata = np.zeros((len(shift_out),4))
    thickdata[:, 0], thickdata[:, 1], thickdata[:, 2], thickdata[:, 3] = shift_out['lon'].values, shift_out['lat'].values, shift_out['thickness'].values, np.ones(len(shift_out))

    if slab == 'sum':
        Surfgrid, xi, dl = s2f.chunksurface(surfdata, node, T, slab, grid, 'depth', time, 'test.txt', filt, pd.DataFrame(), npass, TR_data, meanBA, kdeg, knot_no, rbfs, shift_out,'fin','og','lon',100,110,105)
        flipornot = 'flip'
    elif slab == 'jap':
        Surfgrid, xi, dl = s2f.chunksurface(surfdata, node, T, slab, grid, 'depth', time, 'test.txt', filt, pd.DataFrame(), npass, TR_data, meanBA, kdeg, knot_no, rbfs, shift_out,'fin','og','lat',30,40,35)
        flipornot = 'flip'
    else:
        Surfgrid, xi, dl = s2f.pySurface3(surfdata, node, T, slab, grid, 'depth', time, 'test.txt', filt, pd.DataFrame(), npass, TR_data, meanBA, kdeg, knot_no, rbfs, shift_out,'fin','og')
        flipornot = 'dontflip'
    
    #{‘reflect’, ‘constant’, ‘nearest’, ‘mirror’, ‘wrap’}
    sigma = (filt/2.0) / node

    Errorgrid = s2f.makeErrorgrid(Surfgrid, xi, errordata)
    Errorgrid2 = s2f.makeErrorgrid(Surfgrid, xi, errordataB)
    thickgrid = s2f.makeErrorgrid(Surfgrid, xi, thickdata)

    if slab == 'puy':
        filt2 = 0.6
        Filtgrid = s2f.specialpuyfilt(Surfgrid,xi,filt,filt2,node)
        Errorgrid = s2f.specialpuyfilt(Errorgrid,xi,filt,filt2,node)
        Errorgrid2 = s2f.specialpuyfilt(Errorgrid2,xi,filt,filt2,node)
        thickgrid = s2f.specialpuyfilt(thickgrid,xi,filt,filt2,node)
    elif slab == 'kur':
        filt2 = 1.5
        Filtgrid = s2f.specialkurfilt(Surfgrid,xi,filt,filt2,node)
        Errorgrid = s2f.specialkurfilt(Errorgrid,xi,filt,filt2,node)
        Errorgrid2 = s2f.specialkurfilt(Errorgrid2,xi,filt,filt2,node)
        thickgrid = s2f.specialkurfilt(thickgrid,xi,filt,filt2,node)
    elif slab == 'izu':
        filt2 = 1.5
        Filtgrid = s2f.specializufilt(Surfgrid,xi,filt,filt2,node)
        Errorgrid = s2f.specializufilt(Errorgrid,xi,filt,filt2,node)
        Errorgrid2 = s2f.specializufilt(Errorgrid2,xi,filt,filt2,node)
        thickgrid = s2f.specializufilt(thickgrid,xi,filt,filt2,node)
    else:
        Filtgrid = ndimage.filters.gaussian_filter(Surfgrid, sigma, mode='reflect')
        Errorgrid = ndimage.filters.gaussian_filter(Errorgrid, sigma, mode='reflect')
        Errorgrid2 = ndimage.filters.gaussian_filter(Errorgrid2, sigma, mode='reflect')
        thickgrid = ndimage.filters.gaussian_filter(thickgrid, sigma, mode='reflect')

    strgrid3, dipgrid3 = s2f.mkSDgrddata(xi, Filtgrid, flipornot)

    resdata = np.zeros((len(xi),5))
    resdata[:,0] = xi[:,0]
    resdata[:,1] = xi[:,1]

    resdata[:,2] = Filtgrid.flatten()
    resdata[:,3] = strgrid3.flatten()
    resdata[:,4] = dipgrid3.flatten()

    print("    Identifying contour extents for clipping mask...")
    newres = s2f.mkContourClip(shift_out, TR_data, node, resdata, False,slab)
    print("    Assigning and sorting clipping mask polygon...")
    if len(TR_data)>0:
        clip = s2f.clippingmask(newres,TR_data,node,False,slab,'first')
    else:
        clip = s2f.noTrenchPolygon(newres, node, False, slab)

    mask = s2f.maskdatag(clip, xi)
    mask.shape = Surfgrid.shape

    Filtgrid = (Filtgrid*mask)
    Surfgrid = (Surfgrid*mask)
    Errorgrid = (Errorgrid*mask)
    Errorgrid2 = (Errorgrid2*mask)
    thickgrid = (thickgrid*mask)
    dipgrid3 = (dipgrid3*mask)
    strgrid3 = (strgrid3*mask)
    smooth_dif = Surfgrid.flatten()-Filtgrid.flatten()

    # Create output array
    print("    Populating output array...")

    output = (np.zeros([len(xi), 10]) * np.nan)

    output[:, 0] = xi[:, 0]  # lon Longitude at node (not shifted)
    output[:, 1] = xi[:, 1]  # lat Latitude at node
    output[:, 2] = Surfgrid.flatten()  # dep_shift Post-shift surface depth before smoothing
    output[:, 3] = Filtgrid.flatten()  # dep_shift_smooth Post-shift surface depth after smoothing
    output[:, 4] = strgrid3.flatten() # str_shift_smooth Post-shift surface strike after smoothing (strike was not smoothed - only depth was smoothed)
    output[:, 5] = dipgrid3.flatten()  # dip_shift_smooth Post-shift surface dip after smoothing
    output[:, 6] = Errorgrid.flatten() # dz1 Interpolated, but unsmoothed uncertainty from raw data
    output[:, 7] = Errorgrid2.flatten()  #dz2 Interpolated, unsmoothed uncertainty from shift
    output[:, 8] = smooth_dif.flatten() # dz3 error induced by smoothing (taken as the standard deviation of smoothed-unsmoothed)
    output[:, 9] = thickgrid.flatten()  #dz2 Interpolated, unsmoothed thickness
    output[:, 0][output[:, 0]<0]+=360

    clip.loc[clip.lon < 0, 'lon']+=360
    
    output[:,2][output[:,3] > shift_out['depth'].max()] = np.nan
    output[:,3][output[:,3] > shift_out['depth'].max()] = np.nan
    output[:,4][output[:,3] > shift_out['depth'].max()] = np.nan
    output[:,5][output[:,3] > shift_out['depth'].max()] = np.nan
    output[:,6][output[:,3] > shift_out['depth'].max()] = np.nan
    output[:,7][output[:,3] > shift_out['depth'].max()] = np.nan
    output[:,8][output[:,3] > shift_out['depth'].max()] = np.nan
    output[:,9][output[:,3] > shift_out['depth'].max()] = np.nan

    if slab == 'phi' or slab == 'sul' or slab == 'cot':

        halfolder = 'hal_slab2_12.22.17'
        print ('clipping grid by underriding model: %s ... '%undergrid)
        output = s2f.underclip(output,undergrid)
        finoutput = output[np.isfinite(output[:,3])]
        newres = pd.DataFrame({'lon':finoutput[:,0], 'lat':finoutput[:,1], 'depth':finoutput[:,3], 'strike':finoutput[:,4], 'dip':finoutput[:,5]})
        clip = s2f.clippingmask(newres,TR_data,node,False,slab,'first')
    
    if slab == 'ryu':
    
        kurfolder = 'kur_slab2_12.22.17'
        print ('clipping grid by underriding model: %s ... '%undergrid)
        output = s2f.underclip(output,undergrid)
        finoutput = output[np.isfinite(output[:,3])]
        newres = pd.DataFrame({'lon':finoutput[:,0], 'lat':finoutput[:,1], 'depth':finoutput[:,3], 'strike':finoutput[:,4], 'dip':finoutput[:,5]})
        clip = s2f.clippingmask(newres,TR_data,node,False,slab,'first')

    if slab == 'mue':
    
        carfolder = 'car_slab2_12.22.17'
        print ('clipping grid by underriding model: %s ... '%undergrid)
        output = s2f.underclip(output,undergrid)
        finoutput = output[np.isfinite(output[:,3])]
        newres = pd.DataFrame({'lon':finoutput[:,0], 'lat':finoutput[:,1], 'depth':finoutput[:,3], 'strike':finoutput[:,4], 'dip':finoutput[:,5]})
        clip = s2f.clippingmask(newres,TR_data,node,False,slab,'first')

    if slab == 'kur':
        output = output[output[:,1] >= 35]
        clip = clip[clip.lat >= 35]
        clip['dist1'] = np.abs(35-clip['lat'].values)
        closest = clip[clip.dist1 == clip['dist1'].min()]
        lonc, latc = closest['lon'].values[0], closest['lat'].values[0]
        clip['dist2'] = np.abs(lonc-clip['lon'].values)
        clip['dist3'] = clip['dist1'].values/clip['dist2'].values/clip['dist2'].values
        closest2 = clip[clip.dist3 == clip['dist3'].min()]
        lonc2, latc2 = closest2['lon'].values[0], closest2['lat'].values[0]
        clip.loc[(clip.lon == lonc)&(clip.lat == latc), 'lat'] = 35.0
        clip.loc[(clip.lon == lonc2)&(clip.lat == latc2), 'lat'] = 35.0
        if clip['lon'].values[0] != clip['lon'].values[-1] or clip['lat'].values[0] != clip['lat'].values[-1]:
            pointbeg = clip.iloc[[0]]
            clip = pd.concat([clip, pointbeg])
            clip = clip[['lon','lat']]
    
    # Save results to file
    print("    Saving results and data to file...")
    np.savetxt(outFile, output, header='lon,lat,raw_dep,dep_shift_smooth,str_shift_smooth,dip_shift_smooth,dz1,dz2,dz3,thickness',fmt='%.2f', delimiter=',',comments='')

    # Save clipping mask to file
    clip = clip[['lon', 'lat']]
    clip.to_csv(clipFile, float_format='%.2f', sep=' ', header=False, index=False)
    
    if slab == 'izu' or slab == 'jap' or slab == 'sol' or slab == 'man' or slab == 'ker' or slab == 'hinz' or slab == 'pamz':
        print("    PSYCH! Solving for vertical component of this slab region ...")
        clip, output, supplement, nodes, deepnodes = s2f.splitsurface(nodeFile,outFile,clipFile,trenches,node,filt,grid,slab, knot_no, kdeg, rbfs, folder)
        supplement = supplement[['lon','lat','depth','strike','dip','dz1','dz2','dz3','thickness']]
        nodes.to_csv(nodeuFile, header=True, index=False, na_rep=np.nan, float_format='%.2f')
        deepnodes.to_csv(nodexFile, header=True, index=False, na_rep=np.nan, float_format='%.2f')
        supplement.to_csv(suppFile, header=True, index=False, na_rep=np.nan, float_format='%.2f')
        if slab == 'izu':
            output = output[output[:,1] <= 35]
            clip = clip[clip.lat <= 35]
            clip['dist1'] = np.abs(35-clip['lat'].values)
            closest = clip[clip.dist1 == clip['dist1'].min()]
            lonc, latc = closest['lon'].values[0], closest['lat'].values[0]
            clip['dist2'] = np.abs(lonc-clip['lon'].values)
            clip['dist3'] = clip['dist1'].values/clip['dist2'].values/clip['dist2'].values
            closest2 = clip[clip.dist3 == clip['dist3'].min()]
            lonc2, latc2 = closest2['lon'].values[0], closest2['lat'].values[0]
            clip.loc[(clip.lon == lonc)&(clip.lat == latc), 'lat'] = 35.0
            clip.loc[(clip.lon == lonc2)&(clip.lat == latc2), 'lat'] = 35.0
            if clip['lon'].values[0] != clip['lon'].values[-1] or clip['lat'].values[0] != clip['lat'].values[-1]:
                pointbeg = clip.iloc[[0]]
                clip = pd.concat([clip, pointbeg])
                clip = clip[['lon','lat']]

        print("    Saving results and data to file...")
        clip = clip[['lon', 'lat']]
        clip.to_csv(clipFile, float_format='%.2f', sep=' ', header=False, index=False)
        np.savetxt(outFile, output, header='lon,lat,raw_dep,dep_shift_smooth,str_shift_smooth,dip_shift_smooth,dz1,dz2,dz3,thickness',fmt='%.2f', delimiter=',',comments='')

    xmin = np.min(output[:,0])
    xmax = np.max(output[:,0])
    ymin = np.min(output[:,1])
    ymax = np.max(output[:,1])
    
    deps = pd.DataFrame({'lon':output[:,0], 'lat': output[:,1], 'depth':output[:,3]*-1.0})
    strs = pd.DataFrame({'lon':output[:,0], 'lat': output[:,1], 'str':output[:,4]})
    dips = pd.DataFrame({'lon':output[:,0], 'lat': output[:,1], 'dip':output[:,5]})
    uncs = pd.DataFrame({'lon':output[:,0], 'lat': output[:,1], 'unc':output[:,6]})
    thicks = pd.DataFrame({'lon':output[:,0], 'lat': output[:,1], 'thick':output[:,9]})
    
    deps = deps[['lon','lat','depth']]
    strs = strs[['lon','lat','str']]
    dips = dips[['lon','lat','dip']]
    uncs = uncs[['lon','lat','unc']]
    thicks = thicks[['lon','lat','thick']]
    
    deps.to_csv(depTextFile, header=False, index=False, sep=' ', na_rep=np.nan)
    strs.to_csv(strTextFile, header=False, index=False, sep=' ', na_rep=np.nan)
    dips.to_csv(dipTextFile, header=False, index=False, sep=' ', na_rep=np.nan)
    uncs.to_csv(uncTextFile, header=False, index=False, sep=' ', na_rep=np.nan)
    thicks.to_csv(thickTextFile, header=False, index=False, sep=' ', na_rep=np.nan)
    
    rflag="-R%s/%s/%s/%s" %(np.floor(xmin),np.ceil(xmax),np.floor(ymin),np.ceil(ymax))
    iflag="-I%s/%s" %(node,node)
    
    gflag="-G%s" % (depGridFile)
    os.system("gmt xyz2grd %s %s %s %s" % (depTextFile,rflag,iflag,gflag))
    gflag="-G%s" % (strGridFile)
    os.system("gmt xyz2grd %s %s %s %s" % (strTextFile,rflag,iflag,gflag))
    gflag="-G%s" % (dipGridFile)
    os.system("gmt xyz2grd %s %s %s %s" % (dipTextFile,rflag,iflag,gflag))
    gflag="-G%s" % (uncGridFile)
    os.system("gmt xyz2grd %s %s %s %s" % (uncTextFile,rflag,iflag,gflag))
    gflag="-G%s" % (thickGridFile)
    os.system("gmt xyz2grd %s %s %s %s" % (thickTextFile,rflag,iflag,gflag))

    os.system("rm %s" % depTextFile)
    os.system("rm %s" % strTextFile)
    os.system("rm %s" % dipTextFile)
    os.system("rm %s" % uncTextFile)
    os.system("rm %s" % thickTextFile)

    if slab == 'izu' or slab == 'jap' or slab == 'sol' or slab == 'man' or slab == 'ker' or slab == 'hinz' or slab == 'pamz':
    
        os.system("rm Output/%s/%s_slab2_con_%s.txt"%(folder,slab,date))
        contourlist = np.arange(100,700,20)
        with open('Output/%s/%s_slab2_con_%s.txt'%(folder,slab,date),'a') as f:
            for c in contourlist:
                dat = supplement[(supplement.depth < c+0.03)&(supplement.depth > c-0.03)]
                if len(dat) < 1:
                    dat = supplement[(supplement.depth < c+1)&(supplement.depth > c-1)]
                if len(dat) > 0:
                    if slab == 'izu' or slab == 'man' or slab == 'ker':
                        dat = dat.sort_values(by=['lat'], ascending=False)
                    if slab == 'sol' or slab == 'hin' or slab == 'pam':
                        dat = dat.sort_values(by=['lon'], ascending=False)
                    f.write('> %i \n'%c)
                    dat = dat[['lon','lat']]
                    dat.to_csv(f,header=False,index=False,sep=' ')
        f.close()
        

    print(" All files have been saved in directory: %s/Output/%s"%(os.getcwd(),folder))
    print(" File descriptions:")
    print("       %s_slab2_res_%s.csv:    ascii format of output grids listed below"%(slab,date))
    print("       %s_slab2_dep_%s.grd:    depth grid (res columns: lon,lat,dep_shift_smooth)"%(slab,date))
    print("       %s_slab2_str_%s.grd:    strike grid (res columns: lon,lat,str_shift_smooth)"%(slab,date))
    print("       %s_slab2_dip_%s.grd:    dip grid (res columns: lon,lat,dip_shift_smooth)"%(slab,date))
    print("       %s_slab2_thk_%s.grd:    uncertainty grid (res columns: lon,lat,dz1)"%(slab,date))
    print("       %s_slab2_unc_%s.grd:    thickness grid (res columns: lon,lat,thickness)"%(slab,date))
    
    print("       %s_slab2_nod_%s.csv:    info for all grid nodes constraining final surface "%(slab,date))
    print("       %s_slab2_dat_%s.csv:    filtered input dataset "%(slab,date))
    print("       %s_slab2_clp_%s.csv:    clipping mask "%(slab,date))
    print("       %s_slab2_par_%s.csv:    list of parameters used in this model "%(slab,date))
    print("       %s_slab2_szt_%s.csv:    file listing events used to determine seismogenic width "%(slab,date))
    print("       %s_slab2_szt_%s.png:    depth histogram and PDF of slab related events  "%(slab,date))
            
# Help/description and command line argument parser
if __name__=='__main__':
    desc = '''
        Expected slab regions include: 
            Alaska-Aleutians         > alu
            Central America          > mex
            Cascadia                 > cas
            Izu-Bonin                > izu
            Kermadec-Tonga           > ker
            Kamchatka/Kurils/Japan   > kur
            Philippines              > phi
            Ryukyu                   > ryu
            Santa Cruz Islands       > van
            Scotia                   > sco
            Solomon Islands          > sol
            South America            > sam
            Sumatra-Java             > sum
        '''
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('-p', '--parFile', dest='parFile', type=str,
                        required=True, help='file listing slab parameters')
    parser.add_argument('-c', '--nCores', dest='nCores', type=int,
                        help='number of cores to run with')
    parser.add_argument('-t', '--test', metavar=('lonmin', 'lonmax',
                                                'latmin', 'latmax'),
                        dest='test', type=float, nargs=4,
                        help='test box [lonmin lonmax latmin latmax]')
    parser.add_argument('-u', '--undergrid', dest='undergrid', type=str,
                        help='depth grid for slab abutting this one, required for ryu (kur grid), mue (car grid), phi, sul, cot (hal grid)')
    pargs = parser.parse_args()
    
    #cProfile.run('main(pargs)')
    main(pargs)
