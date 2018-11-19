#!/bin/bash
USAGE="
makettWplots.sh outdir

And the plots will be stored in outdir/
"
function DONE {
    echo -e "\e[92mDONE\e[0m"
    exit 0
}

OUTDIR="ttwplots"
if [[ "X$1" != "X" ]]; then OUTDIR=$1; shift; fi

LUMI=41.4
BASEOPTIONS=" -f -j 2 -l ${LUMI} --s2v"\
" -L ttH-multilepton/functionsTTH.cc"\
" --tree treeProducerSusyMultilepton"\
" --mcc ttH-multilepton/lepchoice-ttH-FO.txt"\
" --exclude-cut trigger"\
" --exclude-cut tauveto" # ignore the trigger and tau veto for now
TREEINPUTS="-P /afs/cern.ch/user/s/stiegerb/work/TTHTrees/13TeV/ttWgen_production_Nov1/"
FRIENDTREES=" --Fs /afs/cern.ch/user/s/stiegerb/work/TTHTrees/13TeV/ttWgen_production_Nov1/1_recleaner_011118/"\
" --Fs /afs/cern.ch/user/s/stiegerb/work/TTHTrees/13TeV/ttWgen_production_Nov1/x_matchedJets_Nov19/"
DRAWOPTIONS="--cmsprel 'Internal' --legendFontSize 0.035"\
" --showRatio --maxRatioRange 0 2 --fixRatioRange --showMCError"\

OPTIONS="--pdir ${OUTDIR}"
OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT3L}"

MCA="ttH-multilepton/ttWGenPlots/mca-ttw.txt"
CUTS="ttH-multilepton/2lss_tight.txt"
PLOTS="ttH-multilepton/ttWGenPlots/plots-ttw.txt"

echo "Storing output in ${OUTDIR}/";
echo "Normalizing to ${LUMI}/fb";

ARGUMENTS="${MCA} ${CUTS} ${PLOTS}"
OPTIONS="${TREEINPUTS} ${FRIENDTREES} ${BASEOPTIONS} ${OPTIONS}"

echo "mca  : ${MCA}"
echo "cuts : ${CUTS}"
echo "plots: ${PLOTS}"

python mcPlots.py ${ARGUMENTS} ${OPTIONS} --select-plot nJet25_unmatches -p ttW[0-6]+um
python mcPlots.py ${ARGUMENTS} ${OPTIONS} --select-plot nJet25_matches -p ttW[0-6]+m
python mcPlots.py ${ARGUMENTS} ${OPTIONS} --select-plot nAddPartons -p ttW
python mcPlots.py ${ARGUMENTS} ${OPTIONS} --select-plot nAddPartons_uw -p ttW -u
python mcPlots.py ${ARGUMENTS} ${OPTIONS} --select-plot nJet25 -p ttW[0-2]+j
python mcPlots.py ${ARGUMENTS} ${OPTIONS} --select-plot nJet25_log -p ttW[0-2]+j
    
DONE