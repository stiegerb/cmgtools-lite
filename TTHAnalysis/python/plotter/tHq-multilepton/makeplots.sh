#!/bin/bash
USAGE="
makeplots.sh outdir plottag

Where plottag is one of:
 3l, 3l-zcontrol, 3l-ttcontrol
 2lss-mm, 2lss-mm-ttcontrol
 2lss-em, 2lss-em-ttcontrol
 2lss-ee, 2lss-ee-ttcontrol

And the plots will be stored in outdir/
"
function DONE {
    echo -e "\e[92mDONE\e[0m"
    exit 0
}

if [[ "X$1" == "X" ]]; then echo "Please provide output directory name: [makeplots.sh outdir plottag]"; exit; fi
OUTDIR=$1; shift;
if [[ "X$1" == "X" ]]; then echo "Please Provide plottag (e.g. 2lss-mm): [makeplots.sh outdir plottag]"; exit; fi
PLOTTAG=$1; shift;

LUMI=36.5
echo "Normalizing to ${LUMI}/fb";

# Note: tthtrees is a symlink to /afs/cern.ch/work/p/peruzzi/tthtrees/
#       thqtrees is a symlink to /afs/cern.ch/work/s/stiegerb/TTHTrees/13TeV/

BASEOPTIONS=" -f -j 8 -l ${LUMI} --s2v"\
" -L ttH-multilepton/functionsTTH.cc"\
" --tree treeProducerSusyMultilepton"\
" --mcc ttH-multilepton/lepchoice-ttH-FO.txt"
TREEINPUTS="-P tthtrees/TREES_TTH_250117_Summer16_JECV3_noClean_qgV2_skimOnlyMC_v1"\
" -P thqtrees/tHq_production_Jan25"
FRIENDTREES=" --Fs {P}/1_recleaner_250117_v1"\
" --Fs {P}/5_triggerDecision_250117_v1"\
" -F sf/t thqtrees/tHq_eventvars_Jan30/evVarFriend_{cname}.root"
DRAWOPTIONS="--lspam '#bf{CMS} #it{Preliminary}' --legendWidth 0.20 --legendFontSize 0.035"\
" --showRatio --maxRatioRange 0 2 --fixRatioRange --showMCError"\

OPT2L="-W puw2016_nTrueInt_13fb(nTrueInt)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[0]],LepGood_pt[iLepFO_Recl[0]],LepGood_eta[iLepFO_Recl[0]],2)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[1]],LepGood_pt[iLepFO_Recl[1]],LepGood_eta[iLepFO_Recl[1]],2)"
OPT3L="-W puw2016_nTrueInt_13fb(nTrueInt)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[0]],LepGood_pt[iLepFO_Recl[0]],LepGood_eta[iLepFO_Recl[0]],3)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[1]],LepGood_pt[iLepFO_Recl[1]],LepGood_eta[iLepFO_Recl[1]],3)*"\
"leptonSF_ttH(LepGood_pdgId[iLepFO_Recl[2]],LepGood_pt[iLepFO_Recl[2]],LepGood_eta[iLepFO_Recl[2]],3)"

