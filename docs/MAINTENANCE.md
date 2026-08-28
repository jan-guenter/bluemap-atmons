# Compatibility snapshot maintenance

## Invariants

A compatibility snapshot consists of one commit and one signed annotated tag:

```text
atmons-<pack-version>
```

The same commit must contain:

- one gitlink for BlueMap at `bluemap/`;
- one gitlink per add-on at `addons/<id>/`;
- `versions/<pack-version>/manifest.json`, with the same commits and exact
  production release assets; and
- a combined-integration record in `docs/integration/<pack-version>.md`.

Compatibility tags are permanent. Installer-only changes can be released with
an independent semantic version and must not move an existing compatibility
tag.

## New pack-version procedure

1. Establish the exact All the Mons pack commit/export, Minecraft version,
   NeoForge version, and Java requirement.
2. Audit client-side rendering mods and the complete previously supported
   component set. Do not assume compatibility from a prior pack.
3. Release any required BlueMap or add-on changes in their child repositories.
4. Create the new normalized manifest. Use direct immutable GitHub release
   URLs and record exact filenames, sizes, and SHA-256 values.
5. Make `.gitmodules`, the Git index's gitlinks, and the manifest agree.
6. Run:

   ```bash
   python tools/validate.py
   bash tests/test-installer.sh
   python tools/validate.py --version <pack-version> --remote
   actionlint .github/workflows/*.yml
   ```

7. Install the manifest's exact artifacts together on a disposable test
   server. Verify server startup, BlueMap startup, pack loading, a complete
   render, and representative visuals. Record only observed results.
8. Commit the compatibility snapshot, inspect its staged paths, then create a
   signed annotated `atmons-<version>` tag. The release workflow verifies the
   signing key in `.github/release-signing-key.asc`; its fingerprint is
   `693A 2856 0FFD D859 A77B 513B B0DC E42D 90C8 150C`.
9. Push the commit and tag. Confirm the release manifest and checksum assets
   were generated from the tag and are downloadable without authentication.

## Manifest rules

Components are sorted by ID. Each has a stable ID, kind, public repository,
submodule path, exact 40-character commit, annotated release tag, dependencies,
and one production artifact. BlueMap is the only `bluemap` component and all
add-ons require it.

Do not include source archives, POMs, galleries, exporters, or development
JARs. Do not read child `latest` endpoints during installation. If a release
publishes several JARs, select the reviewed production artifact explicitly.

## Installer safety boundary

The server must be stopped for mutation. All downloads are verified before any
server file is changed. The installer owns only paths listed in its state file;
unmanaged files are neither removed nor overwritten. Keep these properties
when extending the CLI.
