# Linux-C.O.S -- desktop test harness. A kali-rolling image with the same
# desktop stack the ISO ships, running on a virtual X server, so the theme,
# panels, compositor effects, HUD and Hub can be rendered and screenshotted
# without booting the 15 GB ISO.  See tests/desktop/run.sh
FROM kalilinux/kali-rolling
ENV DEBIAN_FRONTEND=noninteractive
# the http.kali.org redirector sometimes picks a mirror that answers 403;
# the official CDN host is stable
RUN for f in /etc/apt/sources.list /etc/apt/sources.list.d/*; do [ -f "$f" ] && sed -i 's#https\?://http.kali.org#http://kali.download#' "$f"; done; \
    printf 'Acquire::Retries "5";\n' > /etc/apt/apt.conf.d/80retries
RUN apt-get update && apt-get install -y --no-install-recommends \
    xfce4 xfce4-terminal xfce4-whiskermenu-plugin xfce4-docklike-plugin \
    xfce4-genmon-plugin xfce4-pulseaudio-plugin xfce4-notifyd xfce4-power-manager \
    thunar xvfb x11-utils x11-apps x11-xserver-utils xdotool imagemagick dbus-x11 \
    picom rofi conky-all python3-gi python3-gi-cairo python3-cairo \
    gir1.2-gtk-3.0 gir1.2-vte-2.91 gir1.2-webkit2-4.1 \
    arc-theme papirus-icon-theme adwaita-icon-theme fonts-inter fonts-jetbrains-mono \
    fonts-noto-color-emoji zsh zsh-autosuggestions zsh-syntax-highlighting \
    starship fastfetch fzf bat eza zoxide nmap mesa-utils libgl1-mesa-dri \
    librsvg2-bin python3-pil jq procps iproute2 sudo \
    && rm -rf /var/lib/apt/lists/*
