# Agent guide for BlueMap ATMons

This public meta repository is the compatibility and distribution index for
BlueMap on All the Mons. It does not contain production or third-party mod
binaries. Its only tracked JAR is the integration harness's Gradle wrapper,
whose exact path and SHA-256 are enforced by `tools/validate.py`. Read this
file and `README.md` before changing the repository.

## Repository contract

- Each immutable `atmons-<version>` tag identifies one reviewed All the Mons
  compatibility snapshot.
- The tag's commit pins `bluemap/` and every `addons/*` Git submodule to exact
  commits and contains the matching normalized manifest at
  `versions/<version>/manifest.json`.
- A manifest records exact repository, release tag, commit, download URL,
  filename, byte size, and SHA-256 for every production JAR.
- Never resolve a child repository's `latest` release. Compatibility is
  selected only by the meta-repository tag and its manifest.
- BlueMap installs to `<server>/mods/`; add-ons install to
  `<server>/config/bluemap/packs/`.
- Installer state is limited to `<server>/.bluemap-atmons/`. Never remove or
  replace an untracked server file.
- Do not move or recreate published compatibility tags.

## Validation

Run from the repository root:

```bash
python tools/validate.py
bash -n bin/bluemap-atmons install.sh tests/test-installer.sh
bash tests/test-installer.sh
python integration/test_build_candidate_addons.py
python integration/galleries/test_compose.py
python integration/test_child_gates.py
python integration/test_runtime_suite.py
python integration/test_structure_suite.py
python tests/test-duplicate-scanner.py
python tools/scan_duplicates.py --version 1.2.0 --check
```

Build the dedicated-server integration harness separately with Java 21:

```bash
cd integration/harness
./gradlew --no-daemon clean check build
```

After changing a workflow, also run:

```bash
actionlint .github/workflows/*.yml
```

Use `python tools/validate.py --version <version> --remote` before publishing a
compatibility tag.
That gate verifies remote tag targets and every release asset's size and
SHA-256. A new compatibility tag additionally requires an observed combined
runtime/rendering test with the exact manifest artifacts.

## Adding an All the Mons version

1. Establish the exact pack, Minecraft, loader, and Java baseline from
   primary pack evidence.
2. Copy the preceding manifest, then update every component from reviewed
   release evidence. Add, remove, or replace submodules to match it.
3. Run local validation and the remote artifact audit.
4. Test the exact full set together on a disposable server and BlueMap render.
5. Commit the manifest and all gitlink changes together.
6. Create a signed annotated `atmons-<version>` tag with the release key whose
   fingerprint is `693A 2856 0FFD D859 A77B 513B B0DC E42D 90C8 150C`, and
   publish its generated manifest/checksum release assets.

Do not claim compatibility from successful compilation alone. Preserve
unrelated changes and inspect staged paths before committing.

## Integration evidence boundary

- `integration/` contains reusable orchestration and the disposable
  server-only harness. It must not change an immutable compatibility manifest
  merely to test a candidate BlueMap branch.
- Candidate add-on overlays are test artifacts, not releases. Never commit or
  publish their JARs.
- The self-contained integration harness tracks only
  `integration/harness/gradle/wrapper/gradle-wrapper.jar`, SHA-256
  `55243ef57851f12b070ad14f7f5bb8302daceeebc5bce5ece5fa6edb23e1145c`.
  No other JAR may be tracked in the meta repository.
- Runtime worlds, maps, credentials, player identities, Kubernetes Secrets,
  logs, structure catalogs, and raw test results remain outside Git.
- Tracked integration reports may retain reviewed result summaries, public
  inspection links, and SHA-256 identities, but not the raw evidence files or
  session-local access details from which those summaries were derived.
- `reports/deduplication/` is extraction evidence, not proof that similarly
  shaped rendering code is behaviorally interchangeable.
