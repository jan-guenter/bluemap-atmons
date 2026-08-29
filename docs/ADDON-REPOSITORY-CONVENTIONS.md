# BlueMap add-on repository conventions

Version `addon-v1` is the common development contract for the BlueMap ATMons
portfolio. It standardizes repository shape and source style without changing
an add-on's released renderer, compatibility profile, artifact identity, or
license.

## Required repository shape

Every deployable add-on repository contains:

- `.editorconfig`, `.gitattributes`, `.gitignore`, and `AGENTS.md`;
- `README.md`, `CHANGELOG.md`, `LICENSE`, `NOTICE.md`, and `THIRD_PARTY.md`;
- `build.gradle`, `settings.gradle`, and `gradle.properties`;
- pinned `ci.yml` and `release.yml` workflows;
- `config/checkstyle/checkstyle.xml` and `docs/RELEASING.md`;
- a family-owned `gallery/`, `provenance/upstreams.json`, Java sources and
  tests, and `src/main/resources/bluemap.addon.json`.

The Gradle wrapper is optional. Repositories that track it must pin and audit
the wrapper JAR. Candidate-mod binaries, generated galleries, worlds, logs,
credentials, and build output stay untracked.

## Java and build contract

- Java sources use UTF-8, LF, no tabs, a final newline, a 120-character
  non-import line limit, and the `io.github.janguenter.bluemap` package root.
- Editor defaults use four-space indentation. The first source-preserving
  rollout does not mass-reindent legacy files merely to satisfy that default.
- Production and test sources pass Checkstyle `10.18.2` with the exact
  `addon-v1` rules.
- Java compilation targets release 21 with `-Xlint:all` and `-Werror`.
- Archives omit empty directories, preserve no file timestamps, and use a
  reproducible entry order.
- The normal `check` task verifies tests and the production/source artifact
  boundaries. Family-specific exact-input, gallery, provenance, and release
  gates remain in their owning repository.
- Workflow actions are pinned to full commit identities. Mutable action tags
  are not accepted.

## Stable and variable parts

The common contract owns formatting, repository hygiene, the generic Gradle
shell, artifact-boundary vocabulary, and CI/release policy. These remain
family-owned and must not be normalized mechanically:

- exact mod and resource pins;
- add-on ID, package, entrypoint, module name, Maven coordinates, and notices;
- activation routes, block and block-entity registrations;
- decoders, normalized models, geometry, UVs, material and transparency rules;
- gallery cases and accepted artifact identities;
- license and provenance choices.

Differences in those fields are configuration or renderer behavior, not style
drift.

The first portfolio rollout is deliberately source-preserving. The common
rules accept a few harmless legacy forms, including unused imports, so that a
tooling-only pull request cannot alter a sealed production JAR. Those files
can be cleaned when their next behavioral release already requires a new
artifact identity. New code should still avoid the accepted legacy forms.

## Rollout and versioning

Repository-only changes use a feature branch and pull request. They do not
change `addon_version`, published tags, or the ATMons compatibility manifest
because production sources and JAR behavior are unchanged. The rollout gate
rejects Java changes, and repositories with sealed production-JAR checks must
still reproduce their accepted artifact. The next behavioral release inherits
the consolidated tooling and goes through the existing owner visual-acceptance
and release gates.

Run the contract audit against one or more checked-out repositories with:

```bash
PYTHONPATH=toolkit/src python -m bluemap_addon_toolkit \
  conventions check /tmp/bluemap-addon-worktrees/example
```

Use clean child worktrees at their intended rollout commits. Do not point this
audit at `addons/*`: those gitlinks intentionally remain on immutable
compatibility-release commits, many of which predate the repository-contract
rollout.

Render the managed files only into clean child worktrees:

```bash
PYTHONPATH=toolkit/src python -m bluemap_addon_toolkit \
  conventions migrate /tmp/bluemap-addon-worktrees/example --check
PYTHONPATH=toolkit/src python -m bluemap_addon_toolkit \
  conventions migrate /tmp/bluemap-addon-worktrees/example --write
```

The exact toolkit gitlink is the canonical source for the checker, migrator,
and managed templates. It is a development tool, not an installed BlueMap
dependency.
