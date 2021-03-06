import FWCore.ParameterSet.Config as cms

def hzzCustomize(process, fs_daughter_inputs,
                 idCheatLabel, isoCheatLabel, mvaLabel,
                 fsrLabel):
    '''
    Make HZZ ID and isolation decisions (stored as userFloats), make a
    collection of FSR photons and match them to leptons.
    '''
    process.vertexCleaning = cms.EDFilter("VertexSelector",
                                          src = cms.InputTag(fs_daughter_inputs['vertices']),
                                          cut = cms.string('!isFake && ndof > 4 && abs(z) <= 24 && position.Rho <= 2'),
                                          filter = cms.bool(True),
                                          )
    process.cleanVertices = cms.Path(process.vertexCleaning)
    process.schedule.append(process.cleanVertices)
    fs_daughter_inputs['vertices'] = 'vertexCleaning'

    # Make FSR photon collection, give them isolation and cut on it
    process.load("FinalStateAnalysis.PatTools.miniAOD_fsrPhotons_cff")
    fs_daughter_inputs['fsr'] = 'boostedFsrPhotons'

    process.dretPhotonSelection = cms.EDFilter(
        "CandPtrSelector",
        src = cms.InputTag(fs_daughter_inputs['fsr']),
        cut = cms.string('pt > 2 && abs(eta) < 2.4 && '
                         '((userFloat("fsrPhotonPFIsoChHadPUNoPU03pt02") + '
                         'userFloat("fsrPhotonPFIsoNHadPhoton03")) / pt < 1.8)'),
        )
    fs_daughter_inputs['fsr'] = 'dretPhotonSelection'
    process.makeFSRPhotons = cms.Path(process.fsrPhotonSequence *
                                      process.dretPhotonSelection)
    process.schedule.append(process.makeFSRPhotons)

    # Embed HZZ ID decisions because we need to know them for FSR recovery
    process.electronIDCheatEmbedding = cms.EDProducer(
        "MiniAODElectronHZZIDDecider",
        src = cms.InputTag(fs_daughter_inputs['electrons']),
        idLabel = cms.string(idCheatLabel), # boolean stored as userFloat with this name
        vtxSrc = cms.InputTag(fs_daughter_inputs['vertices']),
        bdtLabel = cms.string(mvaLabel),
        idCutLowPtLowEta = cms.double(-.265),
        idCutLowPtMedEta = cms.double(-.556),
        idCutLowPtHighEta = cms.double(-.551),
        idCutHighPtLowEta = cms.double(-.072),
        idCutHighPtMedEta = cms.double(-.286),
        idCutHighPtHighEta = cms.double(-.267),
        missingHitsCut = cms.int32(999),
        ptCut = cms.double(7.), 
        )
    fs_daughter_inputs['electrons'] = 'electronIDCheatEmbedding'
    process.muonIDCheatEmbedding = cms.EDProducer(
        "MiniAODMuonHZZIDDecider",
        src = cms.InputTag(fs_daughter_inputs['muons']),
        idLabel = cms.string(idCheatLabel), # boolean will be stored as userFloat with this name
        vtxSrc = cms.InputTag(fs_daughter_inputs['vertices']),
        # Defaults are correct as of 6 January 2016, overwrite later if needed
        ptCut = cms.double(5.), 
        )
    fs_daughter_inputs['muons'] = 'muonIDCheatEmbedding'
    
    process.embedHZZ4lIDDecisions = cms.Path(
        process.electronIDCheatEmbedding +
        process.muonIDCheatEmbedding
        )
    process.schedule.append(process.embedHZZ4lIDDecisions)
    
    # Embed fsr as userCands
    process.leptonDRETFSREmbedding = cms.EDProducer(
        "MiniAODLeptonDRETFSREmbedder",
        muSrc = cms.InputTag(fs_daughter_inputs['muons']),
        eSrc = cms.InputTag(fs_daughter_inputs['electrons']),
        phoSrc = cms.InputTag(fs_daughter_inputs['fsr']),
        phoSelection = cms.string(""),
        eSelection = cms.string('userFloat("%s") > 0.5'%idCheatLabel),
        muSelection = cms.string('userFloat("%s") > 0.5'%idCheatLabel),
        fsrLabel = cms.string(fsrLabel),
        etPower = cms.double(2.),
        maxDR = cms.double(0.5),
        )
    fs_daughter_inputs['muons'] = 'leptonDRETFSREmbedding'
    fs_daughter_inputs['electrons'] = 'leptonDRETFSREmbedding'
    
    process.embedDRETFSR = cms.Sequence(process.leptonDRETFSREmbedding)
    process.dREtFSR = cms.Path(process.embedDRETFSR)
    process.schedule.append(process.dREtFSR)    
    
    # embed isolation decisions
    process.leptonIsoCheatEmbedding = cms.EDProducer(
        "MiniAODLeptonHZZIsoDecider",
        srcE = cms.InputTag(fs_daughter_inputs['electrons']),
        srcMu = cms.InputTag(fs_daughter_inputs['muons']),
        isoDecisionLabel = cms.string(isoCheatLabel),
        isoValueLabel = cms.string(isoCheatLabel.replace("Pass", "Val")),
        fsrLabel = cms.string(fsrLabel),
        fsrElecSelection = cms.string('userFloat("%s") > 0.5'%idCheatLabel),
        fsrMuonSelection = cms.string('userFloat("%s") > 0.5'%idCheatLabel),
        eaLabel = cms.string('EffectiveArea'),
        isoConeDRMaxE = cms.double(0.3),
        isoConeDRMaxMu = cms.double(0.3),
        isoCutE = cms.double(0.35),
        isoCutMu = cms.double(0.35),
        )

    fs_daughter_inputs['electrons'] = 'leptonIsoCheatEmbedding:electrons'
    fs_daughter_inputs['muons'] = 'leptonIsoCheatEmbedding:muons'
    
    process.embedHZZ4lIsoDecisions = cms.Path(
        process.leptonIsoCheatEmbedding
        )
    process.schedule.append(process.embedHZZ4lIsoDecisions)

    # remove jets that overlap with FSR photons
    process.jetFSRCleaning = cms.EDProducer(
        'MiniAODJetFSRCleaner',
        src = cms.InputTag(fs_daughter_inputs['jets']),
        srcE = cms.InputTag(fs_daughter_inputs['electrons']),
        srcMu = cms.InputTag(fs_daughter_inputs['muons']),
        fsrLabel = cms.string(fsrLabel),
        fsrElecSelection = cms.string('userFloat("%sTight") > 0.5 && userFloat("%s") > 0.5'%(idCheatLabel, isoCheatLabel)),
        fsrMuonSelection = cms.string('userFloat("%sTight") > 0.5 && userFloat("%s") > 0.5'%(idCheatLabel, isoCheatLabel)),
        )
    fs_daughter_inputs['jets'] = 'jetFSRCleaning'
    
    process.cleanJetsFSR = cms.Path(process.jetFSRCleaning)
    process.schedule.append(process.cleanJetsFSR)
