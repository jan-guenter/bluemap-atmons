#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
INSTALLER=$ROOT/bin/bluemap-atmons
TEST_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/bluemap-atmons-test.XXXXXXXX")
trap '[[ ${KEEP_TEST_ROOT:-0} == 1 ]] || rm -rf -- "$TEST_ROOT"' EXIT

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

assert_file() {
  [[ -f $1 ]] || fail "expected file: $1"
}

assert_no_path() {
  [[ ! -e $1 ]] || fail "expected no path: $1"
}

assert_content() {
  [[ $(<"$1") == "$2" ]] || fail "unexpected content in $1"
}

assert_json() {
  local file=$1 expression=$2
  jq -e "$expression" "$file" >/dev/null || fail "JSON assertion failed: $expression"
}

expect_fail() {
  local pattern=$1
  shift
  local output status
  set +e
  output=$("$@" 2>&1)
  status=$?
  set -e
  (( status != 0 )) || fail "command unexpectedly succeeded: $*"
  [[ $output == *"$pattern"* ]] || fail "failure did not contain '$pattern': $output"
}

artifact_json() {
  local id=$1 kind=$2 repository=$3 tag=$4 file=$5
  jq -n \
    --arg id "$id" \
    --arg kind "$kind" \
    --arg repository "$repository" \
    --arg tag "$tag" \
    --arg filename "${file##*/}" \
    --arg url "file://$file" \
    --argjson bytes "$(wc -c < "$file")" \
    --arg hash "$(sha256sum "$file" | cut -d' ' -f1)" '
    {
      id: $id,
      kind: $kind,
      repository: $repository,
      release_tag: $tag,
      artifact: {
        filename: $filename,
        url: $url,
        size_bytes: $bytes,
        sha256: $hash
      }
    }
  '
}

make_manifest() {
  local version=$1 output=$2 core=$3 alpha=$4 beta=${5:-}
  local components=$TEST_ROOT/components.json
  if [[ -n $beta ]]; then
    jq -s '.' \
      <(artifact_json bluemap bluemap jan-guenter/BlueMap v-core "$core") \
      <(artifact_json alpha addon jan-guenter/bluemap-alpha-addon v-alpha "$alpha") \
      <(artifact_json beta addon jan-guenter/bluemap-beta-addon v-beta "$beta") > "$components"
  else
    jq -s '.' \
      <(artifact_json bluemap bluemap jan-guenter/BlueMap v-core "$core") \
      <(artifact_json alpha addon jan-guenter/bluemap-alpha-addon v-alpha "$alpha") > "$components"
  fi
  jq -n \
    --arg version "$version" \
    --slurpfile components "$components" '
    {
      schema_version: 1,
      atmons: {version: $version, tag: ("atmons-" + $version)},
      components: $components[0]
    }
  ' > "$output"
}

mkdir -p "$TEST_ROOT/assets"
printf 'core-v1\n' > "$TEST_ROOT/assets/bluemap-core-v1.jar"
printf 'alpha-v1\n' > "$TEST_ROOT/assets/bluemap-alpha-v1.jar"
printf 'beta-v1\n' > "$TEST_ROOT/assets/bluemap-beta-v1.jar"
printf 'alpha-v2\n' > "$TEST_ROOT/assets/bluemap-alpha-v2.jar"

MANIFEST_120=$TEST_ROOT/manifest-1.2.0.json
MANIFEST_121=$TEST_ROOT/manifest-1.2.1.json
make_manifest 1.2.0 "$MANIFEST_120" \
  "$TEST_ROOT/assets/bluemap-core-v1.jar" \
  "$TEST_ROOT/assets/bluemap-alpha-v1.jar" \
  "$TEST_ROOT/assets/bluemap-beta-v1.jar"
make_manifest 1.2.1 "$MANIFEST_121" \
  "$TEST_ROOT/assets/bluemap-core-v1.jar" \
  "$TEST_ROOT/assets/bluemap-alpha-v2.jar"

SERVER=$TEST_ROOT/server
mkdir -p "$SERVER"

