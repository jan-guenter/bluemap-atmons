# Development tooling

This directory pins development-only components used to maintain the BlueMap
add-on portfolio. These components are not Minecraft mods or BlueMap packs and
must never be added to the server installer manifest.

`manifest.json` records the exact repository, release, commit, wheel URL, size,
and SHA-256 for the toolkit gitlink. Automation uses the full commit and wheel
digest. The release tag is a human-readable identity.

The initial toolkit release owns the `addon-v1` convention checks, exact
candidate-artifact verification, and accepted staged-JAR entry verification.
Gradle plugins, reusable consumer workflows, gallery formats, and production
Java remain outside this first boundary until artifact-parity pilots pass.
