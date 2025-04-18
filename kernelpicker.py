from dnfpluginscore import logger

import dnf
import platform


def get_major_version(version):
    return '.'.join(version.split('.')[:2])


class KernelPicker(dnf.Plugin):
    name = 'kernelpicker'

    VARIANT_6_1 = '6.1'
    VARIANT_6_12 = '6.12'
    VARIANT_DEFUALT = VARIANT_6_1
    VARIANTS = {
        VARIANT_6_1,
        VARIANT_6_12
    }

    def __init__(self, base, cli):
        super().__init__(base, cli)

        uname_r = platform.release()
        version, rest = uname_r.split('-')
        release = '.'.join(rest.split('.')[:3])

        self.version = version
        self.release = release

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
        self.major_version = self.variant
        logger.debug(f'Kernel variant: {self.major_version}')

    def sack(self):
        self.set_major_version()
