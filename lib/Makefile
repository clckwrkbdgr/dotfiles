test: test-python test-bash
	
test-python:
	@mkdir -p ~/.cache/pytest/config
	@echo "Running test for PYTEST='$${PYTEST}'"
	@coverage run -m unittest "$${PYTEST:-discover}"
	@coverage report -m

test-bash:
	# TODO specific bash test like PYTEST
	@echo 'Running test for bash scripts'
	@for scriptname in test/test_*.bash; do $$scriptname || exit 1; done

# TODO some QUIET env var instead, and merge these two sets of rules.
quiet-test: quiet-test-python quiet-test-bash

quiet-test-python:
	@mkdir -p ~/.cache/pytest/config
	@coverage run -m unittest discover -q
	@coverage report -m

quiet-test-bash:
	@for scriptname in test/test_*.bash; do $$scriptname || exit 1; done

.PHONY: test
