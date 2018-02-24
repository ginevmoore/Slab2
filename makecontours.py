import pandas as pd
import numpy as np
import os
import argparse

def main(args):

    folderdir = args.folderdir
    slab = args.slab
    date = args.date
    cint = args.cint
    
    folder = '%s_slab2_%s'%(slab,date)
    supplement = pd.read_csv('%s/%s_slab2_sup_%s.csv'%(folderdir,slab,date))
    
    os.system("rm %s/%s_slab2_c%i_%s.txt"%(folderdir,slab,cint,date))
    contourlist = np.arange(100,700,cint)
    depthlist = np.array(list((set(supplement.depth))))
    with open('%s/%s_slab2_c%i_%s.txt'%(folderdir,slab,cint,date),'a') as f:
        for c in contourlist:
            distdepths = np.abs(c-depthlist)
            supdep = depthlist[np.argmin(distdepths)]
            dat = supplement[supplement.depth == supdep]
            if len(dat) > 0:
                if slab == 'izu' or slab == 'man' or slab == 'ker':
                    dat = dat.sort_values(by=['lat'], ascending=False)
                if slab == 'sol' or slab == 'hin' or slab == 'pam':
                    dat = dat.sort_values(by=['lon'], ascending=False)
                f.write('> %i \n'%c)
                dat = dat[['lon','lat']]
                dat.to_csv(f,header=False,index=False,sep=' ')


# Help/description and command line argument parser
if __name__=='__main__':
    desc = '''
        Expects slab (-s), model-date(-d), path to output folder(-f)
        '''
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('-s', '--slab', dest='slab', type=str,
                        required=True, help='three letter slab code')
    parser.add_argument('-d', '--date', dest='date', type=str,
                        required=True, help='date for model (MM.DD.YY)')
    parser.add_argument('-f', '--folderdir', dest='folderdir', type=str,
                        required=True, help='directory/to/[slab]_slab2_[date] folder')
    parser.add_argument('-i', '--cint', dest='cint', type=int,
                        required=True, help='contour interval (km)')

    pargs = parser.parse_args()
    
    #cProfile.run('main(pargs)')
    main(pargs)
