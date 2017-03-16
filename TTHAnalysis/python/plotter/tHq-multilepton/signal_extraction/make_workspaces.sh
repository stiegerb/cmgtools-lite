#!/bin/bash

# Set environment for combine
COMBINEDIR="/afs/cern.ch/user/s/stiegerb/combine/"
cd $COMBINEDIR; eval `scramv1 runtime -sh`; cd -;

MODEL="K5"
if [[ "$1" == "K5" || "$1" == "K4" ]]; then
	MODEL=$1
	shift;
fi
echo "...running with ${MODEL} model"

# Run the limit
for card in "$@"
do 
	echo "...processing $card"
	text2workspace.py ${card} -o ${card%.card.txt}_${MODEL}.card.root -P HiggsAnalysis.CombinedLimit.LHCHCGModels:${MODEL} --PO BRU=0 -m 125
done
