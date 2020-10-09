Git
================================================================================

## Git shows files as deleted after pull when they're missing even if they're not in sparse checkout file.

After dotfiles were pulled and some dir was _git-moved_ to another location, it appears now as `deleted` in git status on the sparse repo, but it is missing from `sparse-checkout` file.

To fix this issue, git object tree should be re-read:
	
	# Update your working directory with 
	git read-tree -mu HEAD

When git branch shows files that were deleted in another branch and never existed in the current one thanks to the sparse checkout, do the checkout once again:

	git checkout <current_branch>

This should recalculate index and fix issues with showing files not belonging to the branch.

## Git push changes to the same branch in the remote non-bare repository.

	error: refusing to update checked out branch: refs/heads/master
	error: By default, updating the current branch in a non-bare repository
	error: is denied, because it will make the index and work tree inconsistent
	error: with what you pushed, and will require 'git reset --hard' to match
	error: the work tree to HEAD.

The solution is to go to `remote` repo (actual dir) and switch other branch (`git checkout [-b] otherbranch`).
Then return back to `working` repo, `git pull origin master`. Now `working` repo is ok.
Now you can go to `remote` repo and `git checkout master`.

But the **better solution** is to create a separate branch, e.g. `nethome`, checkout it on the `nethome` location and commit only to that branch, then push to the origin (having `nethome` bracnh there too). Then `git merge nethome` in the master repo, having `master` branch checked out.

Next, when committing changes to master branch, simply `git pull origin` on the nethome repo and `git merge master`.

	       D:\master            X:\nethome

	   +---> master [*] --pull--> master     
	   |       ^                    |        [local]
	   |     merge                merge         |
	[local]    |                    V           |
	         nethome <----push--- nethome [*] <-+

## Git attributes not working

Sometimes after `git read-tree` attributes from `.gitattributes` stop working, e.g. filter is not filtering any more and file appears with ghost changes.

`git check-attr -a <path_to_file>` ignores changes in `.gitaatributes`.
In the mean time `git check-attr -a --cached <path_to_file>` shows cached filter (differs from changed `.gitattributes`). Need to remove .gitattributes manually, `git st`, `git diff` and then attributes are working.

No real solution has been found at the moment.

## Git merge conflict after remote updates.

Turns out, deleted/conflicted/unfiltered entries are coming from previously stashed working trees.
Looks like after `git stash` and following `git merge ...` commands there were no `git stash pop`, so stash is still containing (now outdated) working tree and trying to re-stash it back on new updates, polluting current working tree.

So the final solution is to `git stash clear`, making sure that those stashed changes are unneeded.

## How to create subrepo for, like, network-home location with Unix-only routines

	mkdir ~/local
	cd ~/local
	git init
	git config core.sparseCheckout true
		# Now create sparse-checkout list.
		echo '.gitignore' > .git/info/sparse-checkout
	git remote add origin <remote>/.local
	git fetch origin master
	git checkout master
	# Voila!
	ls
	# .git   .gitignore

	# Now can be moved to ~/.local

	# Don't forget! (on unix)
	chmod -R o-rwx,g-rwx ~/.local

## git clone https://...: 443 timed out

`ping wpad`

if ok:

* `firefox http://wpad/wpad.dat`
* grep PROXY, get addr:port
* `git config --system http.proxy <addr:port>`

## How to extract part of SVN repo and merge as part of Git repo

1. Dump whole SVN directory: `svnadmin dump projects.repo >extracted.dump`
2. Prepare list `extracted.prefixes.lst` of excluded paths (shell patterns). For dirs which content is excluded completely via `subdir/*` there might be need for additional pattern to remove the directory itself: `subdir`.
3. Filter dumped directory to a new, horrible one: `svndumpfilter exclude --skip-missing-merge-sources --pattern --targets rogue.prefixes.lst <projects.dump >extracted.dump`
4. Create dummy SVN repo: `svnadmin create dummy --pre-1.4-compatible`
5. Load filtered dump to new repo: `svnadmin load dummy <extracted.dump`
6. Clone dummy SVN repo as Git: `git svn clone file:///y/dummy extracted`. Note that Git for Windows operates on MinGW paths!
7. Merge created Git repo into existing one:

		cd ~/.local/
		git remote add extracted Y:\extracted\
		git fetch extracted --tags
		git merge extracted/master
		git remote remove extracted

Windows
================================================================================

## To turn off Win+X hotkeys in Win10

Hot keys usually provides shortcut access to the Start button or other Windows functions. Sometimes we want to disable some of them if they interfere with us. To disable hotkeys in Windows 10, you may follow the steps below:

* Type gpedit in the Search and then click Edit group policy. (This will open Local Group Policy Editor).
* Navigate to User Configuration > Administrative Templates > Windows Components > File Explorer. In the right-side pane, look for Turn off Windows + X hotkeys and double click on it.
* Check Disabled and click OK.
* Restart the computer to make the settings take effect.


Windows Linux Subsystem (WSL)
================================================================================

1. Turn on Developer Mode
  Open Settings -> Update and Security -> For developers
  Select the Developer Mode radio button
2. Open a command prompt. Run `bash`

