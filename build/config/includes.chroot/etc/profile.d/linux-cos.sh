# Linux-C.O.S shell integration (bash + zsh sourced via /etc/zsh/zshrc.d or ~/.zshrc)
# BlackArch tools behave like native commands: type the name and `cos` runs
# it from the container (or tells you how to get it).
case "$-" in *i*) ;; *) return 0 2>/dev/null || exit 0 ;; esac
[ -x /usr/local/bin/cos ] || return 0 2>/dev/null || exit 0

if [ -n "${BASH_VERSION:-}" ]; then
  command_not_found_handle() { /usr/local/bin/cos _cnf "$@"; rc=$?; [ $rc -eq 127 ] && printf '%s: command not found\n' "$1" >&2; return $rc; }
elif [ -n "${ZSH_VERSION:-}" ]; then
  command_not_found_handler() { /usr/local/bin/cos _cnf "$@"; rc=$?; [ $rc -eq 127 ] && printf 'zsh: command not found: %s\n' "$1" >&2; return $rc; }
fi

# tab completion for `cos`
if [ -n "${BASH_VERSION:-}" ]; then
  _cos_complete() {
    local cur=${COMP_WORDS[COMP_CWORD]} prev=${COMP_WORDS[COMP_CWORD-1]}
    case "$prev" in
      mode) COMPREPLY=($(compgen -W "dual red blue" -- "$cur")) ;;
      fx)   COMPREPLY=($(compgen -W "auto high low off" -- "$cur")) ;;
      cos)  COMPREPLY=($(compgen -W "tools run install mode fx hub doctor stack ai shell version status" -- "$cur")) ;;
      tools) COMPREPLY=($(compgen -W "list search info cats" -- "$cur")) ;;
      run|install|info) COMPREPLY=($(compgen -W "$(cut -f1 /usr/share/linux-cos/tools.tsv)" -- "$cur")) ;;
    esac
  }
  complete -F _cos_complete cos
fi
