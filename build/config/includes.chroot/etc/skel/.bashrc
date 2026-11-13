# Linux-C.O.S bash configuration (zsh is the default shell; this keeps bash usable)
case $- in *i*) ;; *) return ;; esac
HISTSIZE=50000; HISTFILESIZE=50000; HISTCONTROL=ignoreboth:erasedups
shopt -s histappend checkwinsize autocd 2>/dev/null
alias ls='ls --color=auto' ll='ls -lah --color=auto' grep='grep --color=auto'
[ -r /etc/bash_completion ] && . /etc/bash_completion
[ -r /etc/profile.d/linux-cos.sh ] && . /etc/profile.d/linux-cos.sh
export STARSHIP_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/linux-cos/starship.toml"
if command -v starship >/dev/null; then [ -r "$STARSHIP_CONFIG" ] || cos session prompt >/dev/null 2>&1; eval "$(starship init bash)"; fi
