#!/bin/bash
LOCK="/tmp/playerctl_${1}.lock"

if [ ! -f "$LOCK" ]; then
    touch "$LOCK"
    playerctl "$1"
    sleep 1
    rm "$LOCK"
fi