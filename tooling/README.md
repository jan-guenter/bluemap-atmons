# Development tooling

This directory pins development-only components used to maintain the BlueMap
add-on portfolio. These components are not Minecraft mods or BlueMap packs and
must never be added to the server installer manifest.

`manifest.json` records the exact repository, release, commit, wheel URL, size,
and SHA-256 for the toolkit gitlink. Automation uses the full commit and wheel
digest. The release tag is a human-readable identity.

Toolkit `v0.2.0-alpha.1` owns the `addon-v1` convention checks, exact
candidate-artifact verification, accepted staged-JAR entry verification, and
the source-distributed Java 21 Gradle convention. Consumers load that plugin
from their own exact toolkit gitlink. Reusable consumer workflows, gallery
formats, and production Java remain outside the shared boundary.
