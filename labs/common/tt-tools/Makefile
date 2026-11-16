# IC102-D: the tools Tiny Tapeout's test and gl_test jobs use, at the
# runner's versions.
#
#   make install                 install into .local/
#   make check-tools             each tool: runner's version, here, workbench
#   make test PROJECT=<dir>      your project's cocotb test, as the test job runs it
#   make help                    every target

PROJECT ?=
SUBMISSION ?=
SHELL := /bin/bash

.PHONY: help install install-gl check-tools test test-icarus13 test-workbench gl-test selftest uninstall

help:
	@echo "make install                       Python 3.11 with cocotb and pytest, Icarus 12.0 and 13.0, into .local/"
	@echo "make install-gl                    also the sky130 standard cells, for make gl-test"
	@echo "make check-tools                   print each version next to the pinned one"
	@echo "make test PROJECT=<dir>            your cocotb test with the test job's tools (Icarus 12.0)"
	@echo "make test-icarus13 PROJECT=<dir>   the same test with gl_test's Icarus 13.0"
	@echo "make test-workbench PROJECT=<dir>  the same test with the workbench's Icarus 14.0"
	@echo "make gl-test PROJECT=<dir> SUBMISSION=<tt_submission dir>"
	@echo "                                   the gate-level test, as the gl_test job runs it"
	@echo "make selftest                      the template's own test, as the test job runs it"
	@echo "make uninstall                     delete .local/"

install:
	./install.sh

install-gl:
	./install.sh gl-pdk

check-tools:
	@./check-tools.sh

define need_project
	@[ -n "$(PROJECT)" ] || { echo "usage: make $@ PROJECT=<your repository folder>"; exit 2; }
endef

test:
	$(need_project)
	./run-test.sh "$(PROJECT)"

test-icarus13:
	$(need_project)
	ICARUS=13 ./run-test.sh "$(PROJECT)"

test-workbench:
	$(need_project)
	ICARUS=workbench ./run-test.sh "$(PROJECT)"

gl-test:
	$(need_project)
	@[ -n "$(SUBMISSION)" ] || { echo "usage: make gl-test PROJECT=<dir> SUBMISSION=<unzipped tt_submission artifact>"; exit 2; }
	./run-gl-test.sh "$(PROJECT)" "$(SUBMISSION)"

selftest:
	./selftest.sh

uninstall:
	rm -rf .local