[https://docs.microsoft.com/en-us/windows/wsl/install-win10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

	$ sudo PowerShell
	> Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
	grep '^State'
	> Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux

Running WSL: `%windir%\system32\bash.exe`

PuTTY
================================================================================

## How to make PuTTY autologin

1. Have public `id_rsa` and private `id_rsa.pub` keys generated and stored somewhere on desktop.
2. Launch `PuTYYGen` (from Start Menu). Select `Conversions -> Import key` and navigate to `id_rsa` key file. Open key file and enter passphrase.
3. Press `Save private key` and save it as `id_rsa.ppk` somewhere (e.g. to `~/.ssh` together with other keys).
4. Have key public key (`id_rsa.pub`) added to `~/.ssh/authorized_keys` on server side. Set `chmod 600 ~/.ssh/authorized_keys`.
5. Run PuTTY with `-i <path to *.ppk>`.
6. If passphrase was specified, start `pageant.exe` from Start Menu, add PuTTY private key in question and enter passphrase. Now all remote connections will not ask for passphrase.

Unix
================================================================================

## Print names of terminfos that support colors (>1)

	cd $(find /usr -type d -name terminfo 2>/dev/null)
	for f in */*; do f=${f##*/}; export TERM=$f; if [ $(tput colors) -gt 1 ]; then echo "$f"; fi; done

## To view SQL value in raw hex mode

	select UTL_RAW.CAST_TO_RAW(<field>)
	from <table>
	where ....
	;

## To view text file in hex-ascii mode

	hexdump -C test.txt

## How to set 4 space tab in bash

Use the tabs command to change the behavior:

	tabs 4

You can use setterm to set this

	setterm -regtabs 4

## stat

GNU `stat` and BSD `stat` are not POSIX utils and moreover have different arguments and usage.

- GNU `stat` uses `-c, --format` for format.
- BSD `stat` uses `-f` for format.
- GNU `stat` without arguments fails.
- BSD `stat` without arguments prints stat of the stdin.

GCC
================================================================================

## How to make gdb break on 'symbol lookup error'

You can `break _dl_signal_error` or `catch syscall exit_group`.

The latter will stop when you process is about to exit regardless of why that is happening.

	set breakpoint pending on
	break _dl_signal_error
	run <stdin.txt
	where

## How to debug dlopen:

<https://gcc.gnu.org/bugzilla/show_bug.cgi?id=42679>

	export LD_DEBUG=all ; program >ld.log 2>&1

Xonsh
================================================================================

## To register `.xsh` files with `xonsh`

* Open Explorer, run `*.xsh` file, find `xonsh.bat` when asked to choose the program (should reside in `%PYTHONHOME%/Scripts`). No restart is needed.
* Open Registry, search for `xonsh` and for each `shell/open/command` key add ` %*` after the `"%1"`. This would allow xonsh scripts to receive full command line and prevent issues like `Unknown environment variable $ARG1`. No restart is needed.
* Add `;.xsh` to `PATHEXT`. Restart all shells after this.

## Xonsh lacks

- does not use `shell=True` when invoking subprocesses
- does not exit with `exit` from xsh scripts
- does not respect `sys.exit()`/`raise SystemExit`, the xonsh process always returns 0.
- There is no way to get list of arguments without the 0, like `"$@"` in bash. Also, `shift`.
- Windows: `${...}.update(os.environ)` results in duplication (case of variable names is ignored)

## Xonsh patch to prevent Windows conhost from breaking after running subprocesses.

```patch
diff -r "C:\\Python36\\Lib\\site-packages\\xonsh/__amalgam__.py" xonsh/__amalgam__.py
13932,13933d13931
<     if builtins.__xonsh__.env.get("XONSH_NO_POPULATE_CONSOLE"):
<         return
diff -r "C:\\Python36\\Lib\\site-packages\\xonsh/proc.py" xonsh/proc.py
369,370d368
<     if builtins.__xonsh__.env.get("XONSH_NO_POPULATE_CONSOLE"):
<         return
```

Python
================================================================================

## PIP for Python 2 prints deprecation warning

	DEPRECATION: Python 2.7 will reach the end of its life on January 1st, 2020. Please upgrade your Python as Python 2.7 won't be maintained after that date. A future version of pip will drop support for Python 2.7. More details about Python 2 support in pip, can be found at https://pip.pypa.io/en/latest/development/release-process/#python-2-support

To disable it, set following environment variable:

	PYTHONWARNINGS=ignore:DEPRECATION::pip._internal.cli.base_command

## To install data along with Python modules in the package

- Set `install_package_data=True` in `setuptools.setup`.
- Add files to `package_data` under key with the name of the package:
	
		package_data = {
			'': ['this file will go nowhere because empty package is not a package.txt'],
			'mypackage': ['data/*txt'], # These files should be stored in source dir under mypackage/data/*txt and will be installed in corresponding directory in site-packages.

- To access installed data, use in target module (part of `mypackage` package):

		content = pkg_resources.resource_string(__name__, os.path.join('data', 'test.txt')).decode('utf-8')

## How to get requirements for pypi package without instaling

	https://pypi.python.org/pypi/<package_name>/json
	data['info']['requires_dist']

Firefox
================================================================================

## Firefox: Disable opening new tabs from links

Navigate to `about:config`

	browser.link.open_newwindow                      1
	browser.link.open_newwindow.restriction          0
	browser.link.open_newwindow.override.external    3

## To reduce size of `places.sqlite` in Firefox profile

Firefox: `about:support` -> 'Places Database' -> 'Verify Integrity'
