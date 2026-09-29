#!/usr/bin/env bash
# Exercise the portal contract without opening windows or touching real files.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
picker=$root/home/dot_local/bin/executable_yazi-file-picker
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
mkdir -p "$work/bin" "$work/tmp" "$work/folder with spaces"
export TMPDIR=$work/tmp
export MOCK_LOG=$work/argv MOCK_SELECTION=$work/selection MOCK_CWD=$work/cwd
export MOCK_FAIL=0 MOCK_SAVE_STATUS=0
cat > "$work/bin/st" <<'MOCK'
#!/bin/bash
printf '%s\0' "$@" > "$MOCK_LOG"
[[ $MOCK_FAIL == 0 ]] || exit 17
for arg in "$@"; do
    case $arg in
        --chooser-file=*) [[ ! -f $MOCK_SELECTION ]] || cp -- "$MOCK_SELECTION" "${arg#*=}" ;;
        --cwd-file=*) [[ ! -f $MOCK_CWD ]] || cp -- "$MOCK_CWD" "${arg#*=}" ;;
    esac
done
exit 0
MOCK
cat > "$work/bin/zenity" <<'MOCK'
#!/bin/bash
[[ $GTK_USE_PORTAL == 0 && $GDK_DEBUG == no-portals ]] || exit 23
printf '%s\0' "$@" > "$MOCK_LOG"
[[ $MOCK_SAVE_STATUS == 0 ]] || exit "$MOCK_SAVE_STATUS"
cat -- "$MOCK_SELECTION"
MOCK
chmod +x "$work/bin/st" "$work/bin/zenity"
export PATH=$work/bin:$PATH
first="$work/a 'quoted' \"file\" \$(touch INJECTED) \`echo nope\`.txt"
second="$work/second file.txt"
touch -- "$first" "$second"
printf '%s\n' "$first" "$second" > "$MOCK_SELECTION"
bash "$picker" 0 0 0 "$first" "$work/result" 0
[[ $(cat "$work/result") == "$first" ]]
mapfile -d '' -t argv < "$MOCK_LOG"
[[ ${argv[0]} == -c && ${argv[1]} == yazi-file-picker ]]
[[ ${argv[-1]} == "$first" && ${argv[-2]} == -- ]]
[[ ! -e INJECTED ]]
bash "$picker" 1 0 0 "$work" "$work/result" 0
cmp "$MOCK_SELECTION" "$work/result"

# File cancellation clears any stale result, including when cwd is available.
rm "$MOCK_SELECTION"
printf '%s\n' "$work" > "$MOCK_CWD"
bash "$picker" 0 0 0 "$work" "$work/result" 0
[[ ! -s $work/result ]]
# Directory q accepts cwd; Shift+Q writes neither file and cancels.
bash "$picker" 0 1 0 "$work" "$work/result" 0
cmp "$MOCK_CWD" "$work/result"
rm "$MOCK_CWD"
bash "$picker" 0 1 0 "$work" "$work/result" 0
[[ ! -s $work/result ]]
# Only directories survive directory mode, even when Yazi selected files too.
printf '%s\n' "$first" "$work/folder with spaces" "$work" > "$MOCK_SELECTION"
bash "$picker" 0 1 0 "$work" "$work/result" 0
[[ $(cat "$work/result") == "$work/folder with spaces" ]]
bash "$picker" 1 1 0 "$work" "$work/result" 0
printf '%s\n' "$work/folder with spaces" "$work" > "$work/expected"
cmp "$work/expected" "$work/result"
# Save requests may name a file that does not exist yet.
printf '%s\n' "$work/new file.txt" > "$MOCK_SELECTION"
bash "$picker" 0 0 1 "$work/new file.txt" "$work/result" 0
cmp "$MOCK_SELECTION" "$work/result"
mapfile -d '' -t argv < "$MOCK_LOG"
[[ ${argv[0]} == --file-selection && ${argv[1]} == --save ]]
[[ ${argv[2]} == --confirm-overwrite && ${argv[3]} == "--filename=$work/new file.txt" ]]
MOCK_SAVE_STATUS=1 bash "$picker" 0 0 1 "$work/new file.txt" "$work/result" 0
[[ ! -s $work/result ]]
if MOCK_SAVE_STATUS=5 bash "$picker" 0 0 1 "$work/new file.txt" "$work/result" 0; then
    printf 'Save dialog failure was ignored\n' >&2
    exit 1
else
    [[ $? == 5 ]]
fi
[[ ! -s $work/result ]]
export MOCK_FAIL=1
if bash "$picker" 0 0 0 "$work" "$work/result" 0; then
    printf 'Terminal failure was ignored\n' >&2
    exit 1
fi
[[ ! -s $work/result ]]
[[ -z $(find "$TMPDIR" -mindepth 1 -print -quit) ]]
[[ -z $(find "$work" -name '.yazi-file-picker.*' -print -quit) ]]
printf 'preserve\n' > "$work/protected"
ln -s "$work/protected" "$work/symlink"
if bash "$picker" 0 0 0 "$work" "$work/symlink" 0 2>/dev/null; then
    printf 'Unsafe output symlink was accepted\n' >&2
    exit 1
fi
[[ $(cat "$work/protected") == preserve ]]
printf 'Yazi file picker contract checks passed.\n'
