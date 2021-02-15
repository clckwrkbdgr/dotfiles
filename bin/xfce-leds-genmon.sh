#!/bin/sh
STATE_IMAGE_PATH=$XDG_RUNTIME_DIR/xfce4/leds/state.png
STATE_TOOLTIP_PATH=$XDG_RUNTIME_DIR/xfce4/leds/state.txt
echo "<img>$STATE_IMAGE_PATH</img>"
echo -n "<tool>"
cat $STATE_TOOLTIP_PATH
echo "</tool>"
date >>~/badger.log
