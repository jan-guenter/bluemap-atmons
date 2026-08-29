# Toolkit v0.3 contract consolidation

Status: complete
Date: 2026-08-29
Scope: development tooling only

## Release identity

| Field | Exact value |
| --- | --- |
| Release | [`v0.3.0-alpha.1`](https://github.com/jan-guenter/bluemap-addon-toolkit/releases/tag/v0.3.0-alpha.1) |
| Pull request | [`bluemap-addon-toolkit#2`](https://github.com/jan-guenter/bluemap-addon-toolkit/pull/2) |
| Merge commit | `6cd34a8368cc4ee8628fbe830a90ec5b14960629` |
| Signed tag object | `cf101916646fafab453013a9b34a5924070b08e8` |
| Wheel | `bluemap_addon_toolkit-0.3.0a1-py3-none-any.whl` |
| Wheel size | 20,585 bytes |
| Wheel SHA-256 | `82f1ec53603646849a7c2d4b58f3fb7000413fe83043a302bee88cc88daeb8f7` |

The signed annotated tag points to the reviewed two-parent merge. Release
workflow [`33273609685`](https://github.com/jan-guenter/bluemap-addon-toolkit/actions/runs/33273609685)
passed the exact Gradle 9.4.0 and 9.6.1 gates, reproducible archive builds,
clean-wheel installation, checksum verification, release publication, and
SLSA attestation. The downloaded wheel, source archive, and `SHA256SUMS`
matched the published asset digests; the wheel attestation verified against
the toolkit repository.

## Corrected contract

Toolkit v0.2 configured eight common build settings through the shared Gradle
plugin, but its repository checker still required those settings to appear
inline in each consumer's `build.gradle`. Migrated repositories therefore
received eight advisory false positives even though the effective Gradle
configuration and artifact-parity gates passed.

The v0.3 checker treats only the exact applied
`io.github.janguenter.bluemap-addon.java-conventions` declaration in the
leading `plugins` block as the provider of those eight settings. It still
requires `java-library`, `checkstyle`, and `maven-publish` in the consumer.
Comments, multiline strings, `apply false`, suffixes, misspellings, and
declarations outside the leading block do not qualify.

The corrected checker passed fresh current-main clones of all 51 add-ons and
the migrated Lootr consumer. Its migration check also reported Lootr current.
The complete 25-test Python suite and both exact Gradle versions passed before
the pull request, on the pull request, on `main`, and from the release tag.

## Meta-repository deduplication

The meta repository now uses the exact toolkit gitlink as the sole source for
the `addon-v1` checker, migrator, and managed templates. This removes:

- 389 lines from two duplicate implementation scripts;
- 150 lines from two duplicate test files; and
- 128 lines from five byte-identical template and standard files.

That is 667 duplicate tracked lines removed. Meta CI runs the pinned toolkit's
own tests and verifies that the checked-out toolkit version agrees with the
real manifest tag and normalized wheel filename. Compatibility-pinned
`addons/*` gitlinks remain immutable release evidence and are deliberately not
used as current-main convention-audit targets.

No renderer Java, add-on version, release tag, compatibility manifest, or
server-installed artifact changes in this consolidation.

## Meta validation

The complete local meta gate passed after the exact v0.3 gitlink and wheel pin
were applied: manifest and gitlink validation, installer tests, integration
tooling, runtime and structure suites, deduplication validation, the real-pin
coherence test, all 25 pinned toolkit tests, shell syntax, workflow lint, and
`git diff --check`. The Java 21 integration harness also passed
`./gradlew --no-daemon clean check build` with Gradle 9.4.0.
