# BlueMap ATMons integration harness

This is a disposable, dedicated-server-only NeoForge `21.1.248` test harness
for the exact All the Mons `1.2.0` baseline. It catalogs runtime worldgen
structures, generates their bounded chunks, publishes BlueMap structure and
gallery markers, and schedules region renders without registering any game
content or client surface.

Initialize the BlueMap API submodule pinned by the selected backport, then
build and test with Java 21:

```bash
git -C ../../bluemap submodule update --init api
./gradlew --no-daemon clean check build
```

The tracked Gradle wrapper JAR is 48,966 bytes with SHA-256
`55243ef57851f12b070ad14f7f5bb8302daceeebc5bce5ece5fa6edb23e1145c`.
Its Gradle 9.4.0 distribution is pinned by
`distributionSha256Sum=60ea723356d81263e8002fec0fcf9e2b0eee0c0850c7a3d7ab0a63f2ccc601f3`.

The build uses BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`, which is the Java 21 rebuild of
API `2.8.0` pinned by the selected BlueMap backport. Set
`-PblueMapApiSourcePath=/absolute/path/to/BlueMapAPI` only when building from a
different checkout layout. The exact IE `12.4.2-194` CurseForge file is
SHA-256 checked; `-PimmersiveEngineeringJar=/absolute/path/to/the.jar` can use
an already acquired copy.

The first start copies the tracked default configuration to
`config/bluemap-atmons-integration/integration-harness.json`. Runtime output
and resumable state remain beside that file and do not belong in Git.

Operator commands are:

```text
/bluemapatmons structures catalog
/bluemapatmons structures generate
/bluemapatmons structures publish
/bluemapatmons structures render
/bluemapatmons structures verify-render
/bluemapatmons structures status
/bluemapatmons structures clean-forceloads
/bluemapatmons galleries publish
/bluemapatmons galleries render
/bluemapatmons galleries verify-render
/bluemapatmons immersive-engineering form
/bluemapatmons immersive-engineering verify
```

`catalog` and `generate` are resumable. Generation owns only force-loads it
created, flushes chunks in bounded batches, and removes those force-loads
after each successful flush. Structure bounds come from generated
`StructureStart#getBoundingBox()` values and receive the configured four-block
border.

The catalog inspects every level returned by `MinecraftServer#getAllLevels()`.
Each catalog dimension records a collision-resistant BlueMap map ID and its
config filename. The contract is:

```text
map id = atmons_<dimension slug, at most 64 characters>_<first 12 hex
         characters of SHA-256 over the exact dimension resource location>
config = maps/<map id>.conf
```

The slug lowercases the dimension and replaces each non-alphanumeric run with
an underscore. The hash keeps IDs distinct when two dimensions produce the
same slug. BlueMap derives its map ID from the config filename, and every
generated filename contains only lowercase ASCII, digits, and underscores.

The exact ATMons 1.2.0 plan applies three verified placement overrides. It
reads the Better Dungeons `Enable Small Nether Dungeons` Boolean and the Better
Mineshafts `Disable Vanilla Mineshafts` Boolean from their exact files under
`/data/config`. It also requires the loaded Better Strongholds
`1.21.1-NeoForge-5.1.3` JAR at its exact path, size, and SHA-256. Active rules
catalog `betterdungeons:small_nether_dungeon`, both vanilla mineshafts, and the
vanilla stronghold as `registry-only`. Missing, renamed, linked, malformed, or
non-Boolean config files fail plan construction. A wrong Better Strongholds
version or JAR also fails it. The catalog records both config files, the loaded
mod artifact, every disabled structure, and its exact reason. All of that
evidence enters the plan fingerprint.

Standard placements first use a 100-ring locate radius, then a 2,048-ring
fallback. The 4,096-ring configuration ceiling still applies. Recorded
structure bounds clamp only their vertical range to the dimension's inclusive
build height before the four-block border is added. Their X and Z bounds stay
unchanged.

After `structures catalog` reports `complete`, generate the required BlueMap
configs with the real paths inside the server container:

