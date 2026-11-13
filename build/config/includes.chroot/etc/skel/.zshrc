# Linux-C.O.S zsh configuration -- fast, colour-aware, tool-aware.
# Prompt colours follow `cos mode` (generated into ~/.config/linux-cos/starship.toml).

# --- history ------------------------------------------------------------------
HISTFILE=~/.zsh_history
HISTSIZE=50000
SAVEHIST=50000
setopt HIST_IGNORE_ALL_DUPS HIST_IGNORE_SPACE HIST_REDUCE_BLANKS SHARE_HISTORY INC_APPEND_HISTORY
setopt AUTO_CD AUTO_PUSHD PUSHD_IGNORE_DUPS INTERACTIVE_COMMENTS NO_BEEP EXTENDED_GLOB

# --- completion -----------------------------------------------------------------
autoload -Uz compinit && compinit -C
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|=*' 'l:|=* r:|=*'
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*:descriptions' format '%F{cyan}%d%f'

# --- keys -----------------------------------------------------------------------
bindkey -e
bindkey '^[[A' history-beginning-search-backward
bindkey '^[[B' history-beginning-search-forward
bindkey '^[[H' beginning-of-line
bindkey '^[[F' end-of-line
bindkey '^[[3~' delete-char
bindkey '^[[1;5C' forward-word
bindkey '^[[1;5D' backward-word

# --- plugins (installed by the image; skipped if absent) -------------------------------
[ -r /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ] && . /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#5b6a96'
[ -r /usr/share/doc/fzf/examples/key-bindings.zsh ] && . /usr/share/doc/fzf/examples/key-bindings.zsh
[ -r /usr/share/doc/fzf/examples/completion.zsh ] && . /usr/share/doc/fzf/examples/completion.zsh
export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border --color=bg+:#111a33,fg+:#e8eeff,hl:#00e5ff,hl+:#00e5ff,pointer:#ff2e63,prompt:#00e5ff,info:#7f8db8,border:#1c2a52'
command -v zoxide >/dev/null && eval "$(zoxide init zsh)"

# --- aliases --------------------------------------------------------------------------
if command -v eza >/dev/null; then
  alias ls='eza --group-directories-first' ll='eza -lah --group-directories-first --git' lt='eza --tree --level=2'
else
  alias ls='ls --color=auto' ll='ls -lah --color=auto'
fi
command -v batcat >/dev/null && alias cat='batcat --paging=never --style=plain' bat='batcat'
command -v fdfind >/dev/null && alias fd='fdfind'
alias grep='grep --color=auto' ..='cd ..' ...='cd ../..'
alias myip='curl -s https://ifconfig.me; echo'
alias ports='ss -tulpn'
alias serve='python3 -m http.server 8000'
alias cosfetch='fastfetch'

# --- Linux-C.O.S integration ------------------------------------------------------------
# `cos` and BlackArch tools typed as plain commands (see /etc/profile.d/linux-cos.sh)
[ -r /etc/profile.d/linux-cos.sh ] && . /etc/profile.d/linux-cos.sh

# syntax highlighting must be sourced last
[ -r /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ] && . /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# --- prompt -------------------------------------------------------------------------------
export STARSHIP_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/linux-cos/starship.toml"
if command -v starship >/dev/null; then
  [ -r "$STARSHIP_CONFIG" ] || cos session prompt >/dev/null 2>&1
  eval "$(starship init zsh)"
else
  PROMPT='%F{cyan}%n%f@%m %F{red}%~%f %# '
fi
