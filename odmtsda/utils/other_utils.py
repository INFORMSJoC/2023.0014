def check_if_direct_shuttle(l_arcs):

    if len(l_arcs) == 1 and l_arcs[0][0] == 's':
        return True
    else:
        return False


def get_ticket_price(config):

    return config.f_base_ticket_fare
