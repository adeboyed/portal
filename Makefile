all: portal

PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
MANDIR ?= $(PREFIX)/man
SHAREDIR ?= $(PREFIX)/share
PYTHON ?= /usr/bin/env python3

.PHONY: all clean portal

clean:
	rm -rf portal
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	name '*~' -exec rm --force  {} 

install: portal
	install -d $(DESTDIR)$(BINDIR)
	install -m 755 portal $(DESTDIR)$(BINDIR)

portal: portalcli/*.py
	mkdir -p zip
	cp -r src zip/portal
	touch -t 200001010101 zip/portal/*.py
	mv zip/portal/__main__.py zip/
	cd zip ; zip -q ../portal portal/*.py __main__.py
	rm -rf zip
	echo '#!$(PYTHON)' > portal
	cat portal.zip >> portal
	rm portal.zip
	chmod a+x portal