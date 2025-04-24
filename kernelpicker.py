import dnf


class KernelPicker(dnf.Plugin):
    name = 'kernelpicker'

    def sack(self):
        base = self.base.sack.query()
        self.installed = base.installed()
        self.available = base.available()
