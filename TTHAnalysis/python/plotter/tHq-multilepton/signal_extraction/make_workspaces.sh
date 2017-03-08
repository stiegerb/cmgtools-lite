#!/bin/bash

# Set environment for combine
COMBINEDIR="/afs/cern.ch/user/s/stiegerb/combine/"
cd $COMBINEDIR; eval `scramv1 runtime -sh`; cd -;

# Run the limit
for card in "$@"
do 
	echo "...processing $card"
	text2workspace.py $card -P HiggsAnalysis.CombinedLimit.LHCHCGModels:L2 --PO BRU=0
done

# Set back environment
eval `scramv1 runtime -sh`;

