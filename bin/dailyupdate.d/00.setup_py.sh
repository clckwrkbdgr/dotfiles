#!/bin/sh
cd "$XDG_CONFIG_HOME"
python setup.py --no-network ${DAILYUPDATE_VERBOSE:+"--verbose"}
