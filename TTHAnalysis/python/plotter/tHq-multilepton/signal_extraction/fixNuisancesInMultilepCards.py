#!/usr/bin/env python
import os
import sys
import shutil

CLEANUP = False

"""
- Change lumi uncertainty from 1.026 to 1.025
- Rename btag uncertainties to be the same as for bb channel
- Drop templstat uncertainties and add "* autoMCStats 0" instead
"""

BTAGRENAMING = {
    "CMS_ttHl_btag_cErr1": "CMS_btag_cerr1",
    "CMS_ttHl_btag_cErr2": "CMS_btag_cerr2",
    "CMS_ttHl_btag_HF": "CMS_btag_hf",
    "CMS_ttHl_btag_HFStats1": "CMS_btag_hfstat1",
    "CMS_ttHl_btag_HFStats2": "CMS_btag_hfstat2",
    "CMS_ttHl_btag_LF": "CMS_btag_lf",
    "CMS_ttHl_btag_LFStats1": "CMS_btag_lfstat1",
    "CMS_ttHl_btag_LFStats2": "CMS_btag_lfstat2",
}


for filename in sys.argv[1:]:
    if not (os.path.isfile(filename) and filename.endswith('.txt')):
        continue

    print "... processing", filename

    with open(filename, "r") as cardfile, open("%s.temp" % filename, "w") as newfile:

        for line in cardfile:
            if line.startswith("lumi_13TeV"):
                newline = line.replace(str(1.026), str(1.025))
                newfile.write(newline)
                replaced_lumi = True
            elif line.startswith("CMS_ttHl_templstat"):
                continue  # remove line
            else:
                # Keep previous line
                newfile.write(line)

        for oldname, newname in sorted(BTAGRENAMING.items()):
            newfile.write("nuisance edit rename * * %s %s\n" % (oldname, newname))

        newfile.write("* autoMCStats 0\n")

    shutil.copy(filename, "%s.orig" % filename)
    shutil.move("%s.temp" % filename, filename)
    if CLEANUP:
        os.remove("%s.orig" % filename)
