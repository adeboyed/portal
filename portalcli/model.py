

class ContainerInfo(object):

    def __init__(self, container_id, command, vol_bindings, port_bindings):
        self._container_id = container_id
        self._command = command
        self._vol_bindings = vol_bindings
        self._port_bindings = port_bindings

    @property
    def container_id(self):
        return self._container_id

    @property
    def command(self):
        return self._command

    @property
    def ports(self):
        return list(self._port_bindings.keys())

    @property
    def volumes(self):
        return list(map(lambda x: x['bind'], self._vol_bindings.values()))

    @property
    def vol_bindings(self):
        return self._vol_bindings

    @property
    def port_bindings(self):
        return self._port_bindings
