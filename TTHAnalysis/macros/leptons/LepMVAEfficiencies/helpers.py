#!/usr/bin/env python
import os
import ROOT
from array import array


def projectFromTree(hist, varname, sel, tree, option=''):
    try:
        tree.Project(hist.GetName(), varname, sel, option)
        return True
    except Exception, e:
        raise e


def getHistoFromTree(tree, sel, bins, var="mass",
                     hname="histo",
                     titlex='', weight=''):
    histo = ROOT.TH1D(hname, "histo", len(bins)-1, array('d', bins))
    if sel == "":
        sel = "1"
    sel = "(%s)" % sel
    if len(weight):
        sel = "%s*(%s)" % (sel, weight)
    projectFromTree(histo, var, sel, tree)
    histo.SetLineWidth(2)
    histo.GetXaxis().SetTitle(titlex)
    # histo.Sumw2()
    histo.SetDirectory(0)
    return histo


def putPHPIndex(odir):
    LOC = '/afs/cern.ch/user/s/stiegerb/www/ttH/index.php'
    try:
        os.symlink(LOC, os.path.join(odir, 'index.php'))
    except OSError, e:
        if e.errno == 17:  # 'File exists'
            pass


def putPHPIndexInAllSubdirs(target):
    for dirpath, dirnames, _ in os.walk(target):
        for dirname in dirnames:
            putPHPIndex(os.path.join(dirpath, dirname))
