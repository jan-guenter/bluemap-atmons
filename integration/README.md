# ATMons combined integration testing

This directory contains the reproducible integration layer for the exact All
the Mons 1.2.0 snapshot. It keeps the published `atmons-1.2.0` manifest and
release artifacts immutable while allowing an explicitly identified BlueMap
candidate to be tested against all 51 add-ons together.

## Test layers

1. `run_child_gates.py` runs every add-on's tracked gallery checks and common
   Gradle gates sequentially. Release-source runs use the BlueMap commit pinned
   by the manifest. An explicit candidate-source run is a useful negative gate:
   the add-ons must reject an unknown BlueMap commit before compilation.
2. `build_candidate_addons.py` verifies every released add-on JAR and its exact
   pinned source. Legacy bases receive a candidate-aware
   `AdapterCompatibility` and a strict entrypoint. Explicit release overrides
   already migrated to the exact 5.23 feature backport keep their shipped
   compatibility and adapter classes; only the entrypoint is rewritten to
   require a `true` Boolean install result. Both paths emit a post-install
   activation marker, and neither staging artifact is published.
3. `galleries/compose.py` translates all 51 tracked galleries to non-overlapping
   tiles on one high, divided surface. It emits bounded load/release functions,
   a deterministic datapack ZIP, a layout file, BlueMap marker coordinates, and
   scoreboard assertions.
4. `run_runtime_suite.py` builds and verifies the composed galleries through
   RCON, one force-loaded tile at a time. It requires 51 asserted passes.
5. `harness/` catalogs the live structure registry across every loaded
   dimension, locates and generates one eligible instance of each structure,
   derives authoritative bounds with a four-block border, publishes BlueMap
   markers, and schedules the affected map regions.

The source-wide gates and the combined runtime gate answer different questions.
A clean build at the released BlueMap pin does not establish candidate runtime
compatibility; the staging overlays and full server run do. Conversely, a
staging overlay is not a releasable add-on build.

## Local preparation

Initialize all submodules and use Java 21:

```bash
git submodule update --init --recursive
java -version
```

Compose the deterministic gallery campus:

```bash
python integration/galleries/compose.py \
  --output .tmp/integration/bluemap-atmons-galleries
```

The command writes `gallery-layout.json` beside the output directory and a ZIP
at `.tmp/integration/bluemap-atmons-galleries.zip`.

Build staging-only compatibility overlays for an exact candidate:

```bash
python integration/build_candidate_addons.py \
  --bluemap-version '<exact-runtime-version>' \
  --bluemap-commit '<full-commit>' \
  --output .tmp/integration/candidate-addons
```

The output must contain 51 JARs and a `candidate-manifest.json` whose summary is
`passed` with 51 components.

An integration batch may replace selected released add-ons with exact local
candidate artifacts by passing an absolute override lock:

```bash
python integration/build_candidate_addons.py \
  --bluemap-version '<exact-runtime-version>' \
  --bluemap-commit '<full-commit>' \
  --addon-override-lock /absolute/path/to/addon-override-lock.json \
  --output .tmp/integration/candidate-addons
```

The schema-1 lock contains `atmons: "1.2.0"` and a non-empty `components`
array. Each component supplies its manifest ID, an absolute clean source
checkout plus exact commit, and an absolute candidate JAR path, filename,
version, size, and SHA-256. The builder binds those values to the candidate's
tracked release provenance before reading any source or artifact bytes.

Adapter API provenance is evaluated per overridden consumer. This permits a
bounded mixed batch in which selected candidates source-bundle the released
Adapter API `0.1.0-alpha.3` while every other native consumer remains pinned
to `0.1.0-alpha.2`. Each override must pin the matching module gitlink, source
tree, source count, exact embedded class roster, and recognized class bytes;
one component's profile never changes another component's admission rules.
The standalone Adapter API JAR remains absent from the server and nested JARs
remain forbidden.

