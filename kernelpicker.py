import dnf


class KernelPicker(dnf.Plugin):
    name = 'kernelpicker'

    PACKAGE_NAMES = {
        'non_namespaced': [
            'bpftool',
            'bpftool-debuginfo',
            'kernel',
            'kernel-debuginfo',
            'kernel-debuginfo-common-aarch64',
            'kernel-debuginfo-common-x86_64',
            'kernel-devel',
            'kernel-headers',
            'kernel-libbpf',
            'kernel-libbpf-debuginfo',
            'kernel-libbpf-devel',
            'kernel-libbpf-static',
            'kernel-modules-extra',
            'kernel-modules-extra-common',
            'kernel-tools',
            'kernel-tools-debuginfo',
            'kernel-tools-devel',
            'perf',
            'perf-debuginfo',
            'python3-perf',
            'python3-perf-debuginfo'
        ],
        'namespaced': [
            ('kernel-debuginfo', 'kernel6.12-debuginfo'),
            ('kernel-debuginfo-common-aarch64', 'kernel6.12-debuginfo-common-aarch64'),
            ('kernel-debuginfo-common-x86_64', 'kernel6.12-debuginfo-common-x86_64'),
            ('kernel-modules-extra', 'kernel6.12-modules-extra'),
            ('kernel-modules-extra-common', 'kernel6.12-modules-extra-common'),  # not yet provided ?
            ('perf', 'perf6.12'),
            ('perf-debuginfo', 'perf6.12-debuginfo'),
            ('python3-perf', 'python3-perf6.12'),
            ('python3-perf-debuginfo', 'python3-perf6.12-debuginfo')
        ]
    }

    def get_installing_kernels(self):
        """
        Returns a list of installing kernel packages (dnf.Package)
        """

        kernels = []

        method_names = [
            'list_downgrades',
            'list_installs',
            'list_reinstalls',
            'list_upgrades',
        ]

        for method_name in method_names:
            list_packages = getattr(self.base.goal, method_name)

            for package in list_packages():
                if package.name in ['kernel', 'kernel6.12']:
                    kernels.append(package)

        kernels.sort(key=lambda package: package.version + package.release)

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

        query_vr = {
            'version__eq': kernel.version,
            'release__eq': kernel.release
        }

        for name in self.PACKAGE_NAMES['non_namespaced']:
            query = {
                'name__eq': name
            }

            if not self.installed.filter(**query):
                continue

            query.update(query_vr)

            if self.installed.filter(**query) or \
               not self.available.filter(**query):
                continue

            self.base.install(f'{name}-{kernel.version}-{kernel.release}', strict=False)
            resolve = True

        return resolve

    def install_namespaced_packages(self, kernel):
        """
        Install matching namespaced subpackages based on passed kernel (dnf.Package)
        and return True if packages are added to transaction.
        """

        resolve = False

        if kernel.name == 'kernel':
            return resolve

        for non_namespaceed, namespaced in self.PACKAGE_NAMES['namespaced']:
            if kernel.name == 'kernel':
                installed_name = namespaced
                install_name = non_namespaceed
            else:
                installed_name = non_namespaceed
                install_name = namespaced

            if not self.installed.filter(name__eq=installed_name):
                continue

            query = {
                'name__eq': install_name,
                'version__eq': kernel.version,
                'release__eq': kernel.release
            }

            if self.installed.filter(**query) or \
               not self.available.filter(**query):
                continue

            self.base.install(f'{install_name}-{kernel.version}-{kernel.release}', strict=False)
            resolve = True

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
