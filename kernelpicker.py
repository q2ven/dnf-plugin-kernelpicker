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
