import pandas as pd
from haversine import haversine
from odmtsda.utils import data_utils
def check_if_direct_shuttle(l_arcs):

    if len(l_arcs) == 1 and l_arcs[0][0] == 's':
        return True
    else:
        return False


def get_ticket_price(config):

    return config.f_base_ticket_fare

# note that this is not used in the paper
# this function is created for readers who want to try p-path
def create_haversine_matrices(config):

    print('Recreating distance and time matrices')
    d_dist_km = {}
    d_time_min = {}

    df_stops = pd.read_csv(config.s_stop_csv_path)

    for _, df_stop_a in df_stops.iterrows():

        i_stop_a  = df_stop_a['stop_id']
        l_point_a = [
            df_stop_a['stop_lat'], df_stop_a['stop_lon']
        ]

        for _, df_stop_b in df_stops.iterrows():
            
            i_stop_b  = df_stop_b['stop_id']
            l_point_b = [
                df_stop_b['stop_lat'], df_stop_b['stop_lon']
            ]

            f_km = haversine(
                l_point_a, l_point_b
            )

            f_min = f_km / config.f_dummy_speed

            d_dist_km[i_stop_a, i_stop_b] = f_km
            d_time_min[i_stop_a, i_stop_b] = f_min

    data_utils.savePickle(
        d_time_min,
        config.s_time_min_pickle_path
    )

    data_utils.savePickle(
        d_dist_km,
        config.s_dist_km_pickle_path
    )