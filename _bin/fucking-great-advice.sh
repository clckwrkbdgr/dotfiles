#!/bin/bash
# fucking-great-advice.sh - prints random fortunes.

/usr/bin/printf "$(wget -q -O - fucking-great-advice.ru/api/random | awk -F \" '{print $8}' | sed 's/\&nbsp;/ /g')\n" 
