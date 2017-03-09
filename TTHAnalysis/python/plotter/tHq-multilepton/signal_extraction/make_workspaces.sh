#!/bin/bash

# Set environment for combine
COMBINEDIR="/afs/cern.ch/user/s/stiegerb/combine/"
cd $COMBINEDIR; eval `scramv1 runtime -sh`; cd -;

# Run the limit
for card in "$@"
do 
	echo "...processing $card"
	text2workspace.py $card -P HiggsAnalysis.CombinedLimit.LHCHCGModels:K5 --PO BRU=0 -m 125
	# text2workspace.py $card -P HiggsAnalysis.CombinedLimit.LHCHCGModels:K4 --PO BRU=0 -m 125
	# text2workspace.py $card -P HiggsAnalysis.CombinedLimit.LHCHCGModels:K2 --PO BRU=0 -m 125
	# text2workspace.py $card -P HiggsAnalysis.CombinedLimit.LHCHCGModels:K1 --PO BRU=0 -m 125
	# text2workspace.py $card -P HiggsAnalysis.CombinedLimit.LHCHCGModels:K3 --PO BRU=0 -m 125
	# text2workspace.py $card -P HiggsAnalysis.CombinedLimit.LHCHCGModels:L2 --PO BRU=0 -m 125
done
