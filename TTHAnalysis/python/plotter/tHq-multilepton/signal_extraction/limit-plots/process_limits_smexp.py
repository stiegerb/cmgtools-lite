#!/usr/bin/env python
import os
import sys
import numpy as np
import pandas as pd

from functools import partial

from ctcv_helper import print_table
from ctcv_helper import read_dataframe


def xs_limit_ratio(ratio, df_xsecs, df_limits, limval='exp', att='tot'):
    # Take the cross section for cv=1.0, ct=ct/cv
    ratio = round(ratio, 3)
    xsec = read_dataframe(ratio, 1.0, df=df_xsecs, att=att)
    lim = getattr(df_limits.loc[df_limits.ratio.round(3)==ratio], limval)

    try:
        xs_lim = float(xsec) * float(lim)
    except TypeError as e:
        print ratio
        print xsec
        print lim
        raise e

    return xs_lim


def process_limits_smexp(file_smexp, file_xs_limits,
                         outdir='xs_limits/',
                         printout=False,
                         att='tot'):
    # Read sm expected signal strength limits from csv file
    df_limits = pd.read_csv(file_smexp, sep=",", index_col=None)
    # Read xs limits from other csv file (for observed)
    xs_limits = pd.read_csv(file_xs_limits, sep=",", index_col=None)

    # Read the cross sections from csv files
    df_xsecs = pd.read_csv("xsecs/xsecs_tH_ttH_WWZZttbb_K6.csv", sep=",", index_col=None)

    df_xs_limits = pd.DataFrame()
    df_xs_limits['alpha'] = xs_limits.alpha.round(3)
    df_xs_limits['ratio'] = xs_limits.ratio.round(3)

    # Use our xs_limit function to store the limits
    for limval in ['twosigdown', 'onesigdown', 'exp', 'onesigup', 'twosigup']:
        df_xs_limits[limval] = np.vectorize(partial(xs_limit_ratio,
                                                    df_xsecs=df_xsecs,
                                                    df_limits=df_limits,
                                                    limval=limval,
                                                    att=att))(
                                                        df_limits.ratio)

    # Add observed limit
    df_xs_limits['obs'] = xs_limits.obs

    # Remove the duplicate entries, sort, reset the index, and write to csv
    # df_xs_limits.drop_duplicates(subset='ratio', inplace=True)
    df_xs_limits.sort_values(by='ratio', inplace=True)
    df_xs_limits.index = range(1,len(df_xs_limits)+1)
    df_xs_limits.to_csv(os.path.join(outdir, "xs_limits_K6_smexp.csv"))


if __name__ == '__main__':
    from optparse import OptionParser
    usage = """%prog smexp.csv xs_limits.csv"""
    parser = OptionParser(usage=usage)
    parser.add_option("-o", "--outdir", dest="outdir",
                      type="string", default="xs_limits/")
    parser.add_option("--att", dest="att",
                      type="string", default="tot",
                      help="Which xsection to use ('tot' or 'hbb')")
    (options, args) = parser.parse_args()

    try:
        os.system('mkdir -p %s' % options.outdir)
    except ValueError:
        pass

    process_limits_smexp(args[0], args[1], options.outdir, att=options.att)

    sys.exit(0)
