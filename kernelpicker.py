import dnf
import platform


class KernelPicker(dnf.Plugin):
    name = 'kernelpicker'

    def __init__(self, base, cli):
        super().__init__(base, cli)

        uname_r = platform.release()
        version, rest = uname_r.split('-')
        release = '.'.join(rest.split('.')[:3])

        self.version = version
        self.release = release
