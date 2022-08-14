all:
	python setup.py

verbose:
	python setup.py verbose

deploy:
	git push local master --tags
	cd $(XDG_CONFIG_HOME); git pull local master