printf '1. dry-run and stopped-server guard\n'
"$INSTALLER" install --server "$SERVER" --manifest "$MANIFEST_120" --dry-run >/dev/null
assert_no_path "$SERVER/.bluemap-atmons"
assert_no_path "$SERVER/mods/bluemap-core-v1.jar"
expect_fail 'mutation requires' "$INSTALLER" install --server "$SERVER" --manifest "$MANIFEST_120"

printf '2. complete install and layout\n'
"$INSTALLER" install --server "$SERVER" --manifest "$MANIFEST_120" --server-stopped >/dev/null
assert_content "$SERVER/mods/bluemap-core-v1.jar" 'core-v1'
assert_content "$SERVER/config/bluemap/packs/bluemap-alpha-v1.jar" 'alpha-v1'
assert_content "$SERVER/config/bluemap/packs/bluemap-beta-v1.jar" 'beta-v1'
assert_json "$SERVER/.bluemap-atmons/state.json" '.schema_version == 2 and .snapshot_status == "complete" and .atmons_versions == ["1.2.0"] and .compatibility_tags == ["atmons-1.2.0"] and (.components | length == 3)'
"$INSTALLER" status --server "$SERVER" >/dev/null
"$INSTALLER" verify --server "$SERVER" >/dev/null

printf '3. same-version no-op and unknown-file preservation\n'
printf 'leave-me\n' > "$SERVER/config/bluemap/packs/unmanaged.jar"
state_hash_before=$(sha256sum "$SERVER/.bluemap-atmons/state.json")
same_output=$("$INSTALLER" update --server "$SERVER" --manifest "$MANIFEST_120" --server-stopped)
[[ $same_output == *'nothing to do'* ]] || fail "same-version update was not reported as a no-op"
[[ $(sha256sum "$SERVER/.bluemap-atmons/state.json") == "$state_hash_before" ]] || fail 'same-version update rewrote state'
assert_content "$SERVER/config/bluemap/packs/unmanaged.jar" 'leave-me'

printf '4. core-only and add-on subset selection\n'
CORE_SERVER=$TEST_ROOT/core-server
mkdir -p "$CORE_SERVER"
"$INSTALLER" install --server "$CORE_SERVER" --manifest "$MANIFEST_120" --components bluemap --server-stopped >/dev/null
assert_file "$CORE_SERVER/mods/bluemap-core-v1.jar"
assert_no_path "$CORE_SERVER/config/bluemap/packs/bluemap-alpha-v1.jar"
assert_json "$CORE_SERVER/.bluemap-atmons/state.json" '.snapshot_status == "partial" and (.components | map(.id)) == ["bluemap"]'

ADDON_SERVER=$TEST_ROOT/addon-server
mkdir -p "$ADDON_SERVER"
"$INSTALLER" install --server "$ADDON_SERVER" --manifest "$MANIFEST_120" --components addons --addons alpha,beta --exclude-addon beta --server-stopped >/dev/null
assert_file "$ADDON_SERVER/config/bluemap/packs/bluemap-alpha-v1.jar"
assert_no_path "$ADDON_SERVER/config/bluemap/packs/bluemap-beta-v1.jar"
assert_no_path "$ADDON_SERVER/mods/bluemap-core-v1.jar"
assert_json "$ADDON_SERVER/.bluemap-atmons/state.json" '(.components | map(.id)) == ["alpha"]'

printf '5. unmanaged collision refusal\n'
COLLISION_SERVER=$TEST_ROOT/collision-server
mkdir -p "$COLLISION_SERVER/mods"
printf 'some-other-core\n' > "$COLLISION_SERVER/mods/bluemap-core-v1.jar"
expect_fail 'unmanaged file' "$INSTALLER" install --server "$COLLISION_SERVER" --manifest "$MANIFEST_120" --server-stopped
assert_content "$COLLISION_SERVER/mods/bluemap-core-v1.jar" 'some-other-core'
assert_no_path "$COLLISION_SERVER/.bluemap-atmons"

