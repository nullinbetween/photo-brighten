#!/bin/bash
# Double-click on macOS: choose a folder → enter a brightness → brightened copies are written to brighten/ inside it.
# The processing is in brighten.py next to this file. Local only, nothing is uploaded. This script never installs packages.
cd "$(dirname "$0")" || exit 1
echo ""
echo "💡 Batch Brighten  python3: $(python3 --version 2>&1)"

# 0) Check the dependency (no automatic install)
if ! python3 -c "import PIL" 2>/dev/null; then
  echo "❌ Pillow is required but is not installed for this python3."
  echo "   Install it yourself in Terminal (versions in requirements.txt):"
  echo "     python3 -m pip install --user -r \"$(pwd)/requirements.txt\""
  echo "   Then double-click this file again."
  read -r -p "Press Enter to close..."; exit 1
fi

# 1) Choose a folder (macOS dialog)
FOLDER=$(osascript -e 'try' -e 'POSIX path of (choose folder with prompt "Choose the photo folder to brighten (brighten/ will be created inside it)")' -e 'end try' 2>/dev/null)
[ -z "$FOLDER" ] && { echo "No folder chosen, exiting."; read -r -p "Press Enter to close..."; exit 0; }

# 2) Brightness (OK keeps the default; 0.1–5.0, 1.0 = unchanged)
BRI=$(osascript -e 'try' -e 'text returned of (display dialog "Brightness factor (0.1–5.0, 1.0 = unchanged): higher if too dark, lower if too bright" default answer "1.45" buttons {"OK"} default button "OK")' -e 'end try' 2>/dev/null)
[ -z "$BRI" ] && BRI=1.45
echo "Folder: $FOLDER"
echo "Files with the same name in brighten/ will be overwritten; your original photos are never modified."
echo ""

python3 brighten.py "$FOLDER" --brightness "$BRI"
STATUS=$?
echo ""
[ $STATUS -eq 0 ] || echo "⚠ Finished with errors (code $STATUS) — see the messages above."
read -r -p "Press Enter to close..."
exit $STATUS
