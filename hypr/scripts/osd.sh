#!/bin/bash

get_vol() {
    wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{printf "%d", $2 * 100}' | sed 's/\.//'
}

get_bright() {
    brightnessctl -m | awk -F, '{print substr($4, 0, length($4)-1)}'
}

osd() {
    local icon="$1" pct="$2" class="$3"
	local filled=$(( pct * 15 / 100 ))
	local empty=$(( 15 - filled ))
	local bar=
    for ((i=0; i<filled; i++)); do bar+="━"; done
    for ((i=0; i<empty; i++)); do bar+="─"; done
    export osd="{\"text\": \"$icon $bar $pct%\", \"class\": \"$class\"}"
    kill "$osd_pid" 2>/dev/null
    if [[ -z "$bar_pid" ]] || ! kill -0 "$bar_pid" 2>/dev/null; then
        waybar -c "$HOME/.config/waybar/osd-config.jsonc" -s "$HOME/.config/waybar/osd-style.css" &
        bar_pid=$!
    else
        pkill -RTMIN+8 -f "waybar -c $HOME/.config/waybar/osd-config.jsonc"
    fi
	(sleep 1; kill "$bar_pid" 2>/dev/null) &
    osd_pid=$!
}

case "$1" in
    vup)
        wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 2%+
        if wpctl get-volume @DEFAULT_AUDIO_SINK@ | grep -q MUTED; then
            osd "󰖁" "$(get_vol)" "muted"
        else
            osd "󰕾" "$(get_vol)" "volume"
        fi
        ;;
    vdown)
        wpctl set-volume @DEFAULT_AUDIO_SINK@ 2%-
        if wpctl get-volume @DEFAULT_AUDIO_SINK@ | grep -q MUTED; then
            osd "󰖁" "$(get_vol)" "muted"
        else
            osd "󰕾" "$(get_vol)" "volume"
        fi
        ;;
    mute)
        wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
        if wpctl get-volume @DEFAULT_AUDIO_SINK@ | grep -q MUTED; then
            osd "󰖁" "$(get_vol)" "muted"
        else
            osd "󰕾" "$(get_vol)" "volume"
        fi
        ;;
    bup)
        brightnessctl -e4 -n2 set 5%+
        osd "󰃠" "$(get_bright)" "brightness"
        ;;
    bdown)
        brightnessctl -e4 -n2 set 5%-
        osd "󰃞" "$(get_bright)" "brightness"
        ;;
esac