printf '6. bad download hash leaves server untouched\n'
BAD_MANIFEST=$TEST_ROOT/bad-manifest.json
jq '.components[1].artifact.sha256 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"' "$MANIFEST_120" > "$BAD_MANIFEST"
BAD_SERVER=$TEST_ROOT/bad-server
mkdir -p "$BAD_SERVER"
expect_fail 'SHA-256 mismatch' "$INSTALLER" install --server "$BAD_SERVER" --manifest "$BAD_MANIFEST" --server-stopped
assert_no_path "$BAD_SERVER/.bluemap-atmons"
assert_no_path "$BAD_SERVER/mods/bluemap-core-v1.jar"

printf '7. live PID always refuses mutation\n'
printf '%s\n' "$$" > "$TEST_ROOT/live.pid"
expect_fail 'still running' "$INSTALLER" update --server "$SERVER" --manifest "$MANIFEST_120" --pid-file "$TEST_ROOT/live.pid" --server-stopped
printf '99999999\n' > "$TEST_ROOT/dead.pid"
"$INSTALLER" update --server "$SERVER" --manifest "$MANIFEST_120" --pid-file "$TEST_ROOT/dead.pid" >/dev/null

printf '8. update replaces and removes only managed files\n'
"$INSTALLER" update --server "$SERVER" --atmons 1.2.1 --manifest "$MANIFEST_121" --server-stopped >/dev/null
assert_file "$SERVER/mods/bluemap-core-v1.jar"
assert_content "$SERVER/config/bluemap/packs/bluemap-alpha-v2.jar" 'alpha-v2'
assert_no_path "$SERVER/config/bluemap/packs/bluemap-alpha-v1.jar"
assert_no_path "$SERVER/config/bluemap/packs/bluemap-beta-v1.jar"
assert_content "$SERVER/config/bluemap/packs/unmanaged.jar" 'leave-me'
assert_json "$SERVER/.bluemap-atmons/state.json" '.snapshot_status == "complete" and .atmons_versions == ["1.2.1"] and .compatibility_tags == ["atmons-1.2.1"] and (.components | map(.id)) == ["alpha", "bluemap"]'

printf '9. exclusions remain untouched during a partial update\n'
EXCLUDE_SERVER=$TEST_ROOT/exclude-server
mkdir -p "$EXCLUDE_SERVER"
"$INSTALLER" install --server "$EXCLUDE_SERVER" --manifest "$MANIFEST_120" --server-stopped >/dev/null
"$INSTALLER" update --server "$EXCLUDE_SERVER" --atmons 1.2.1 --manifest "$MANIFEST_121" --exclude-addon beta --server-stopped >/dev/null
assert_file "$EXCLUDE_SERVER/config/bluemap/packs/bluemap-beta-v1.jar"
assert_json "$EXCLUDE_SERVER/.bluemap-atmons/state.json" '.snapshot_status == "mixed" and .atmons_versions == ["1.2.0", "1.2.1"] and (.components | map(.id)) == ["alpha", "beta", "bluemap"]'

printf '10. cross-version subset reports a mixed snapshot\n'
MIXED_SERVER=$TEST_ROOT/mixed-server
mkdir -p "$MIXED_SERVER"
"$INSTALLER" install --server "$MIXED_SERVER" --manifest "$MANIFEST_120" --server-stopped >/dev/null
"$INSTALLER" update --server "$MIXED_SERVER" --atmons 1.2.1 --manifest "$MANIFEST_121" --components addons --addons alpha --server-stopped >/dev/null
assert_json "$MIXED_SERVER/.bluemap-atmons/state.json" '.snapshot_status == "mixed" and .atmons_versions == ["1.2.0", "1.2.1"] and .compatibility_tags == ["atmons-1.2.0", "atmons-1.2.1"]'
mixed_status=$("$INSTALLER" status --server "$MIXED_SERVER")
[[ $mixed_status == *'Snapshot status: mixed'* ]] || fail 'status did not report a mixed snapshot'
[[ $mixed_status == *'All the Mons versions: 1.2.0, 1.2.1'* ]] || fail 'status did not report both managed versions'

