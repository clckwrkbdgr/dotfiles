all:
	python setup.py

test: test-xdg

test-xdg: bin/xdg
	. xdg && [ -d "$$XDG_CONFIG_HOME" ]
	. xdg && [ -d "$$XDG_DATA_HOME" ]
	. xdg && [ -d "$$XDG_CACHE_HOME" ]
	xdg && [ -h ~/.bashrc ]
	xdg && [ -h ~/.profile ]
	xdg && [ -h ~/.xinitrc ]
	xdg && [ -h ~/.w3m ]
	xdg && [ -h ~/.macromedia ]
	xdg && [ -h ~/.adobe ]
	. xdg && [ -d "$$XDG_CACHE_HOME/vim" ]

