#!/bin/bash

USAGE="
makecards.sh outdir channel

Where channel is one of:
 3l, 2lss-mm, 2lss-em, 2lss-ee

And the cards will be stored in outdir/channel
"

if [[ "X$1" == "X" ]]; then echo "Please provide output directory name: [makecards.sh outdir channel]"; exit; fi
OUTNAME=$1; shift;
if [[ "X$1" == "X" ]]; then echo "Please provide channel (e.g. 2lss-mm): [makecards.sh outdir channel]"; exit; fi
CHANNEL=$1; shift;

LUMI=36.5
echo "Normalizing to ${LUMI}/fb";

# Note: tthtrees is a symlink to /afs/cern.ch/work/p/peruzzi/tthtrees/
#       thqtrees is a symlink to /afs/cern.ch/work/s/stiegerb/TTHTrees/13TeV/

BASEOPTIONS="-P tthtrees/TREES_TTH_250117_Summer16_JECV3_noClean_qgV2_skimOnlyMC_v1"\
" -P thqtrees/tHq_production_Jan25"\
" --Fs {P}/1_recleaner_250117_v1"\
" --Fs {P}/5_triggerDecision_250117_v1"\
" -F sf/t thqtrees/tHq_eventvars_Jan30/evVarFriend_{cname}.root"\
" -f -j 8 -l ${LUMI} --s2v -v 2"\
" -L ttH-multilepton/functionsTTH.cc"\
" -L tHq-multilepton/functionsTHQ.cc"\
" --tree treeProducerSusyMultilepton"\
" --mcc ttH-multilepton/lepchoice-ttH-FO.txt"\
" --xp data --asimov"\
" --neg"\
" --2d-binning-function 10:tHq_MVAto1D_3l_10"



OPT2L="-W puw2016_nTrueInt_13fb(nTrueInt)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[0]],LepGood_pt[iLepFO_Recl[0]],LepGood_eta[iLepFO_Recl[0]],2)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[1]],LepGood_pt[iLepFO_Recl[1]],LepGood_eta[iLepFO_Recl[1]],2)"
OPT3L="-W puw2016_nTrueInt_13fb(nTrueInt)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[0]],LepGood_pt[iLepFO_Recl[0]],LepGood_eta[iLepFO_Recl[0]],3)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[1]],LepGood_pt[iLepFO_Recl[1]],LepGood_eta[iLepFO_Recl[1]],3)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[2]],LepGood_pt[iLepFO_Recl[2]],LepGood_eta[iLepFO_Recl[2]],3)"

OPTIONS="--od ${OUTNAME}/${CHANNEL} -o ${CHANNEL}"

MCA=""
CUTS=""
BINNING="thqMVA_ttv_3l:thqMVA_tt_3l 40,-1,1,40,-1,1"
SYSTFILE="tHq-multilepton/signal_extraction/systsEnv.txt"

case "$CHANNEL" in
    "3l" )
        OPTIONS="${OPTIONS} ${OPT3L}"
        MCA="tHq-multilepton/signal_extraction/mca-thq-3l-mcdata-frdata_limits.txt"
        CUTS="tHq-multilepton/cuts-thq-3l.txt"
        ;;
    "2lss-mm" )
        OPTIONS="${OPTIONS} ${OPT2L} -E mm_chan"
        MCA="tHq-multilepton/signal_extraction/mca-thq-2lss-mcdata-frdata_limits.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        ;;
    "2lss-em" )
        OPTIONS="${OPTIONS} ${OPT2L} -E em_chan"
        MCA="tHq-multilepton/signal_extraction/mca-thq-2lss-mcdata-frdata_limits.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        ;;
    "2lss-ee" )
        OPTIONS="${OPTIONS} ${OPT2L} -E ee_chan"
        MCA="tHq-multilepton/signal_extraction/mca-thq-2lss-mcdata-frdata_limits.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        ;;
    *)
        echo "${USAGE}"
        echo -e "\e[31mUnknown CHANNEL\e[0m"
        exit 1
esac

test -d $OUTNAME/$CHANNEL || mkdir -p $OUTNAME/$CHANNEL
echo "Storing output in ${OUTNAME}/${CHANNEL}/";

ARGUMENTS="${MCA} ${CUTS} ${BINNING} ${SYSTFILE}"
OPTIONS="${BASEOPTIONS} ${OPTIONS}"

echo "mca      : ${MCA}"
echo "cuts     : ${CUTS}"
echo "binning  : ${BINNING}"
echo "systfile : ${SYSTFILE}"

if [[ "X$1" != "X" ]]; then
    INPUTFILE=$1; shift;
    if [[ ! -f ${INPUTFILE} ]]; then
        echo "File ${INPUTFILE} does not exist"
        exit 1
    fi
    echo "Reading from an input file: ${INPUTFILE}";
    OPTIONS="${OPTIONS} --infile ${INPUTFILE}"
    python makeShapeCardsTHQ.py ${ARGUMENTS} ${OPTIONS}
else
    OPTIONS="${OPTIONS} --savefile ${OUTNAME}/${CHANNEL}/report_thq_${CHANNEL}.root"
    python makeShapeCardsTHQ.py ${ARGUMENTS} ${OPTIONS}
fi


echo -e "\e[92mDONE\e[0m"