```bash
python3 tools/generate_bluemap_map_configs.py \
  --catalog /data/config/bluemap-atmons-integration/structure-catalog.json \
  --render-masks /data/config/bluemap-atmons-integration/structure-render-masks.json \
  --bluemap-config-root /data/config/bluemap \
  --world /data/world
```

The script writes one `maps/*.conf` file for every dimension containing a
located selection. Each file uses that dimension's four-block-bordered render
masks. It also writes `atmons-structure-maps.json`, which gives cluster code an
exact dimension, map ID, config path, and mask-count ledger. The orchestrator
must supply the actual absolute world root and BlueMap config root. Fully
restart the server after writing configs; a BlueMap reload is not sufficient
because the harness requires every generated config and its ledger to predate
the current harness process. Then run `structures publish` and `structures
render`. Both commands fail if any required dimension map is missing. The
render command also requires an idle renderer and requires BlueMap to accept
one exact region set per map; it reports only that those tasks were queued.
External orchestration must poll the synchronous `structures verify-render`
receipt until the renderer is idle. It must not depend on BlueMap CLI status
text, which may be delivered asynchronously to RCON. The verification command
binds the schedule to the current boot and exact catalog/config ledger, and
requires every render-mask tile to have a fresh `rendered` or `rendered-edge`
state plus a fresh nonempty high-resolution storage item whose PRBM
representation can be fully read and decompressed. Every exact region must
also carry a completion timestamp from this strictly newer render epoch. Only
a successful verification may describe the structure maps as viewable.

`structure-catalog.json` is validated by the harness before use; its tracked
machine contract is bundled as
`bluemap-atmons/structure-catalog.schema.json`. Runtime catalogs, work state,
render masks, gallery imports, coordinates, and world data stay in the server
configuration directory and are never packaged back into this repository.

`gallery-layout.json` accepts the aggregate composer format with `galleries`,
or small operator-authored `areas` and `points`. Composer galleries publish an
extruded area and a named POI to the layout's exact `mapId`. The tracked schema
accepts and validates all six composer function fields, including `load` and
`release`. Operator entries use their dimension's safe map ID. The harness
replaces its marker sets by stable IDs, so publishing is idempotent.

`galleries render` is available only for the runtime-attested composer layout
in `minecraft:overworld` and its exact `atmons_integration` map. The command
deletes any prior gallery-render receipt, requires the map to be loaded and
unfrozen, requires running render threads and an idle queue, captures the prior
region timestamps, and queues one forced update for the Minecraft regions
touched by the layout's top-level campus bounds. A successful response is:

```text
Queued exact BlueMap gallery render for atmons_integration covering <regions> regions; completion and storage output remain pending
```

The response proves only that BlueMap accepted the task. External orchestration
must poll the synchronous `galleries verify-render` command until it succeeds;
BlueMap CLI text is asynchronous and is not completion evidence. While work is
pending, the verification command fails with:

```text
BlueMap gallery renderer is not running and idle
```

The per-boot `gallery-render-schedule.json` receipt binds the layout bytes,
composition ID, runtime attestation, boot ID, map, exact regions, BlueMap tile
set, and the strictly newer render epoch. Verification requires an idle
renderer, a matching receipt, and a fresh `rendered` or `rendered-edge` state
for every BlueMap tile intersecting at least one composer's `tileBounds`.
Campus gaps outside all 51 gallery tile bounds are not evidence targets. Each
required tile must also have fresh nonempty high-resolution storage whose PRBM
representation can be fully read and decompressed. Every scheduled region must
have a completion timestamp from the same render epoch. Success returns:

```text
Verified <tiles> freshly rendered gallery tiles for atmons_integration across <regions> regions; evidenceSha256=<sha256>
```

The two Immersive Engineering commands are staging-only bridges for the
repository gallery's schema-2 request in
`immersiveengineering_gallery:formation`. Built-in functions
`immersiveengineering_gallery_helper:form` and `:verify` invoke them. They use
IE's registered `IMultiblock` API, and verification increments
`#immersive_engineering` in `bma_test` on a mismatch when that objective is
present.
