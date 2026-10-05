#!/bin/bash
set -euo pipefail
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "iOS export must run on a Mac with Xcode and matching Godot export templates." >&2
  exit 1
fi
: "${APPLE_TEAM_ID:?Set your real Apple team identifier locally. Do not send a password.}"
godot_bin="${GODOT_BIN:-/Applications/Godot.app/Contents/MacOS/Godot}"
project_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_root"
"$godot_bin" --headless --editor --path . --import
"$godot_bin" --headless --path . --script res://tools/configure_ios.gd
mkdir -p build
output_dir="$(mktemp -d "$project_root/build/ios-XXXXXX")"
"$godot_bin" --headless --path . --export-debug iOS "$output_dir/Nocturne.zip"
printf 'Unsigned Xcode export: %s\n' "$output_dir"
printf 'Open the generated Xcode project to configure signing and install on your device.\n'
