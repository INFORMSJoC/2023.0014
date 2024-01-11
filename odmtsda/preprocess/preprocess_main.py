from odmtsda.preprocess import createBackboneArcs, createNewbusArcs, organizeH2hArcs, createConnectionArcs, createTrips

def run(config):
    
    ### Part 0: New Matrices
    

    ### Part 1: Construct H2H Arcs
    l_all_backbone_arcs = createBackboneArcs.create(config)
    l_all_newbus_arcs   = createNewbusArcs.create(config, l_all_backbone_arcs)
    organizeH2hArcs.merge(config, l_all_backbone_arcs + l_all_newbus_arcs)


    ### Part 2: Construct Shuttle Connection Arcs
    createConnectionArcs.create(config)

    ### Part 3: Construct Connection Arcs
    createTrips.create(config)