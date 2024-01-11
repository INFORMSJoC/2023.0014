if __name__ == "__main__":

    from odmtsda.configs import configuration
    from odmtsda.utils import other_utils as ou
    config = configuration.Configuration()
    if config.b_recreate_haversine_matrix:
        ou.create_haversine_matrices(config)
    config._load_accessory()

    from odmtsda.preprocess import preprocess_main
    preprocess_main.run(config)

    from odmtsda.path import path_main
    path_main.enumerate(config)

    from odmtsda.solve import solve_main
    solve_main.solve(config)