To test explicit alternate add-on releases or sealed candidates, pass an
absolute JSON lock with `--addon-override-lock`. Each listed checkout must be
clean and at the declared HEAD. The exact commit's tracked
`provenance/release.json` must identify the same version, filename, size, and
SHA-256 as the artifact, and the JAR manifest must carry that version. The gate
accepts either an `owner-accepted-release-candidate` with
`final_release_artifacts`, or an `unpublished-migration-candidate` with
`published: false` and `candidate_artifacts`. The latter exists only so a
sealed native migration can complete integration before owner review. It is
not release approval. Each artifact path must name that exact readable
production JAR:

```json
{
  "schemaVersion": 1,
  "atmons": "1.2.0",
  "components": [
    {
      "id": "laserio",
      "source": {
        "checkout": "/absolute/path/to/bluemap-laserio-addon",
        "commit": "0123456789abcdef0123456789abcdef01234567"
      },
      "artifact": {
        "path": "/absolute/path/to/bluemap-laserio-addon-0.2.0-alpha.1.jar",
        "filename": "bluemap-laserio-addon-0.2.0-alpha.1.jar",
        "sizeBytes": 12345,
        "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "version": "0.2.0-alpha.1"
      }
    }
  ]
}
```

The builder copies that local base JAR and retains the compatibility manifest's
canonical output filename. Ordinary overrides receive the two-class overlay.
A native 5.23 override is admitted only when its source has no local
`AdapterCompatibility`, pins Adapter API `v0.1.0-alpha.2` at commit
`e81f08bc4bfbf02d810ec8949a019130e2e61634`, ships the exact four shared API
classes without a nested module JAR or any `bluemap522` package classes, and
uses one `BlueMap523Adapter` behind
`BlueMapRuntimeCompatibility.matchesCurrent()` or its exact explicit-identity
wrapper. Migration provenance may use one self-contained Adapter API migration
section. The paired `adapter_api_source` form is accepted only with an exact
`render_core_523_migration` companion. That companion must pin the audited
render-core release and gitlink, the exact BlueMap runtime and API commits, the
`bluemap523` source package, and source-only use of both shared modules. A
missing or mixed provenance form is rejected. That path overlays only the
entrypoint and is accepted solely for BlueMap commit
`7e07f4e74ec1e92a6ead9aa1e66054af3e133aac`. The output manifest records the
released baseline, local base, native-contract and release-provenance
identities, plus the lock hash. It never records local paths, including on a
failed build. A native 5.23 release already pinned by the tracked manifest is
admitted through the same exact native contract and uses a released-base
entrypoint overlay; legacy manifest releases retain the two-class overlay.

For the next full-stack 5.23 run, the reviewed public release identities are
tracked in
`candidate-releases/atmons-1.2.0-bluemap-5.23.json`. Materialize those releases
into the existing path-bound lock contract instead of reusing old local build
candidates:

```bash
python integration/materialize_candidate_release_overrides.py \
  --work-root /tmp/bluemap-atmons-1.2.0-5.23-releases \
  --output /tmp/bluemap-atmons-1.2.0-5.23-overrides.json
```

The materializer fetches each exact annotated tag, verifies its tag object and
peeled commit, downloads and hashes the published production JAR, then applies
the same release-provenance and native-adapter checks as the candidate builder.
The resulting checkout, JARs, and absolute-path lock are disposable and remain
untracked. The profile does not alter the immutable `atmons-1.2.0` manifest or
its BlueMap 5.22 compatibility snapshot.

## Individual add-on gates

Inspect the complete deterministic command plan without running it:

```bash
python integration/run_child_gates.py \
  --plan \
  --bluemap-source /absolute/path/to/manifest-pinned-bluemap \
  --expected-bluemap-commit '<manifest-commit>'
```

Run the plan and retain a JSON result:

```bash
python integration/run_child_gates.py \
  --run \
  --bluemap-source /absolute/path/to/manifest-pinned-bluemap \
  --expected-bluemap-commit '<manifest-commit>' \
  --gallery-artifact-dir rechiseled-create=/absolute/path/to/exact/runtime-jars \
  --output .tmp/integration/child-gates.json
```

The Rechiseled Create artifact directory is required by that repository's
tracked generator and must contain the exact pack-pinned Rechiseled Create,
Rechiseled, Fusion, and Create JARs.

## Runtime gallery gate

Install the composed ZIP in the standard world's `datapacks` directory and
copy `gallery-layout.json` to the harness configuration directory. The runner
supports direct RCON or a JSON command prefix such as a credential-hiding
cluster-side RCON wrapper:

