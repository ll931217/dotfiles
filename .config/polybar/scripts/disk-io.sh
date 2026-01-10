#!/bin/bash

INTERVAL=1
DEVICE="sdb"

OUTPUT=$(iostat -d -k $INTERVAL 2 | awk -v dev="$DEVICE" '
BEGIN { found_first = 0; found_second = 0 }

$1 == dev {
    if (!found_first) {
        found_first = 1
        next
    }

    read_kbs = $3
    write_kbs = $4

    read_bars = int(read_kbs / 50)
    write_bars = int(write_kbs / 50)

    if (read_bars > 7) read_bars = 7
    if (write_bars > 7) write_bars = 7
    if (read_bars < 0) read_bars = 0
    if (write_bars < 0) write_bars = 0

    read_bar_str = ""
    write_bar_str = ""

    for (i = 0; i < 7; i++) {
        if (i < read_bars) read_bar_str = read_bar_str "█"
        else read_bar_str = read_bar_str " "
    }

    for (i = 0; i < 7; i++) {
        if (i < write_bars) write_bar_str = write_bar_str "█"
        else write_bar_str = write_bar_str " "
    }

    printf "R:%3dK/s%s W:%3dK/s%s", int(read_kbs), read_bar_str, int(write_kbs), write_bar_str
    exit
}
')

if [ -z "$OUTPUT" ]; then
    echo "R:  0K/s       W:  0K/s      "
else
    echo "$OUTPUT"
fi