printf '11. cross-version duplicate destination is rejected before mutation\n'
DUPLICATE_MANIFEST=$TEST_ROOT/duplicate-manifest.json
jq --slurpfile old "$MANIFEST_120" '.components[1].artifact = $old[0].components[2].artifact' "$MANIFEST_121" > "$DUPLICATE_MANIFEST"
DUPLICATE_SERVER=$TEST_ROOT/duplicate-server
mkdir -p "$DUPLICATE_SERVER"
"$INSTALLER" install --server "$DUPLICATE_SERVER" --manifest "$MANIFEST_120" --server-stopped >/dev/null
duplicate_state_before=$(sha256sum "$DUPLICATE_SERVER/.bluemap-atmons/state.json")
expect_fail 'duplicate managed destination' "$INSTALLER" update --server "$DUPLICATE_SERVER" --atmons 1.2.1 --manifest "$DUPLICATE_MANIFEST" --components addons --addons alpha --server-stopped
[[ $(sha256sum "$DUPLICATE_SERVER/.bluemap-atmons/state.json") == "$duplicate_state_before" ]] || fail 'duplicate-path refusal changed state'
assert_content "$DUPLICATE_SERVER/config/bluemap/packs/bluemap-beta-v1.jar" 'beta-v1'

printf '12. explicit recovery restores files and state\n'
RECOVER_SERVER=$TEST_ROOT/recover-server
mkdir -p "$RECOVER_SERVER"
"$INSTALLER" install --server "$RECOVER_SERVER" --manifest "$MANIFEST_120" --server-stopped >/dev/null
RECOVER_STATE=$RECOVER_SERVER/.bluemap-atmons
mkdir -p "$RECOVER_STATE/transaction/backups"
cp "$RECOVER_STATE/state.json" "$RECOVER_STATE/transaction/previous-state.json"
mv "$RECOVER_SERVER/mods/bluemap-core-v1.jar" "$RECOVER_STATE/transaction/backups/1.jar"
printf 'interrupted-write\n' > "$RECOVER_SERVER/mods/bluemap-core-v1.jar"
printf 'BACKUP\tmods/bluemap-core-v1.jar\tbackups/1.jar\nINSTALL\tmods/bluemap-core-v1.jar\t-\n' > "$RECOVER_STATE/transaction/operations.tsv"
"$INSTALLER" recover --server "$RECOVER_SERVER" --server-stopped >/dev/null
assert_content "$RECOVER_SERVER/mods/bluemap-core-v1.jar" 'core-v1'
assert_no_path "$RECOVER_STATE/transaction"
"$INSTALLER" verify --server "$RECOVER_SERVER" >/dev/null

printf '13. destination symlinks cannot escape the server tree\n'
ESCAPE_SERVER=$TEST_ROOT/escape-server
ESCAPE_TARGET=$TEST_ROOT/escape-target
mkdir -p "$ESCAPE_SERVER/config/bluemap" "$ESCAPE_TARGET"
ln -s "$ESCAPE_TARGET" "$ESCAPE_SERVER/config/bluemap/packs"
expect_fail 'outside the server directory' "$INSTALLER" install --server "$ESCAPE_SERVER" --manifest "$MANIFEST_120" --components addons --server-stopped
assert_no_path "$ESCAPE_TARGET/bluemap-alpha-v1.jar"

printf '14. schema-v1 state upgrades on the next mutation\n'
LEGACY_SERVER=$TEST_ROOT/legacy-server
mkdir -p "$LEGACY_SERVER"
"$INSTALLER" install --server "$LEGACY_SERVER" --manifest "$MANIFEST_120" --server-stopped >/dev/null
jq '{schema_version: 1, atmons_version: .atmons_versions[0], compatibility_tag: .compatibility_tags[0], components: [.components[] | del(.atmons_version, .compatibility_tag)]}' \
  "$LEGACY_SERVER/.bluemap-atmons/state.json" > "$LEGACY_SERVER/.bluemap-atmons/state.json.next"
mv "$LEGACY_SERVER/.bluemap-atmons/state.json.next" "$LEGACY_SERVER/.bluemap-atmons/state.json"
"$INSTALLER" update --server "$LEGACY_SERVER" --manifest "$MANIFEST_120" --server-stopped >/dev/null
assert_json "$LEGACY_SERVER/.bluemap-atmons/state.json" '.schema_version == 2 and .snapshot_status == "complete"'

printf 'PASS: all installer tests completed\n'