OPTIONS="--pdir ${OUTDIR}"
MCA=""
CUTS=""
PLOTS=""
case "$PLOTTAG" in
    "3l" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT3L} --xp data"
        MCA="tHq-multilepton/mca-thq-3l-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-3l.txt"
        PLOTS="tHq-multilepton/plots-thq-3l-kinMVA.txt"
        ;;
    "3l-mvaout" )
        OPTIONS="${OPTIONS} ${OPT3L} --xp data --plotmode norm"
        OPTIONS="${OPTIONS} --select-plot thqMVA_tt_3l,thqMVA_ttv_3l"
        OPTIONS="${OPTIONS} --xp WWss,WWDPS,VVV,tttt,tZq,ZZ,WZ"
        MCA="tHq-multilepton/mca-thq-3l-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-3l.txt"
        PLOTS="tHq-multilepton/plots-thq-3l-kinMVA.txt"
        ;;
    "3l-zcontrol" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT3L}"
        MCA="tHq-multilepton/mca-thq-3l-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-3l-Zcontrol.txt"
        PLOTS="tHq-multilepton/plots-thq-3l-zcontrol.txt"
        ;;
    "3l-ttcontrol" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT3L}"
        MCA="tHq-multilepton/mca-thq-3l-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-3l-ttbarcontrol.txt"
        PLOTS="tHq-multilepton/plots-thq-3l-kinMVA.txt"
        ;;
    "2lss-mvaout" )
        OPTIONS="${OPTIONS} ${OPT2L} --xp data --plotmode norm"
        OPTIONS="${OPTIONS} --select-plot thqMVA_tt_2lss,thqMVA_ttv_2lss"
        OPTIONS="${OPTIONS} --xp WWss,WWDPS,VVV,tttt,tZq,ZZ,WZ"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-mm" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L} --xp data -E mm_chan"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-mm-ttcontrol" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L} -E mm_chan"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss-ttbarcontrol.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-em" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L} --xp data -E em_chan"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-em-ttcontrol" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L} -E em_chan"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss-ttbarcontrol.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-ee" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L} --xp data -E ee_chan"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2lss-ee-ttcontrol" )
        OPTIONS="${OPTIONS} ${DRAWOPTIONS} ${OPT2L} -E ee_chan"
        MCA="tHq-multilepton/mca-thq-2lss-mcdata-frdata.txt"
        CUTS="tHq-multilepton/cuts-thq-2lss-ttbarcontrol.txt"
        PLOTS="tHq-multilepton/plots-thq-2lss-kinMVA.txt"
        ;;
    "2los-em-ttcontrol" )
        TREEINPUTS="-P tthtrees/TREES_TTH_250117_Summer16_JECV3_noClean_qgV2"
        FRIENDTREES=" --Fs {P}/1_recleaner_250117_v1 --Fs {P}/5_triggerDecision_250117_v1 -F sf/t thqtrees/tHq_eventvars_Feb2/evVarFriend_{cname}.root"
        OPTIONS="${TREEINPUTS} ${FRIENDTREES} ${BASEOPTIONS} ${OPTIONS} ${DRAWOPTIONS} ${OPT2L}"
        MCA="tHq-multilepton/mca-2los-mcdata.txt"
        CUTS="tHq-multilepton/cuts-thq-ttbar-fwdjet.txt"
        PLOTS="tHq-multilepton/plots-thq-ttbar-fwdjet.txt"
        python mcPlots.py ${MCA} ${CUTS} ${PLOTS} ${OPTIONS} --enable-cut 2bl --select-plot dEtaFwdJet2BJet
        python mcPlots.py ${MCA} ${CUTS} ${PLOTS} ${OPTIONS} --exclude-plot dEtaFwdJet2BJet
        DONE
        ;;
    *)
        echo "${USAGE}"
        echo -e "\e[31mUnknown plottag\e[0m"
        exit 1
esac

echo "Storing output in ${OUTDIR}/";

ARGUMENTS="${MCA} ${CUTS} ${PLOTS}"
OPTIONS="${TREEINPUTS} ${FRIENDTREES} ${BASEOPTIONS} ${OPTIONS}"

echo "mca  : ${MCA}"
echo "cuts : ${CUTS}"
echo "plots: ${PLOTS}"



if [[ "X$1" != "X" ]]; then
    SELECTPLOT=$1; shift;
    echo "Running a single plot: ${SELECTPLOT}";
    python mcPlots.py ${ARGUMENTS} ${OPTIONS} --select-plot ${SELECTPLOT}
else
    python mcPlots.py ${ARGUMENTS} ${OPTIONS} --enable-cut 2bl --select-plot dEtaFwdJet2BJet
    python mcPlots.py ${ARGUMENTS} ${OPTIONS} --exclude-plot dEtaFwdJet2BJet
fi

DONE