First derive the reviewed base ledger from the exact 1.2.0 server archive.
The runner pins the resulting file to SHA-256
`aba2db94fbcd6cf756d6ab2f03e7adc35422d4a2c1eb82e47d998ed740e4d70c`;
a caller-authored 375-row substitute is rejected.

```bash
python integration/generate_server_mod_inventory.py \
  --archive /absolute/path/to/ServerFiles-1.2.0.zip \
  --output .tmp/integration/atmons-1.2.0-server-mods.tsv
```

```bash
python integration/run_runtime_suite.py \
  --layout .tmp/integration/gallery-layout.json \
  --composition-manifest .tmp/integration/gallery-composition-manifest.json \
  --output .tmp/integration/runtime-suite.json \
  --exec-prefix-json '["kubectl","exec","...","--","rcon-cli"]' \
  --bluemap-commit '<full-candidate-commit>' \
  --candidate-manifest .tmp/integration/candidate-addons/candidate-manifest.json \
  --addon-override-lock /absolute/path/to/addon-override-lock.json \
  --bluemap-jar /absolute/path/to/candidate-bluemap.jar \
  --harness-jar integration/harness/build/libs/bluemap-atmons-integration-harness-0.1.0-SNAPSHOT.jar \
  --artifact-exec-prefix-json '["kubectl","exec","...","--"]' \
  --runtime-mods-directory /data/mods \
  --runtime-packs-directory /data/config/bluemap/packs \
  --trusted-base-inventory .tmp/integration/atmons-1.2.0-server-mods.tsv \
  --runtime-log /data/logs/latest.log \
  --runtime-identity-file /data/config/bluemap-atmons-integration/runtime-identity.json \
  --runtime-attestation /data/config/bluemap-atmons-integration/runtime-attestation.json \
  --datapack-archive .tmp/integration/bluemap-atmons-galleries.zip \
  --installed-datapack /data/world/datapacks/bluemap-atmons-galleries.zip \
  --expected-runtime-jar-count 377 \
  --restart-exec-json '["/absolute/path/to/controlled-restart-hook"]'
```

Omit `--addon-override-lock` for the ordinary release-only 51-add-on run. If
the candidate manifest contains any local add-on base, the runtime suite
requires the same lock, validates it again, and passes it to the independent
51-overlay reproduction.

The suite completes its initial live preflight, then requires one controlled
container restart before it prepares or builds any gallery. A restart hook must
replace the container; the runner refuses readiness until hostname/PID-1 start
identity changes. It repeats the full artifact, runtime, activation, datapack,
and composition attestation against the restarted server before construction.
The `bluemap version` response is retained as a transport diagnostic only:
BlueMap may emit that command's text asynchronously, so direct RCON can return
an empty body. Exact candidate identity is instead gated by the independently
hashed runtime JAR, runtime configuration attestation, live harness identity,
activation markers, and the canonical startup log in both boots.

The runner then applies the 51 gallery cycles sequentially. Each cycle prepares
and builds one tile, polls its explicit game-tick completion score, immediately
runs its asserted verification while the tile is still force-loaded, and
releases that tile's force-load. Source builds and scheduled settle checks may
mirror transient failures into the cumulative `bma_test` score. After the
completion barrier, the runner records that score as a diagnostic, resets it to
zero, runs the final verify function, and treats only the fresh score as the
authoritative assertion. The reset never occurs after verification. It flushes
the world only after all 51 cycles pass. A wall-clock completion timeout is only a fail-safe.
`--settle-seconds` is an optional extra margin after the completion barrier and
defaults to zero. The harness independently hashes all 377 JARs on disk. It
also requires NeoForge's 374 ordinary
`ModList` roots to equal that inventory after excluding only the exact
hash-pinned CrashAssistant wrapper, KotlinForForge library, and
ScalableCatsForce library roots. Candidate packs are attested separately under
BlueMap's packs directory.
A full report passes only with 51 performed builds and 51 immediate asserted
verifications. Interrupted runs start the lifecycle again; there is no
prebuilt-gallery resume path because restart-time normalization can change the
source mods' gallery assertions.

