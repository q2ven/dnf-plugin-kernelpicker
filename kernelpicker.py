import dnf


class KernelPicker(dnf.Plugin):
    name = 'kernelpicker'

    def get_installing_kernels(self):
        """
        Returns a list of installing kernel packages (dnf.Package)
        """

        kernels = []
        return kernels

    def get_installed_kernels(self):
        """
        Returns a list of installed kernel packages (dnf.Package)
        """

        kernels = []
        kernels += self.installed.filter(name__eq='kernel').run()
        kernels += self.installed.filter(name__eq='kernel6.12').run()

        kernels.sort(key=lambda package: package.version + package.release)

        return kernels

    def install_non_namespaced_packages(self, kernel):
        """
        Install matching non_namespaced subpackages based on passed kernel (dnf.Package)
        and return True if packages are added to transaction.
        """

        resolve = False
        return resolve

    def install_namespaced_packages(self, kernel):
        """
        Install matching namespaced subpackages based on passed kernel (dnf.Package)
        and return True if packages are added to transaction.
        """

        resolve = False
        return resolve

    def install_packages(self, kernel):
        """
        Install matching subpackages based on passed kernel (dnf.Package)
        and return True if packages are added to transaction.
        """

        resolve = False

        resolve |= self.install_non_namespaced_packages(kernel)
        resolve |= self.install_namespaced_packages(kernel)

        return resolve

    def resolved(self):
        if getattr(self, 'resolving', False):
            return

        resolve = False

        kernels = self.get_installing_kernels()
        if not kernels:
            kernels = self.get_installed_kernels()

        for kernel in kernels:
            resolve |= self.install_packages(kernel)

        if resolve:
            self.resolving = True
            self.base.resolve()
            self.resolving = False

    def sack(self):
        base = self.base.sack.query()
        self.installed = base.installed()
        self.available = base.available()
