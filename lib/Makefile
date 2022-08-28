MAKEFILE := $(CURDIR)/$(firstword $(MAKEFILE_LIST))
test:
	@unittest $(TESTCASE)
	
test-python: test-python3 test-python2

test-python3:
	@echo "$(MAKEFILE): deprecated, use 'unittest -p py3 [...]' instead"
	@unittest -p py3 "$${PYTEST}"

test-python2:
	@echo "$(MAKEFILE): deprecated, use 'unittest -p py2 [...]' instead"
	@unittest -p py2 "$${PYTEST}"

test-bash:
	@echo "$(MAKEFILE): deprecated, use 'unittest -p bash [...]' instead"
	@unittest -p bash

# TODO some QUIET env var instead, and merge these two sets of rules.
quiet-test: quiet-test-python quiet-test-bash

quiet-test-python:
	@echo "$(MAKEFILE): deprecated, use 'unittest --quiet -p py2 py3 [...]' instead"
	@unittest --quiet -p py2 py3 "$${PYTEST}"

quiet-test-bash:
	@echo "$(MAKEFILE): deprecated, use 'unittest --quiet -p bash [...]' instead"
	@unittest --quiet -p bash

.PHONY: test
