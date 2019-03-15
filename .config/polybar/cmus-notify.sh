#!/usr/bin/env bash
playerctl metadata --format '{{xesam:title}} - {{xesam:artist}} • {{lc(status)}} •  {{duration(position)}} / {{duration(mpris:length)}}'
