#!/bin/sh
cd "$XDG_CONFIG_HOME"
python setup.py ${DAILYUPDATE_VERBOSE:+"--verbose"}
