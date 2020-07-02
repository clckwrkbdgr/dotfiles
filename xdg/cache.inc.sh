# Customizations for XDG compliance: XDG_CACHE_HOME
# These could easily be cleared at any time without loss of any important data.
mkdir -p "$XDG_CACHE_HOME/vim"
export NPM_CONFIG_CACHE="$XDG_CACHE_HOME/npm"
