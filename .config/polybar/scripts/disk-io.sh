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

    printf "R:%3dK/s W:%3dK/s", int(read_kbs), int(write_kbs)
    exit
}
')

if [ -z "$OUTPUT" ]; then
  echo "R:  0K/s W:  0K/s"
else
  echo "$OUTPUT"
fi