Nine reviewed child fixtures deliberately increment invocation counters and
require each to equal one: AE2 has four, while Factory Blocks, LaserIO, RFTools
Builder, EnderIO, Modular Routers, SecurityCraft, Functional Storage, and
Logistics Networks have one each. Their aggregate prepare wrappers verify those
exact increment commands against each pinned child commit and reset only those
twelve counters before rebuilding, so an interrupted aggregate run can restart
against the same disposable world without weakening any block or NBT assertion.
The remaining persistent child counters reset themselves inside every build.

The aggregate copy also has exact, commit-guarded settled-world corrections
for three child fixtures that intentionally force synthetic properties. It
checks PneumaticCraft's stock heat-pipe control by block identity, omits only
More Red's volatile power value on its stock meter control, and builds legal
XNet neighbor and antenna topologies before checking its cable, connector,
facade, and router states. The composer requires every correction to match its
single expected source line. It never changes a child checkout or accepts an
arbitrary nonzero failure score.

## Structure reference lifecycle

Build the dedicated-server-only harness as documented in
[`harness/README.md`](harness/README.md), install its JAR in the disposable
server, then use this order:

```text
/bluemapatmons structures catalog
/bluemapatmons structures status
/bluemapatmons structures generate
/bluemapatmons structures status
```

After the catalog is complete, create one BlueMap map configuration for every
catalog dimension using its deterministic safe map ID. Once BlueMap exposes
those maps, use the external completion gate to publish markers, enqueue the
exact regions, wait for an idle renderer, and require fresh high-resolution
tiles plus region-state evidence for every requested region:

The tracked generator chooses each map's lower-median located structure as its
start position and disables `render-edges`. Keep that setting for the gallery
map too. BlueMap's artificial edge caps obscure geometry when a map contains
many small four-block-bordered masks.

```bash
python integration/run_structure_suite.py \
  --exec-prefix-json '["kubectl","exec","...","--","rcon-cli"]' \
  --artifact-exec-prefix-json '["kubectl","exec","...","--"]' \
  --output .tmp/integration/structure-suite.json
```

Like the runtime suite, the structure runner also accepts direct
`--rcon HOST:PORT --password-env NAME`; this is preferred when the cluster
command proxy is not stable enough for non-replayable render scheduling.
The artifact command prefix must preserve file bytes exactly. Do not wrap
remote `cat` output in command substitution or append a newline: the runner
binds the catalog, masks, generation receipt, work state, and map manifest by
their exact SHA-256 values before scheduling a render.

After the structure suite has passed and the renderer is idle, publish the
gallery markers, enqueue the four exact campus regions once, and poll the
verification command until it reports 589 fresh tiles:

```text
/bluemapatmons galleries publish
/bluemapatmons galleries render
/bluemapatmons galleries verify-render
```

Only `BlueMap gallery renderer is not running and idle` is a pending
verification response. Do not enqueue the gallery regions again after a
successful `galleries render`; continue polling `galleries verify-render`
until it returns the current layout's evidence SHA-256.

Catalog and generation operations are resumable. Every structure with an
eligible placement must be located; only registry entries with no eligible
placement in any loaded dimension may be recorded as `registry-only`. The
harness owns and removes only the force-loads it created. Runtime catalogs,
layouts, map data, worlds, credentials, and generated test results stay
outside Git.

After the automated storage and tile gates pass, open the exact public gallery
link and representative links for every structure map. Confirm that each view
loads without an obviously blank, black, missing, or grossly broken result.
This lightweight browser check does not replace owner comparison against the
game client. Record reviewed summaries and evidence hashes under
`reports/integration/<version>-candidate.md`; keep raw reports outside Git.

## Focused tooling checks

```bash
python integration/test_build_candidate_addons.py
python integration/galleries/test_compose.py
python integration/test_child_gates.py
python integration/test_runtime_suite.py
python integration/test_structure_suite.py
python tests/test-duplicate-scanner.py
python tools/scan_duplicates.py --version 1.2.0 --check
```

The [disposable cluster profile](cluster-profile.md) records the staging
controls and filesystem contract without player identity or credentials. Do
not commit Kubernetes Secrets, RCON values, whitelist/ops files, worlds, map
output, or third-party JARs.
