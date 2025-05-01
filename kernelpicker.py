from dnfpluginscore import logger

import dnf
import platform


def get_major_version(version):
    return '.'.join(version.split('.')[:2])


class KernelPicker(dnf.Plugin):
    name = 'kernelpicker'

    VARIANT_6_1 = '6.1'
    VARIANT_6_12 = '6.12'
    VARIANT_LATEST = 'latest'
    VARIANT_DEFUALT = VARIANT_6_1
    VARIANTS = {
        VARIANT_6_1,
        VARIANT_6_12,
        VARIANT_LATEST
    }

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
            'kernel6.12',
            'kernel6.12-debuginfo',
            'kernel6.12-debuginfo-common-aarch64',
            'kernel6.12-debuginfo-common-x86_64',
            'kernel6.12-modules-extra',
            'kernel6.12-modules-extra-common',  # not yet provided ?
            'perf6.12',
            'perf6.12-debuginfo',
            'python3-perf6.12',
            'python3-perf6.12-debuginfo'
        ]
    }

    def __init__(self, base, cli):
        super().__init__(base, cli)

        uname_r = platform.release()
        version, rest = uname_r.split('-')
        release = '.'.join(rest.split('.')[:3])

        self.version = version
        self.release = release

        if self.cli:
            self.cli.register_command(KernelPickerCommand)

    def config(self):
        cp = self.read_config(self.base.conf)

        # /etc/dnf/plugins/kernelpicker.conf
        if cp and cp.has_section('main') and cp.has_option('main', 'variant'):
            self.variant = cp.get('main', 'variant')
            if self.variant in self.VARIANTS:
                return

            message = f'Ignoring kernel variant in kernelpicker.conf: \'{self.variant}\''
            if not self.variant:
                logger.debug(message)
            else:
                logger.warning(message)

        # uname -r
        self.variant = get_major_version(platform.release().split('-')[0])
        if self.variant in self.VARIANTS:
            return

        logger.warning(f'Ignoring kernel variant of $(uname -r): \'{self.variant}\'')

        self.variant = self.VARIANT_DEFUALT

    def set_major_version(self):
        if self.variant == 'latest':
            versions = []

            for name in ('kernel', 'kernel6.12'):
                latest = self.available.filter(name__eq=name).latest()
                if latest:
                    kernel = latest.run()[0]
                    versions.append(kernel.version)

            self.major_version = get_major_version(versions[-1])
        else:
            self.major_version = self.variant

        logger.debug(f'Kernel variant: {self.major_version}')

    def get_filter_query(self):
        version__lt = f'{self.major_version}.0'

        first, second = self.major_version.split('.')

        version__gte = '.'.join([
            first,
            str(int(second) + 1),
            '0'
        ])

        return [
            {'version__lt': version__lt},
            {'version__gte': version__gte}
        ]

    def exclude_non_namespaced_packages(self):
        """
        Filter out non-namespaced kernel & subpackages if their versions meet
          1. < self.major_version
          2. >= self.major_version + 1
        """
        excluded = self.empty

        for name in self.PACKAGE_NAMES['non_namespaced']:
            base = self.all.filter(name__eq=name)

            for query in self.get_filter_query():
                excluded = excluded.union(base.filter(**query))

        self.excluded = self.excluded.union(excluded)

    def exclude_namespaced_packages(self):
        """
        Filter out namespaced kernel & subpackages if their versions meet
          1. < self.major_version
          2. >= self.major_version + 1
        """
        excluded = self.empty

        for name in self.PACKAGE_NAMES['namespaced']:
            base = self.all.filter(name__eq=name)

            for query in self.get_filter_query():
                excluded = excluded.union(base.filter(**query))

        self.excluded = self.excluded.union(excluded)

    def exclude_livepatch_packages(self):
        # kernel-livepatch-repo-(s3|cdn) is noarch
        livepatch = self.all.filter(arch__neq='noarch', name__glob='kernel-livepatch-*')

        # Do not restrict to the running kernel only, in case a user wants to
        # install a new kernel and livepatch in the same transaction and reboot.
        included = self.all.filter(name__glob=f'kernel-livepatch-{self.major_version}.*')
        excluded = livepatch.difference(included)

        self.excluded = self.excluded.union(excluded)

    def exclude_packages(self):
        """
        Filter out kernel, subpackages, and livepatch that does not match
        the preferred major version.
        """
        self.excluded = self.empty

        self.exclude_non_namespaced_packages()
        self.exclude_namespaced_packages()
        self.exclude_livepatch_packages()

        # "dnf update" requires the running kernel packages to be
        # included in the query result, so don't exclude them !
        self.excluded = self.excluded.difference(self.installed)

        if self.excluded:
            logger.debug(
                'Filtered packages\n  %s\n',
                '\n  '.join(
                    f'{query.name}-{query.version}.{query.release}.{query.arch} ({query.reponame})'
                    for query in self.excluded.run()
                )
            )

            self.base.sack.add_excludes(self.excluded)

    def sack(self):
        self.all = self.base.sack.query()
        self.available = self.all.available()
        self.empty = self.all.filter(empty=True)
        self.installed = self.all.installed()

        self.set_major_version()
        self.exclude_packages()

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

        # Don't try to install filtered versions of packages.
        if get_major_version(kernel.version) != self.major_version:
            return resolve

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


class KernelPickerCommand(dnf.cli.Command):
    aliases = ('kernelpicker',)
    summary = 'Configure preferred kernel package variant'

    @staticmethod
    def set_argparser(parser):
        parser.add_argument(
            'variant',
            nargs='?',
            choices=KernelPicker.VARIANTS,
            help=('Set the preference for kernel package variant, '
                  'or show it if not specified'),
            metavar='[%s]' % ' | '.join(KernelPicker.VARIANTS)
        )

    def run(self):
        if self.opts.variant:
            self.base.conf.write_raw_configfile(
                self.base.conf.pluginconfpath[0] + '/kernelpicker.conf',
                'main',
                self.base.conf.substitutions,
                {'variant': self.opts.variant}
            )

        kernelpicker = KernelPicker(self.base, None)
        kernelpicker.config()

        logger.info(f'variant: {kernelpicker.variant}')
