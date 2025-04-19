from dnfpluginscore import _, logger

import dnf
import platform


class KernelPicker(dnf.Plugin):
    name = 'kernelpicker'

    VARIATN_DEFUALT = '6.1'
    VARIANT_6_1 = '6.1'
    VARIANT_6_12 = '6.12'
    VARIANTS = {
        VARIANT_6_1,
        VARIANT_6_12
    }

    PACKAGE_NAMES = {
        'base': [
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

    QUERIES = {
        VARIANT_6_1: [
            {'version__lt': '6.1.0'},
            {'version__gte': '6.2.0'}
        ],
        VARIANT_6_12: [
            {'version__lt': '6.12.0'},
            {'version__gte': '6.13.0'}
        ]
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.cli:
            self.cli.register_command(KernelPickerCommand)

    def set_variant(self, variant):
        if variant in self.VARIANTS:
            self.variant = variant
            logger.debug(_(f'Kernel variant: {variant}'))
            return True

        return False

    def config(self):
        cp = self.read_config(self.base.conf)

        # /etc/dnf/plugins/kernelpicker.conf
        if cp and cp.has_section('main') and cp.has_option('main', 'variant'):
            variant = cp.get('main', 'variant')

            if self.set_variant(variant):
                return

            message = _(f'Ignoring kernel variant in kernelpicker.conf: \'{variant}\'')
            if not variant:
                logger.debug(message)
            else:
                logger.warning(message)

        # uname -r
        variant = '.'.join(platform.release().split('.')[:2])

        if not self.set_variant(variant):
            logger.warning(_(f'Ignoring kernel variant of $(uname -r): \'{variant}\''))
            self.set_variant(self.VARIATN_DEFUALT)

    def get_excluded_base(self, packages):
        excluded = packages.filter(empty=True)

        for name in self.PACKAGE_NAMES['base'] + self.PACKAGE_NAMES['namespaced']:
            base = packages.filter(name__eq=name)

            for query in self.QUERIES[self.variant]:
                excluded = excluded.union(base.filter(**query))

        return excluded

    def get_excluded_packages(self):
        packages = self.base.sack.query()

        excluded = packages.filter(empty=True)
        excluded = excluded.union(self.get_excluded_base(packages))

        return excluded

    def sack(self):
        excluded = self.get_excluded_packages()

        logger.debug(
            _('Filtered packages\n  %s\n'),
            '\n  '.join(
                f'{query.name}-{query.version}.{query.release}.{query.arch} ({query.reponame})'
                for query in excluded.run()
            )
        )

        self.base.sack.add_excludes(excluded)


class KernelPickerCommand(dnf.cli.Command):
    aliases = ('kernelpicker',)
    summary = _('Configure preferred kernel package variant')

    @staticmethod
    def set_argparser(parser):
        parser.add_argument(
            'variant',
            nargs='?',
            choices=KernelPicker.VARIANTS,
            help=_('Set the preference for kernel package variant, '
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
