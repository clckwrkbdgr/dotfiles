setterm -blank 0 -powersave off -powerdown 0
xset -dpms
xset s noblank
xset s off

xmodmap -e 'keycode 87 = 1 exclam'
xmodmap -e 'keycode 88 = 2 at'
xmodmap -e 'keycode 89 = 3 numbersign'
xmodmap -e 'keycode 83 = 4 dollar'
xmodmap -e 'keycode 84 = 5 percent'
xmodmap -e 'keycode 85 = 6 asciicircum'
xmodmap -e 'keycode 79 = 7 ampersand'
xmodmap -e 'keycode 80 = 8 parenleft'
xmodmap -e 'keycode 81 = 9 parenright'
xmodmap -e 'keycode 90 = 0 equal'

xrdb -load ~/.config/Xresources
