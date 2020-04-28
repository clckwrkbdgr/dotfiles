test:
	@mkdir -p ~/.cache/pytest/config
	@echo "Running test for PYTEST='$${PYTEST}'"
	@coverage run -m unittest "$${PYTEST:-discover}"
	@coverage report -m

quiet-test:
	@mkdir -p ~/.cache/pytest/config
	@coverage run -m unittest discover -q
	@coverage report -m
