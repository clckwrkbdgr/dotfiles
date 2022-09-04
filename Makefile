all:
	python setup.py

test:
	@cd lib; $(MAKE) TESTCASE=$(TESTCASE)

verbose:
	python setup.py verbose

deploy:
	git push local master --tags
	cd $(XDG_CONFIG_HOME); git pull local master
