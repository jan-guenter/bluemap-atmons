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

The repositories remain governed by their own licenses. This meta-repository's
installer, validation code, and documentation are MIT-licensed.

Compatibility tags are annotated and signed by fingerprint
`693A 2856 0FFD D859 A77B 513B B0DC E42D 90C8 150C`; the release workflow
rejects any other or unsigned tag.

Maintenance and release details are in [docs/MAINTENANCE.md](docs/MAINTENANCE.md).
