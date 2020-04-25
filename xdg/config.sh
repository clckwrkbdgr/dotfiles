# Customizations for XDG compliance: XDG_CONFIG_HOME
# Configurations. Should be stored under VCS.
export GIMP2_DIRECTORY="$XDG_CONFIG_HOME/gimp"
export MPLAYER_HOME="$XDG_CONFIG_HOME/mplayer"
export VIMPERATOR_INIT=":source $XDG_CONFIG_HOME/vimperator/vimperatorrc"
export VIMPERATOR_RUNTIME="$XDG_CONFIG_HOME/vimperator"
export VIMINIT='let $MYVIMRC="'"$XDG_CONFIG_HOME"'/vim/vimrc" | source $MYVIMRC'
export MAILRC=~/.config/mailx/mailrc
export PENTADACTYL_RUNTIME=$XDG_CONFIG_HOME/pentadactyl
export GTK2_RC_FILES="$XDG_CONFIG_HOME/gtk-2.0/gtkrc"
export XRE_PROFILE_PATH="$XDG_CONFIG_HOME/firefox"
