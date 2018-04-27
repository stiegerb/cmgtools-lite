#!/usr/bin/env python
import os
import sys
import numpy as np
import pandas as pd

# Hardcoded SM production cross sections for tHq, tHW, and ttH
xsec_thq_SM = 0.07096
xsec_thw_SM = 0.01561
xsec_tth_SM = 0.5071

# Hardcoded SM BRs for WW, ZZ, and tautau
SM_BR_ww = 0.214
SM_BR_zz = 0.026
SM_BR_tt = 0.063
SM_BR_bb = 0.583

def process_xsec_scalings(xsbr_scalings, br_scalings, outdir='xsec_scalings/'):
    df_xsbr = pd.read_csv(xsbr_scalings, sep=",", index_col=None)
    df_br = pd.read_csv(br_scalings, sep=",", index_col=None)

    xsecs = pd.DataFrame()
    xsecs['cv']  = df_xsbr.cv.round(3) # only use 3 significant digits
    xsecs['cf']  = df_xsbr.ct.round(3)

    xsecs['tthtot'] =  df_xsbr.ttHww*SM_BR_ww*xsec_tth_SM 
    xsecs['tthtot'] += df_xsbr.ttHzz*SM_BR_zz*xsec_tth_SM 
    xsecs['tthtot'] += df_xsbr.ttHtt*SM_BR_tt*xsec_tth_SM
    xsecs['tthtot'] += df_xsbr.ttHbb*SM_BR_bb*xsec_tth_SM

    xsecs['thtot'] =  df_xsbr.tHqww*SM_BR_ww*xsec_thq_SM 
    xsecs['thtot'] += df_xsbr.tHqzz*SM_BR_zz*xsec_thq_SM 
    xsecs['thtot'] += df_xsbr.tHqtt*SM_BR_tt*xsec_thq_SM
    xsecs['thtot'] += df_xsbr.tHqbb*SM_BR_bb*xsec_thq_SM
    xsecs['thtot'] += df_xsbr.tHWww*SM_BR_ww*xsec_thw_SM 
    xsecs['thtot'] += df_xsbr.tHWzz*SM_BR_zz*xsec_thw_SM 
    xsecs['thtot'] += df_xsbr.tHWtt*SM_BR_tt*xsec_thw_SM
    xsecs['thtot'] += df_xsbr.tHWbb*SM_BR_bb*xsec_thw_SM

    xsecs['tthhbb'] =  df_xsbr.ttHbb*SM_BR_bb*xsec_tth_SM 

    xsecs['thhbb'] =  df_xsbr.tHqbb*SM_BR_bb*xsec_thq_SM 
    xsecs['thhbb'] += df_xsbr.tHWbb*SM_BR_bb*xsec_thw_SM 

    xsecs['hbb'] =  df_xsbr.ttHbb*SM_BR_bb*xsec_tth_SM 
    xsecs['hbb'] += df_xsbr.tHqbb*SM_BR_bb*xsec_thq_SM 
    xsecs['hbb'] += df_xsbr.tHWbb*SM_BR_bb*xsec_thw_SM


    xsecs['tot'] = xsecs['tthtot'] + xsecs['thtot']

    # Write them out as csv files for other notebooks to use
    xsecs.to_csv(os.path.join(outdir, 'xsecs_tH_ttH_WWZZttbb_K6.csv'))
    print "wrote", os.path.join(outdir, 'xsecs_tH_ttH_WWZZttbb_K6.csv')

if __name__ == '__main__':
    from optparse import OptionParser
    usage = """%prog xsbr_scalings.csv br_scalings.csv"""
    parser = OptionParser(usage=usage)
    parser.add_option("-o", "--outdir", dest="outdir",
                      type="string", default="xsec_scalings/")
    (options, args) = parser.parse_args()

    try:
        os.system('mkdir -p %s' % options.outdir)
    except ValueError:
        pass

    assert(all([os.path.exists(f) for f in args[:2]])), 'provide both xsbr and br scalings file'

    process_xsec_scalings(args[0], args[1], options.outdir)

    sys.exit(0)
