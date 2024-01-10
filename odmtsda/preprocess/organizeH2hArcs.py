import sys
from odmtsda.utils import data_utils as du


def merge(config, l_h2h_arcs_raw):

    l_h2h_arcs = [
        {
            **{
                'id': i_idx,
                'arc_name': 'z{}'.format(i_idx)
            },
            **l_h2h_arcs_raw[i_idx]
        }
        for i_idx in range(len(l_h2h_arcs_raw))
    ]

    du.saveJson(
        l_h2h_arcs,
        config.h2h_arcs_json_path
    )