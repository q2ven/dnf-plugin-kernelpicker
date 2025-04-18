.PHONY = install clean

CONFIG_PATH = /etc/dnf/plugins
PLUGIN_PATH = /usr/lib/python3.9/site-packages/dnf-plugins

install:
	cp kernelpicker.conf $(CONFIG_PATH)
	cp kernelpicker.py $(PLUGIN_PATH)

clean:
	rm -f $(PLUGIN_PATH)/kernelpicker.py
