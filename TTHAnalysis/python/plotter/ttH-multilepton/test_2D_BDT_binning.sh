combinedir=~stiegerb/combine # a directory where combine is installed: https://twiki.cern.ch/twiki/bin/viewauth/CMS/SWGuideHiggsAnalysisCombinedLimit#Setting_up_the_environment
directory=$8 # something like cards_testWP_date
category=$9 # 2lss or 3l or all
echo "float cuts_2lss_ttbar1 = ${1};" > ttH-multilepton/binning_2d_thresholds.h
echo "float cuts_2lss_ttbar2 = ${2};" >> ttH-multilepton/binning_2d_thresholds.h
echo "float cuts_2lss_ttV1 = ${3};" >> ttH-multilepton/binning_2d_thresholds.h
echo "float cuts_3l_ttbar1 = ${4};" >> ttH-multilepton/binning_2d_thresholds.h
echo "float cuts_3l_ttbar2 = ${5};" >> ttH-multilepton/binning_2d_thresholds.h
echo "float cuts_3l_ttV1 = ${6};" >> ttH-multilepton/binning_2d_thresholds.h
echo "float cuts_3l_ttV2 = ${7};" >> ttH-multilepton/binning_2d_thresholds.h

# run same command with save option first
echo "running: bash ttH-multilepton/make_cards.sh ${directory} 10 ${category} read"
bash ttH-multilepton/make_cards.sh ${directory} 10 ${category} read > /dev/null
cd cards/${directory}
cd ${combinedir}; eval `scramv1 runtime -sh`; cd -;
rm ${category}.txt; combineCards.py *card.txt > ${category}.txt
res=`combine -M Asymptotic --run blind --rAbsAcc 0.0005 --rRelAcc 0.0005 ${category}.txt | grep "Expected 50"`
cd ../..

echo ${res}
echo "${1} ${2} ${3} ${4} ${5} ${6} ${7} ${8} ${9} ${res}" >> results_optMVAWP_${directory}.txt

eval `scramv1 runtime -sh`


# bash ttH-multilepton/test_2D..  -0.1 0.5 0.1 0.3 -0.1 outputdir [2lss/3l/all]
# bash ttH-multilepton/test_2D..  -0.1 0.5 0.1 0.3 -0.1 outputdir [2lss/3l/all]