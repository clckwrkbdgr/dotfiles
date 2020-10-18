#!/bin/sh

workstation_on_battery()
{
	upower -i /org/freedesktop/UPower/devices/DisplayDevice | grep state | grep -q dis
}

workstation_lock()
{
	xflock4
}
