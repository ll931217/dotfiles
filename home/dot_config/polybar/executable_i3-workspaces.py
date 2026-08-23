#!/usr/bin/env python3
import json, subprocess


def get_workspaces():
    result = subprocess.run(
        ["i3-msg", "-t", "get_workspaces"], capture_output=True, text=True, check=False
    )
    return json.loads(result.stdout)


workspaces = get_workspaces()
current = next((ws for ws in workspaces if ws.get("focused")), {"num": 0})["num"]

formatted = []
for ws in sorted(workspaces, key=lambda x: x.get("num", 0)):
    num = ws.get("num", 0)
    name = ws.get("name", str(num))

    if num < current:
        styled = f"%{{F#bac2de}}{name}%{{F-}}"
    elif num == current:
        styled = f"%{{B#94e2d5}}%{{F#181825}}{name}%{{F-}}%{{B-}}"
    else:
        styled = f"%{{B#45475a}}%{{F#bac2de}}{name}%{{F-}}%{{B-}}"

    formatted.append(styled)

print("  ".join(formatted))
