import argparse
import os

from .errors import CommandLineError
from .model import ContainerInfo


def split_argv(argv):
    if (argv is None or len(argv) < 2):
        raise CommandLineError(argv, 'Please define a function to run')

    if (len(argv) > 2):
        return argv[1], argv[2:]
    else:
        return argv[1], ''


def get_action(arg_type):
    if (arg_type is None):
        return 'store'

    if (arg_type == 'string'):
        return 'store'

    if (arg_type == 'flag'):
        return 'store_true'

def generate_argparse(command_name, spec_args):
    parser = argparse.ArgumentParser(command_name, add_help=False)

    for spec_key in spec_args.keys():
        spec = spec_args[spec_key]

        if ('shorthand' in spec and spec['shorthand'] == '*'):
            continue

        default = spec['default'] if 'default' in spec else ''
        longname = '--' + spec_key if spec['shorthand'] != spec_key else None
        parser.add_argument('-' + spec['shorthand'],
                            longname,
                            dest=spec['shorthand'],
                            default=default,
                            action=get_action(spec['argType']))
    
    parser.add_argument('cmdargs', nargs=argparse.REMAINDER)
    return parser

def check_if_port_cmd(argument):
    return (argument['docker']) == 'portBinding'

def check_if_volume_cmd(argument):
    return (argument['docker']) == 'volumeBinding'

def check_if_input_cmd(argument):
    return (argument['docker'] == 'inputFile' or (argument['docker']) == 'inOutFile') and ('value' in argument and len(argument['value']) > 0)

def check_if_output_cmd(argument):
    return (argument['docker'] == 'outputFile' or (argument['docker']) == 'inOutFile') and ('value' in argument and len(argument['value']) > 0)

def get_input_files(command_spec):
    return list(filter(check_if_input_cmd, command_spec['arguments'].values()))

def get_output_files(command_spec):
    return list(filter(check_if_output_cmd, command_spec['arguments'].values()))

def construct_container(image_info, args, command_spec):
    container_id = image_info['Id']

    image_cmd = None
    if ('Entrypoint' in image_info['Config'] and image_info['Config']['Entrypoint'] is not None):
        args_str = ' '.join(args)
    elif ('Cmd' in image_info['Config'] and image_info['Config']['Cmd'] is not None):
        image_cmd = image_info['Config']['Cmd'][0]
        args_str = '%s %s' % (image_cmd, ' '.join(args))
    else:
        image_cmd = command_spec['command']
        args_str = '%s %s' % (image_cmd, ' '.join(args))
        
    port_arguments = list(filter(check_if_port_cmd, command_spec['arguments'].values()))
    port_bindings = {}
    for porta in port_arguments:
        port_bindings[porta['internalPort']] = porta['value']

    vol_arguments = list(filter(check_if_volume_cmd, command_spec['arguments'].values()))
    vol_bindings = {}
    for volume in vol_arguments:
        vol_bindings[os.path.abspath(volume['value'])] = {
            'bind': volume['internalPath'],
            'mode': 'rw'
        }

    return ContainerInfo(container_id, args_str, vol_bindings, port_bindings)

def merge_passthrough_vars(spec_data):
    new_args = []
    for arg in spec_data['arguments'].values():
        if (arg['docker'] == 'passthrough'):
            if (arg['argType'] == 'flag' and arg['value']):
                new_args.append('-' + arg['shorthand'])

    return new_args