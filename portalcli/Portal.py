import pkgutil
import toml
import json
import os
import sys
import select
import signal
import tarfile
import uuid
import errno
from io import BytesIO
from pathlib import Path


from docker import APIClient
from docker.errors import ImageNotFound
from .utils import construct_container, generate_argparse, merge_passthrough_vars, get_input_files, get_output_files, get_input_env_files, get_output_env_files


class Portal(object):

    def __init__(self):
        self._docker_client = APIClient()
        self._kill_now = False
        self._container_id = None
        self._std_in = None

        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

    def _cleanup(self):
        self._kill_now = True

        if (self._container_id is not None):
            self._docker_client.stop(self._container_id)
            self._docker_client.remove_container(self._container_id, v=True, force=True)

    def _exit_gracefully(self, signum, frame):
        self._cleanup()

    # Bad code to capture whether stdin is set or not
    def _capture_stdin(self):
        if select.select([sys.stdin, ], [], [], 0.0)[0]:
            self._std_in = sys.stdin.buffer.read()
        elif not sys.stdin.isatty():
            self._std_in = sys.stdin.buffer.read()
    
    def _download_docker_image(self, command, docker_spec):
        docker_image_name = None

        if (docker_spec['image'] == 'Dockerfile'):
            docker_image_name = "portal/" + command
            try:
                image_data = self._docker_client.inspect_image(docker_image_name)
                return image_data
            except ImageNotFound:
                dockerfile = pkgutil.get_data(
                    __name__, "commands/%s/Dockerfile" %  command ).decode('utf-8')
                f = BytesIO(dockerfile.encode('utf-8'))
                for progress_dict in self._docker_client.build(fileobj=f, quiet=True, tag=docker_image_name, decode=True, rm=True):
                    print(progress_dict)
                # if ('progress' in progress_dict):
                #     print(progress_dict['progress'])
        else:
            docker_image_name = docker_spec['image']
            try:
                image_data = self._docker_client.inspect_image(docker_image_name)
                return image_data
            except ImageNotFound:
                print('Pulling Docker Image...')
                for progress_dict in self._docker_client.pull(docker_spec['image'], stream=True, decode=True):
                    print(progress_dict['status'])
                    if ('progress' in progress_dict):
                        print(progress_dict['progress'])
        return self._docker_client.inspect_image(docker_image_name)

    def _parse_args(self, spec_data, argv):
        parser = generate_argparse(spec_data['command'], spec_data['arguments'])
        cmd_options = vars(parser.parse_args(argv))
        cmd_args = cmd_options['cmdargs']
        for argkey in spec_data['arguments'].keys():
            if (spec_data['arguments'][argkey]['shorthand'] == '*'):
                if (len(cmd_args) > 0):
                    spec_data['arguments'][argkey]['value'] = cmd_args[0]
                    if ('File' in spec_data['arguments'][argkey]['docker']):
                        cmd_args = [os.path.join(spec_data['docker']['working_dir'], cmd_options['cmdargs'][0])]
                continue
            spec_data['arguments'][argkey]['value'] = cmd_options[spec_data['arguments']
                                                                  [argkey]['shorthand']]
                                    
        cmd_args += merge_passthrough_vars(spec_data)
        return spec_data, cmd_args

    def _validate_spec(self, spec_data):
        for _, vargs in spec_data['arguments'].items():
            if (vargs['argType'] == 'path' and vargs['docker'] == 'volumeBinding'):
                # Check if path exists
                # if (not os.path.isfile(vargs['value'])): #TODO: Fix!
                #     print('Error: Path %s does not exist!' % vargs['value'])
                #     exit(101)
                pass

    def _create_container(self, cinfo, attach_stdin):
        host_config = self._docker_client.create_host_config(
            port_bindings=cinfo.port_bindings,
            binds=cinfo.vol_bindings
        )
        return self._docker_client.create_container(
            cinfo.container_id,
            command=cinfo.command,
            ports=cinfo.ports,
            environment=cinfo.environment_vars,
            stdin_open=attach_stdin,
            volumes=cinfo.volumes,
            # tty=True,
            host_config=host_config
        )

    def _copy_artefacts_to_container(self, container_id, command_spec):
        def copy_file(input_path, input_name,  output_path):
            tar_name = str(uuid.uuid4()) + '.tar'
            tf = tarfile.open(tar_name, mode='w')

            if (os.path.isfile(input_path)):
                tf.add(input_path, arcname=input_name)
            else:
                print("Could not find file %s " % input_path)
                tf.close()
                os.remove(tar_name)
                return False

            tf.close()
            with open(tar_name, 'rb') as tar_file:
                data = tar_file.read()
                self._docker_client.put_archive(container_id, output_path, data)

            os.remove(tar_name)


        for file in get_input_files(command_spec):
            copy_file(file['value'], file['value'], command_spec['docker']['working_dir'])

        home = str(Path.home())
        for file in get_input_env_files(command_spec):
            copy_file(os.path.join(home, file['name']), file['name'], '/root')
        return True


    def _copy_artefacts_from_container(self, container_id, command_spec):
        def copy_file(input_file, output_path):
            tar_name = str(uuid.uuid4()) + '.tar'
            f = open(tar_name, 'wb')
            bits, _ = self._docker_client.get_archive(
                container_id, input_file)
            for chunk in bits:
                f.write(chunk)
            f.close()

            tar = tarfile.open(tar_name)
            tar.extractall()
            tar.close()
            os.remove(tar_name)

        for file in get_output_files(command_spec):
            copy_file(os.path.join(command_spec['docker']['working_dir'], file['value']), None)

        for file in get_output_env_files(command_spec):
            copy_file(os.path.join('/root/', file['name']), None)

    def run_command(self, command, argv):

        command_spec = None
        try:
            spec_data = pkgutil.get_data(
                __name__, "commands/%s/spec.toml" %  command ).decode('utf-8')
            command_spec = toml.loads(spec_data)
        except FileNotFoundError:
            print('Command not found')
            return 101

        self._capture_stdin()

        command_spec, cmd_argv = self._parse_args(command_spec, argv)
        self._validate_spec(command_spec)
        
        image_info = self._download_docker_image(command, command_spec['docker'])
        cinfo = construct_container(image_info, cmd_argv, command_spec)

        docker_container = self._create_container(cinfo, (self._std_in is not None))
        if (len(docker_container.get('Warnings')) > 0):
            print('Could not start container. Warnings: %s',
                  ' '.join(docker_container.get('Warnings')))
            return 101

        self._container_id = docker_container.get('Id')
        print('Process created in container: %s' % self._container_id)

        if (not self._copy_artefacts_to_container(self._container_id, command_spec)):
            self._cleanup()
            return 101

        
        
        if (self._std_in is not None):
            s = self._docker_client.attach_socket(self._container_id, params={'stdin': 1, 'stream': 1})
            os.write(s.fileno(), self._std_in)
            # s._sock.sendall(self._std_in)
            s.close()
        
        ## Attaching stdin
        self._docker_client.start(container=self._container_id)

        for log in self._docker_client.logs(
            container=self._container_id, stream=True, follow=True):
            sys.stdout.buffer.write(log)
        self._docker_client.wait(container=self._container_id)

        self._copy_artefacts_from_container(self._container_id, command_spec)

        self._docker_client.remove_container(container=self._container_id)

        return 0
