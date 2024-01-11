import json, pickle, yaml, os, argparse

import git

def generate_argParser():

    
    s_git_repo_dir = git.Repo(".", search_parent_directories=True).working_tree_dir
    l_valid_input_arguments = [
        x
        for filename in os.listdir(
            os.path.join(
                s_git_repo_dir,
                'odmtsda/configs/valid_input_arguments'
            )
        )
        if filename.endswith('.json')
        for x in loadJson(
            os.path.join(
                s_git_repo_dir,
                'odmtsda/configs/valid_input_arguments',
                filename
            )
        )
    ]


    parser = argparse.ArgumentParser()
    for d_args in l_valid_input_arguments:

        if isinstance(d_args['default_val'], list) or isinstance(d_args['default_val'], tuple):
            input_type = type(d_args['default_val'][0])
        elif isinstance(d_args['default_val'], bool):
            input_type = str2bool
        else:
            input_type = type(d_args['default_val'])

        parser.add_argument(
            d_args['var_name'],
            required = d_args['required'],
            nargs = d_args['nargs'],
            type = input_type,
            default = d_args['default_val']
        )

    return vars(parser.parse_known_args()[0])


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")

def loadPickle(path):

    file = open(path, 'rb')
    data = pickle.load(file)
    file.close()
    return data

def savePickle(data, path):

    file = open(path, 'wb')
    data = pickle.dump(data, file)
    file.close()

def loadJson(path):

    file = open(path, 'r')
    data = json.load(file)
    file.close()
    return data

def saveJson(data, path):

    file = open(path, 'w')
    json.dump(data, file, indent = 4)
    file.close()

def loadYaml(path):

    with open(path, 'r') as stream:
        data = yaml.safe_load(stream)
    return data
    
def checkDir(*dirs):

    for s_dir in dirs:

        if not os.path.isdir(s_dir):
            os.makedirs(s_dir)

def convert_type_to_str(val):

    if isinstance(val, bool):
        return str(int(val))

    elif isinstance(val, list) or isinstance(val, tuple):
        return '_'.join(map(str, val))
    
    elif isinstance(val, float):

        return str(round(val, 2))
    else:
        return str(val)

def writeLog(path, log):
    with open(path, 'wb') as log_file:
        log_file.write(log)
    log_file.close()

def pairwise_list(myList):

    return zip(
        myList[0 : -1],
        myList[1 :]
    )

def compute_percent(f_a, f_b):

    if f_b != 0:
        return round(f_a / f_b * 100, 2)
    else:
        return 0.0