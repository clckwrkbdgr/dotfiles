test: test-python test-bash
	
test-python: test-python3 test-python2

test-python3:
	@mkdir -p ~/.cache/pytest/config
	@echo "Running Py3 tests for PYTEST='$${PYTEST}'"
	@python3 -m coverage run -m unittest "$${PYTEST:-discover}"
	@python3 -m coverage report -m

test-python2:
	@mkdir -p ~/.cache/pytest/config
	@echo "Running Py2 tests for PYTEST='$${PYTEST}'"
	@python2 -m coverage run -m unittest "$${PYTEST:-discover}"
	@python2 -m coverage report -m

test-bash:
	# TODO specific bash test like PYTEST
	@echo 'Running test for bash scripts'
	@for scriptname in test/test_*.bash; do echo $$scriptname; $$scriptname || exit 1; done

# TODO some QUIET env var instead, and merge these two sets of rules.
quiet-test: quiet-test-python quiet-test-bash

quiet-test-python:
	@mkdir -p ~/.cache/pytest/config
	@coverage run -m unittest discover -q
	@coverage report -m

quiet-test-bash:
	@for scriptname in test/test_*.bash; do echo $$scriptname; $$scriptname || exit 1; done

.PHONY: test
