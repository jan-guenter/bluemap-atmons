# BlueMap ATMons

BlueMap ATMons is the versioned compatibility index and installer for the
[BlueMap](https://github.com/jan-guenter/BlueMap) Java 21 backport and its
All the Mons rendering add-ons.

Every `atmons-<version>` tag is an immutable, tested snapshot. Its commit pins
all source repositories as Git submodules, while one normalized manifest pins
the exact release JARs and their SHA-256 digests. The installer reads that
single manifest; it never guesses from child repositories' latest releases.

## Supported snapshots

| All the Mons | Minecraft | NeoForge | Java | BlueMap add-ons | Tag |
| --- | --- | --- | --- | ---: | --- |
| 1.2.0 | 1.21.1 | 21.1.248 | 21 | 51 | `atmons-1.2.0` |

Applied Mekanistics' zero-block rendering extension is bundled in the AE2
add-on `0.1.0-alpha.3`; it intentionally has no separate repository, gitlink,
or JAR in the snapshot.

## Install or update a server

Stop the Minecraft server first. Download the installer from the compatibility
tag you intend to use, inspect it, and run a plan before making changes:

```bash
curl -fsSLo /tmp/bluemap-atmons \
  https://raw.githubusercontent.com/jan-guenter/bluemap-atmons/atmons-1.2.0/bin/bluemap-atmons
chmod +x /tmp/bluemap-atmons

/tmp/bluemap-atmons plan \
  --server /srv/minecraft \
  --atmons 1.2.0

/tmp/bluemap-atmons install \
  --server /srv/minecraft \
  --atmons 1.2.0 \
  --server-stopped
```

`update` uses the same options and replaces only files previously managed by
BlueMap ATMons. `verify` checks installed files against recorded state, and
`status` summarizes it. Run `recover` if an interrupted transaction is
reported.

The default selection installs everything. Common narrower selections are:

```bash
# BlueMap only
/tmp/bluemap-atmons install --server /srv/minecraft --atmons 1.2.0 \
  --components bluemap --server-stopped

# Add-ons only
/tmp/bluemap-atmons install --server /srv/minecraft --atmons 1.2.0 \
  --components addons --server-stopped

# Selected add-ons (comma-separated manifest IDs)
/tmp/bluemap-atmons install --server /srv/minecraft --atmons 1.2.0 \
  --components addons --addons ae2,create,mekanism --server-stopped
```

BlueMap is installed under `<server>/mods/`. Add-ons are installed under
`<server>/config/bluemap/packs/`. Existing files not recorded in
`<server>/.bluemap-atmons/state.json` are left alone; a conflicting unmanaged
destination makes the installer stop instead of overwriting it.

The installer needs Bash, `curl`, `jq`, `sha256sum`, `flock`, and `realpath`.
Use `--manifest <path-or-url>` for a reviewed mirror or an offline manifest.

## Inspect the pinned source

```bash
git clone --branch atmons-1.2.0 --recurse-submodules \
  https://github.com/jan-guenter/bluemap-atmons.git
```

## Combined integration testing

The [`integration/`](integration/README.md) layer composes every pinned
add-on gallery into one divided test campus, runs all 51 gallery assertions on
one exact ATMons server, catalogs live world structures, and drives bounded
BlueMap renders. Candidate BlueMap branches use staging-only compatibility
overlays; published compatibility manifests and child releases remain
immutable.

The dedicated-server integration harness includes a hash-pinned Gradle wrapper
JAR so `./gradlew` works from a fresh checkout. The repository validator rejects
that file if its bytes change and rejects every other tracked JAR.

The current feature-branch evidence is collected in the
[ATMons 1.2.0 candidate integration report](reports/integration/atmons-1.2.0-candidate.md).
It is a test record, not a replacement for the immutable compatibility tag.

The current source-wide consolidation evidence consists of the generated
[ATMons 1.2.0 clone inventory](reports/deduplication/atmons-1.2.0.md) and its
[semantic extraction review](reports/deduplication/atmons-1.2.0-review.md).
The scanner covers Java plus structured Python, Gradle, GitHub Actions, and
shell units without reading mutable child worktrees. The review separates
safe development-tooling reuse from source modules that still require shared
fixtures and migration gates.

The common child-repository contract is documented in
[add-on repository conventions](docs/ADDON-REPOSITORY-CONVENTIONS.md). Its
versioned files, checker, and migrator live in the exact pinned development
toolkit. The initial rollout deliberately changes no Java source, add-on
version, compatibility manifest, or published release tag.
The observed baseline, rollout boundary, validation, and extraction order are
recorded in the [ATMons 1.2.0 consolidation report](reports/consolidation/atmons-1.2.0.md).

The development-only [BlueMap Add-on Toolkit](toolkit/README.md) is pinned as
a separate gitlink and release artifact by [tooling/manifest.json](tooling/manifest.json).
Its first release centralizes the validated repository contract and the two
byte-exact artifact-verification tools. Toolkit `v0.2.0-alpha.1` added the
source-distributed Java 21 Gradle convention used by artifact-parity pilots;
`v0.3.0-alpha.1` makes the canonical repository checker aware of that exact
applied convention.
The [v0.3 contract consolidation](reports/consolidation/toolkit-v0.3-contract-consolidation.md)
also removes the meta repository's duplicate checker, migrator, tests, and
template mirror.
The toolkit is not an installed component and does not appear in an ATMons
server manifest.
The first [shared-verifier rollout](reports/consolidation/toolkit-verifier-rollout.md)
removed both exact script cohorts from all 24 proven consumers.
The [Gradle convention pilot](reports/consolidation/toolkit-gradle-convention-pilot.md)
records the four reviewed consumers and their byte-for-byte artifact parity.
The [second convention cohort](reports/consolidation/toolkit-gradle-convention-cohort-2.md)
records four additional reviewed consumers under the same parity gate.
The [third convention cohort](reports/consolidation/toolkit-gradle-convention-cohort-3.md)
records Trophy Manager, Laser Bridges, More Red, and Lootr under the same
artifact and gallery parity gate.
The [fourth convention cohort](reports/consolidation/toolkit-gradle-convention-cohort-4.md)
records XNet, LaserIO, Little Big Redstone, and Nature's Aura under the same
gate.

The repositories remain governed by their own licenses. This meta-repository's
installer, validation code, and documentation are MIT-licensed.

Compatibility tags are annotated and signed by fingerprint
`693A 2856 0FFD D859 A77B 513B B0DC E42D 90C8 150C`; the release workflow
rejects any other or unsigned tag.

Maintenance and release details are in [docs/MAINTENANCE.md](docs/MAINTENANCE.md).
