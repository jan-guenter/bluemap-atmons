# Development tooling

This directory pins development-only components used to maintain the BlueMap
add-on portfolio. These components are not Minecraft mods or BlueMap packs and
must never be added to the server installer manifest.

`manifest.json` records the exact repository, release, commit, wheel URL, size,
and SHA-256 for the toolkit gitlink. Automation uses the full commit and wheel
digest. The release tag is a human-readable identity.

Toolkit `v0.3.0-alpha.1` owns the `addon-v1` convention checks, exact
candidate-artifact verification, accepted staged-JAR entry verification, and
the source-distributed Java 21 Gradle convention introduced in v0.2. The v0.3
checker understands that exact applied plugin while continuing to require the
three consumer-owned Gradle plugins. Consumers load the convention from their
own exact toolkit gitlink. Reusable consumer workflows, gallery formats, and
production Java remain outside the shared boundary.
