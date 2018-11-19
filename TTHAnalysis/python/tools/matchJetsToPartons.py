#!/usr/bin/env python

import os
import ROOT
from CMGTools.TTHAnalysis.treeReAnalyzer2 import Object
from PhysicsTools.HeppyCore.utils.deltar import matchObjectCollection3

class ObjectProxy:
    def __init__(self, event, prefix, index=None):
        self.obj = Object(event, prefix, index)


    def __getitem__(self, attr):
        return self.__getattr__(attr)


    def __getattr__(self, name):
        if name=='eta':
            return self.eta_
        elif name=='phi':
            return self.phi_
        else:
            return getattr(self.obj, name)


    def eta_(self):
        return self.obj.eta


    def phi_(self):
        return self.obj.phi


def filterPt(reco, gen):
    return (reco.pt - gen.pt) / reco.pt < 0.2


def isQGStat23(gp):
    return (gp.status == 23 and
            abs(gp.pdgId) in [1, 2, 3, 4, 5, 21])


class MatchJetsToPartons:
    """
    Counts number of partons at matrix element level, relying on isPromptHard from genParticles
    Then attempts to match jets in a jet collection (JetSel by default) to these partons

    Note that the number of additional partons is already contained in LHEnMEPartons

    Match is done by closest in delta R and within a certain range of pt.

    Added branches:
    "JetSel_[label]_matchedGenPartIndex" : index of the matched genparticle, -1 if unmatched
    "nJetsFromHard"       : total number of jets (pt>25) matched to the hard partons
    "nJetsFromAddPartons" : number of jets (pt>25) matched to the additional partons
    "nHardPartons"        : number of hard partons from the matrix element i.e. how many possible gen jets
    "nAddPartons"         : number of additional partons from the matrix element e.g. ttW+0,1,2
    """
    def __init__(self, label="_Recl", jetcoll='JetSel'):
        self.label = label
        self.jetcoll = jetcoll
        self.branches = []
        self.branches.append(("n%s%s" % (self.jetcoll, self.label), "I")) ## FIXME do i need this?
        self.branches.append(("%s%s_matchedGenPartIndex" % (self.jetcoll, self.label), "I", 20,
                              "n%s%s" % (self.jetcoll, self.label)))
        self.branches.append(("nJetsFromHard", "I"))
        self.branches.append(("nHardPartons", "I"))
        self.branches.append(("nAddPartons", "I"))
        self.branches.append(("nJetsFromAddPartons", "I"))


    def listBranches(self):
        return self.branches


    def __call__(self,event):
        njets = getattr(event,"n%s%s" % (self.jetcoll, self.label))
        jets = [ObjectProxy(event, "%s%s" % (self.jetcoll, self.label), i) for i in xrange(njets)]

        allgenparts = [ObjectProxy(event, "GenPart", i) for i in xrange(getattr(event, 'nGenPart'))]

        # Count additional hard partons
        # I.e. they have status 23 and are not isPromptHard (i.e. not from top or W decay for ttW)
        addpart = [gp for gp in allgenparts if isQGStat23(gp) and not gp.isPromptHard]

        # Try to match jets to either the hard products (from top or W) or to the additional partons
        hardparts = [gp for gp in allgenparts if isQGStat23(gp) and gp.isPromptHard]
        pairs = matchObjectCollection3(jets, addpart + hardparts, filter=filterPt)
        # pairs: dict of jet -> matched genparticle

        matchedJetsInd = [-1]*len(jets)
        nmatched_hard_25 = 0
        nmatched_addpart_25 = 0

        for ji, jet in enumerate(jets):
            matched_gp = pairs.get(jet)
            if matched_gp:
                matchedJetsInd[ji] = allgenparts.index(matched_gp)
                if jet.pt > 25:
                    nmatched_hard_25 += 1
                    if not matched_gp.isPromptHard:
                        nmatched_addpart_25 += 1

        ret = {}
        ret["n%s%s" % (self.jetcoll, self.label)] = len(jets)
        ret["%s%s_matchedGenPartIndex" % (self.jetcoll, self.label)] = matchedJetsInd
        ret["nJetsFromHard"] = nmatched_hard_25
        ret["nJetsFromAddPartons"] = nmatched_addpart_25
        ret["nAddPartons"] = len(addpart)
        ret["nHardPartons"] = len(addpart+hardparts)

        return ret

MODULES = [('matchJetsToPartons', MatchJetsToPartons())]

##################################################
# Test this friend producer like so:
# >> python matchJetsToPartons.py tree.root
# or so:
# >> python matchJetsToPartons.py tree.root friend_tree.root

if __name__ == '__main__':
    from sys import argv
    from pprint import pprint
    treefile = ROOT.TFile.Open(argv[1])
    tree = treefile.Get("tree")
    tree.vectorTree = True
    print "... processing %s" % argv[1]

    try:
        friendfile = ROOT.TFile.Open(argv[2])
        friendtree = friendfile.Get("sf/t")
        tree.AddFriend(friendtree)
        print "... adding friend tree from %s" % argv[2]
    except IndexError:
        pass

    from CMGTools.TTHAnalysis.treeReAnalyzer import EventLoop, Module

    class Tester(Module):
        def __init__(self, name):
            Module.__init__(self,name,None)
            self.module = MatchJetsToPartons(label="_Recl", jetcoll="JetSel")
            print "Adding these branches:", self.module.listBranches()

        def analyze(self,ev):
            print ("\nrun %6d lumi %4d event %d: jets %d, fwdJets %d, leps %d, isdata=%d" %
                      (ev.run, ev.lumi, ev.evt, ev.nJet25, ev.nJetFwd, ev.nLepGood, int(ev.isData)))
            ret = self.module(ev)

            pprint(ret)
            print '-----------'



        def done(self):
            pass

    T = Tester("tester")
    el = EventLoop([ T ])
    el.loop([tree], maxEvents = 20)
    T.done()
