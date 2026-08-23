#!/bin/bash

DF_OUTPUT=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')

if [ -n "$DF_OUTPUT" ]; then
    USAGE_PERCENT=$DF_OUTPUT

    BAR_SEGMENTS=$((USAGE_PERCENT / 15))

    if [ "$BAR_SEGMENTS" -gt 7 ]; then BAR_SEGMENTS=7; fi
    if [ "$BAR_SEGMENTS" -lt 0 ]; then BAR_SEGMENTS=0; fi

    BAR=""

    for i in $(seq 0 6); do
        if [ "$i" -lt "$BAR_SEGMENTS" ]; then
            BAR="${BAR}█"
        else
            BAR="${BAR} "
        fi
    done

    printf "%3d%%%s" "$USAGE_PERCENT" "$BAR"
else
    echo "N/A      "
fi
