#!/usr/bin/env bash
# Lint the Stage 1 packages and report every violation.
#
# ADVISORY BY DESIGN: this script always exits 0. Style violations must not
# make pull requests fail while the existing style backlog is being cleared.
# Stage 3 can make this blocking once that backlog is gone.
set -uo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/.." && pwd)"
packages_file="$script_dir/custom_packages.txt"
cd "$repo_root"

: "${ROS_DISTRO:=humble}"

# setup.bash can read unset variables, so temporarily disable nounset.
set +u
# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO}/setup.bash"
set -u

mapfile -t package_dirs < <(sed -e 's/#.*//' -e '/^[[:space:]]*$/d' "$packages_file")

report_dir="$(mktemp -d)/lint"
mkdir -p "$report_dir"

# count_of <logfile> <regex>: print the number of matching lines, or zero.
count_of() {
  grep -cE "$2" "$1" 2>/dev/null || true
}

echo "=== Linting ${#package_dirs[@]} Stage 1 package directories ==="
printf '  %s\n' "${package_dirs[@]}"

for package_dir in "${package_dirs[@]}"; do
  ament_cpplint "$package_dir" >"$report_dir/$package_dir.cpplint" 2>&1 || true
  ament_uncrustify "$package_dir" >"$report_dir/$package_dir.uncrustify" 2>&1 || true
  ament_flake8 "$package_dir" >"$report_dir/$package_dir.flake8" 2>&1 || true
  ament_xmllint "$package_dir" >"$report_dir/$package_dir.xmllint" 2>&1 || true
done

echo
echo '=================== FULL LINT OUTPUT ==================='
for report in "$report_dir"/*; do
  [[ -s "$report" ]] || continue
  echo
  echo "----- $(basename "$report") -----"
  cat "$report"
done

summary="${GITHUB_STEP_SUMMARY:-/dev/stdout}"
{
  echo '## Lint report (advisory)'
  echo
  echo 'Violations below do not fail CI. See `ci/lint.sh` for details.'
  echo
  echo '| Package | cpplint | uncrustify | flake8 | xmllint |'
  echo '| --- | ---: | ---: | ---: | ---: |'
} >>"$summary"

total=0
for package_dir in "${package_dirs[@]}"; do
  cpplint_count=$(count_of "$report_dir/$package_dir.cpplint" ':[0-9]+:  ')
  uncrustify_count=$(count_of "$report_dir/$package_dir.uncrustify" '^Code style divergence')
  flake8_count=$(count_of "$report_dir/$package_dir.flake8" ':[0-9]+:[0-9]+: ')
  xmllint_count=$(count_of "$report_dir/$package_dir.xmllint" ':[0-9]+:')
  total=$((total + cpplint_count + uncrustify_count + flake8_count + xmllint_count))
  echo "| \`$package_dir\` | $cpplint_count | $uncrustify_count | $flake8_count | $xmllint_count |" >>"$summary"
done

{
  echo
  echo "**Total: $total** (cpplint and flake8 count individual violations;"
  echo 'uncrustify counts files that differ from the canonical format.)'
} >>"$summary"

echo
echo "=== Total violations: $total (advisory, not failing the build) ==="
exit 0
