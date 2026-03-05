#!/bin/bash

choice=$(printf "%s\n%s\n%s\n%s\n%s" Lock Suspend Logout Reboot Shutdown | rofi -dmenu -theme $HOME/.config/rofi/power.rasi -p "Power")

case "$choice" in
    Lock)     hyprlock ;;
    Suspend)  systemctl suspend ;;
    Logout)   hyprctl dispatch exit ;;
    Reboot)   systemctl reboot ;;
    Shutdown) systemctl poweroff ;;
esac
