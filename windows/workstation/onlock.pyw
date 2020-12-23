# Task Scheduler -> New schedule -> Triggers -> On workstation lock.
# NOTE: Use full path to python executable.
# NOTE: It is advised to use 'pythonw.exe' to suppress cmd window.
import clckwrkbdgr.workstation
clckwrkbdgr.workstation.onlock()
