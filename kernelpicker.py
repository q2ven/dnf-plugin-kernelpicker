import dnf


class KernelPicker(dnf.Plugin):
    name = 'kernelpicker'

    def resolved(self):
        if getattr(self, 'resolving', False):
            return

        resolve = False

        if resolve:
            self.resolving = True
            self.base.resolve()
            self.resolving = False

    def sack(self):
        base = self.base.sack.query()
        self.installed = base.installed()
        self.available = base.available()
