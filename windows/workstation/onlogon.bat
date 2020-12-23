@ECHO OFF
REM gpedit.msc -> User Configuration -> Windows Settings -> Scripts (Logon/Logoff) -> Logon
REM Debugging: https://docs.microsoft.com/en-au/archive/blogs/askds/a-treatise-on-group-policy-troubleshootingnow-with-gpsvc-log-analysis
REM NOTE: pythonw should be on system PATH, as these scripts may be executed before proper user environment is set.
pythonw -m clckwrkbdgr.workstation onlogin
