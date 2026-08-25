#!/bin/zsh
set -euo pipefail

repo_dir="${0:A:h:h}"
template_dir="${repo_dir}/tools/l2_native_app_template"
output_app="${1:-${HOME}/Desktop/vOICe L2 Native Aspect.app}"

if [[ -e "$output_app" ]]; then
  print -u2 "Refusing to overwrite existing path: ${output_app}"
  exit 2
fi

for required_path in \
  "$template_dir/Info.plist" \
  "$template_dir/vOICe-L2-Native-Launcher" \
  "$repo_dir/server.py" \
  "$repo_dir/web/index.html" \
  "$repo_dir/web/app.js" \
  "$repo_dir/stimuli/4x3/manifest.json"; do
  if [[ ! -f "$required_path" ]]; then
    print -u2 "Missing required file: ${required_path}"
    exit 1
  fi
done

build_complete=0
cleanup_incomplete_output() {
  if [[ "$build_complete" -ne 1 && -e "$output_app" ]]; then
    /bin/rm -rf "$output_app"
  fi
}
trap cleanup_incomplete_output EXIT

/bin/mkdir -p "$output_app/Contents/MacOS" "$output_app/Contents/Resources/runtime"
/bin/cp "$template_dir/Info.plist" "$output_app/Contents/Info.plist"
/bin/cp "$template_dir/vOICe-L2-Native-Launcher" \
  "$output_app/Contents/MacOS/vOICe-L2-Native-Launcher"
/bin/chmod +x "$output_app/Contents/MacOS/vOICe-L2-Native-Launcher"

runtime_dir="$output_app/Contents/Resources/runtime"
/bin/cp "$repo_dir/server.py" "$runtime_dir/server.py"
/bin/cp -R "$repo_dir/web" "$repo_dir/stimuli" "$runtime_dir/"
/usr/bin/find "$runtime_dir" -name '__pycache__' -type d -prune -exec /bin/rm -rf {} +
/usr/bin/codesign --force --deep --sign - "$output_app"
/usr/bin/codesign --verify --deep --strict "$output_app"
build_complete=1
print "Built vOICe L2 Native Aspect launcher: ${output_app}"
