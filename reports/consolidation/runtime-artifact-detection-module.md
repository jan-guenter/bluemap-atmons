# Runtime artifact-detection module

This report records the first production-code extraction selected by the
ATMons 1.2.0 deduplication review. The extraction is intentionally narrow: it
contains only the exact JDK-only artifact pin and detector shared by the
portfolio. It does not contain renderer behavior, BlueMap integration,
activation state, mod-specific policy, or an installed shared runtime.

## Released module

The public
[`bluemap-addon-runtime`](https://github.com/jan-guenter/bluemap-addon-runtime)
repository released `v0.1.0-alpha.1` from true merge commit
`6c062239f2669de9d20da32dc8b5372a5653b19d`. The signed annotated tag object
is `8281b08a5ef97a463a52259f97b48e35c91ad8d3` and peels to that merge.

The module uses the neutral package
`io.github.janguenter.bluemap.addon.runtime.artifact` and requires only Java
21. It has no BlueMap, Minecraft, NeoForge, or production dependency; no mod
descriptor, entrypoint, nested JAR, or module descriptor is present in its
production archive. Consumers pin its release commit as a submodule and
compile its main source into their own JAR. Server administrators must not
install the standalone runtime JAR.

The reviewed PR and publication identities are:

| Evidence | Identity |
| --- | --- |
| Reviewed PR | [#1](https://github.com/jan-guenter/bluemap-addon-runtime/pull/1) |
| Owner-signed feature | `3fc8464371eb4ab86a7b81fa53cb32fcbc2864a8` |
| Synthetic PR checkout | `e4dd03fb780b65e6f81beb5756868ea57ef2833a` |
| PR CI / artifact | `33291545302` / `9726116155` |
| True merge | `6c062239f2669de9d20da32dc8b5372a5653b19d` |
| Exact-main CI / artifact | `33291597036` / `9726132045` |
| Release workflow | `33291651319` |

Both Gradle 9.4.0 and 9.6.1 gates passed locally, on the pull request's actual
synthetic checkout, on exact main, and from the release tag. All published
files reproduce the frozen local and CI copies byte for byte:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| Runtime JAR | 13,472 | `a21295dc296d7f14c63b3088d06c1621af3ada03f69a7a238ceb17f3e88c4d24` |
| Sources JAR | 7,262 | `cf6f8052a63efa8268f6ca06ca399134f7d48f5c8136eca3461174d62a962b93` |
| POM | 1,581 | `8478584e6d1bc8af395bb33c8421f40c038e7eb9372820b62e1ab8652206935b` |
| Gradle module metadata | 2,823 | `dec816d0e8c40a77017d8d950b9d0e276f92e0205ef3f4a51006615207afaa2f` |
| `SHA256SUMS` | 440 | `6425c0cbb7aeb71ee45a7ea73fa985274dae6520773b0ede0676665896593037` |

The five release attestations verify against the tag workflow and merge
commit. The Maven publication contains the same four publication files with
the same bytes.

## Extraction evidence

The first pilot covers LaserIO, More Red, and Little Big Redstone. Their local
copies of both production classes are exact after changing only the package
declaration:

- `ArtifactPin.java`, 41 lines;
- `ExactArtifactDetector.java`, 272 lines; and
- `ExactArtifactDetectorTest.java`, with the same cases in all three
  consumers after package normalization.

The release module preserves those original cases and adds differential
coverage against frozen LaserIO-origin oracles. Across the three consumers,
the pilot can remove 33,987 bytes of repeated production source and 10,266
bytes of repeated tests. `AddonRuntime` remains consumer-owned because its
diagnostics and activation state are outside the v0.1 contract.

## Signed consumer candidates

The three pilot repositories were promoted from final, owner-signed
candidates. Each candidate pins runtime commit
`6c062239f2669de9d20da32dc8b5372a5653b19d`, whose main-source tree is
`c70cf01d3196eb8a8eeacb572f7f3ceb6f3e2025`. The table retains the signed
pre-merge boundary separately from GitHub's synthetic and final merge
commits.

| Add-on | Baseline commit | Signed candidate | Candidate tree | Version |
| --- | --- | --- | --- | --- |
| LaserIO | `d0c6b834310206251a92af136d01046a257a0bbf` | `87aef9166b62f1b7a9cfe180751bbb73eb5e3464` | `8cbe417d4bddee9b1fb5526df5784ec4361be3b2` | `0.1.0-alpha.2` |
| More Red | `79a377bf340c646de19e08df15fb4a911bf55f44` | `aec1b78e08d380ebfeeca24e725de3f52129263c` | `ca6a40217b696da40e1ef92d67eef6ce48473ba4` | `0.1.0-alpha.2` |
| Little Big Redstone | `4ec7670e2d1aa7af4fb9ce4f06d4e66e2dc87a65` | `78c9f4f63460846d1e9cde81875a5c95b720fd65` | `3dfe9349ef67c4df27cecaca5a290265b53c6a3c` | `0.1.0-alpha.2` |

Complete Java 21 release-candidate gates passed at those exact commits. Each
gate completed 51 actions and reproduced its publication files:

| Add-on | Production JAR | Sources JAR | POM | Module metadata |
| --- | --- | --- | --- | --- |
| LaserIO | 111,676 B `d01eb100dd57f7efc1ac4ce8c004e02320901e83ef16337dac24b9e690849828` | 74,565 B `654a8ab0bfc0ea38b65a638e1f459acef3891e41ddf2607916c9f6468a860429` | 1,317 B `1d0598c7ac8cd13e015f58f343a355fc1691dc638310b40320d1e8ce52737f21` | 2,819 B `7961b5578b6e4ea22fe2c06827916a6bd104ea9018e3a2b985d7c13a0684d84e` |
| More Red | 93,967 B `1c65d4320f0acdbed5bf520858540824459dcd7367b80245d06b23aed728ebb8` | 57,088 B `6db012f4e5db6261049b7ed0b69a0ec0fdcc434dc467df14539c1ed82dded944` | 1,319 B `074ed8bbe2f5e6f4ae683d8d4a3c42220a1ee970b0a27d05b8cf849b1857f225` | 2,817 B `021912128be41ca324c69d4ba37c1d822f8df7445bcc2f61055f6748aa80db29` |
| Little Big Redstone | 55,017 B `b059862aefcd6afdcc2097dd69b7cf22c7b2bb80127de545f519912f6bdcdf0e` | 38,976 B `20402735961144caf70f0ee12783cb585b891aec2b495bf070427959da50128d` | 1,389 B `c49a46f546d769158d239f4c9ce2e7f5436a0dc9dc42825f4b7266584d5023b8` | 2,901 B `5fd0284972704de363252f98d21aa562895536a379732776e31f1f74e231673d` |

The retained Java suites contain 10 tests for LaserIO, 13 for More Red, and
three for Little Big Redstone. The unchanged gallery packages are:

| Add-on | Gallery bytes | SHA-256 |
| --- | ---: | --- |
| LaserIO | 3,870 | `acea3d7134891204f9b2246ed584fa6bfe730a7b8e3cfe2ab19b6187ddaf474b` |
| More Red | 4,546 | `faebaf1139ebf88b6dc5656fa57276957f6120ceea5e75007f2eb9b0df15a8b8` |
| Little Big Redstone | 2,469 | `cf2f3b370ef25ee2f3cbbef7d3c92b5a6d56e27f80985bee917346fd8a8ffe26` |

The archive diffs account for every entry. LaserIO retains 29 of 36
production entries unchanged, More Red 25 of 32, and Little Big Redstone 16
of 23. Each has three expected metadata or caller changes and four exact
local-to-shared class relocations. The sources archives retain 22 of 26, 18
of 22, and 15 of 19 entries respectively, with two caller imports and two
source relocations in each. Package-normalized shared source and bytecode are
exact. No renderer, resource, profile, gallery, or acceptance fact changed.

All three settings preflights rejected an uninitialized module, a wrong HEAD,
a dirty checkout, and an indexed gitlink mismatch. They also enforce exact
counts for the four shared production classes and two shared sources and ban
the former consumer-local detector paths. An independent final audit found no
actionable issue in any candidate.

## Combined overlay preparation

The meta-repository's candidate builder now accepts an exact local override
lock without changing the immutable compatibility manifest. The override-path
audit initially found three fail-closed gaps: source-to-JAR correlation,
failure-message path leakage, and permissive Boolean schema handling. The
implementation fixed all three and passed the second audit. The tightened
builder has SHA-256
`895aabaa37e3a8e51b2a5527817cab9f343f983c2765f1e773c452314f6a05b0`.

The final local lock is 1,836 bytes with SHA-256
`c1ef08e6d3b9f771a63fc97564efc1ca427117f3e380ffa4a07e08cf916549a1`.
It binds the three signed commits and production JARs above. The builder
combined them with the other 48 released add-ons and candidate BlueMap commit
`7e07f4e74ec1e92a6ead9aa1e66054af3e133aac`, version
`5.22-feature.backport-5.23-stateless-java-web-server-46`.

Two independent builds produced the same 51 JAR filenames, byte sizes, and
SHA-256 values. Their JAR inventory contains 9,046,059 bytes and hashes to
`ee0ce7203c7c76cd5cec7c0ee98e4ed37265ce3da0385f2514600528f472d977`
when encoded as sorted `filename`, byte count, and SHA-256 rows. The retained
candidate manifest is 86,667 bytes with SHA-256
`ae8defbf51e55b482b6ec190bc77eba26f59897d3ac133464344e197c4a9dad6`.
Its 51-row checksum manifest is 5,663 bytes with SHA-256
`73c827a9d00ae150a023c3af715ea9322ebe500c426b2bf16eec945d02722ba2`.
Trophy Manager remains a released, non-migrated control.

The combined disposable server admitted the 51 candidate add-ons alongside
the exact ATMons 1.2.0 runtime. Its first boot reported one active marker for
every add-on and no inactive or linkage diagnostic. The gate then replaced
the server container and attested a distinct runtime identity before
continuing.

The second boot reproduced the exact 377-JAR runtime inventory, all 51
candidate checksums, the 51-source overlay, the gallery composition, and one
active marker per add-on. The runner then rebuilt and asserted every gallery:
51 passed, zero failed, zero skipped, and zero were performed without an
assertion. The retained 75,741-byte result hashes to
`c3df386d0ce2176d4b5a026bdc5c949e65b8f619f6561828d0aff066ecb67afb`.

## Consumer boundary

Each pilot consumer must:

1. pin the exact release commit at `modules/bluemap-addon-runtime`;
2. fail closed when the committed or indexed gitlink, checkout HEAD,
   cleanliness, initialization, or expected source tree differs;
3. compile only the module's main Java source into its own production JAR;
4. delete its two local production copies and duplicate detector test;
5. admit exactly the four resulting shared class entries and two shared
   source entries while retaining its nested-JAR and foreign-entry bans; and
6. pass its complete isolated release-candidate, archive-diff, deterministic
   gallery, and trust-probe gates.

The source-package relocation changes consumer JAR bytes and therefore
requires a new consumer version and release-only provenance. Upstream pins,
renderer sources, profiles, galleries, and owner-acceptance facts remain
unchanged. The accepted entry manifest may be resealed only after every
unaffected archive entry is shown byte-identical and every changed entry is
accounted for by version metadata, the exact relocation, or the two affected
caller constant pools.

## Pilot release gate

No consumer release is authorized by an isolated green build. The three
candidates must first run together with the other 48 released add-ons on the
disposable ATMons 1.2.0 integration server. The combined gate must verify all
51 add-on activations, reject duplicate or conflicting class definitions,
complete all 51 gallery builds and assertions, and retain Trophy Manager as a
non-migrated control. Consumer PRs and releases follow only after that
combined result has been reviewed.

The isolated candidates, reproducible 51-add-on overlay, mandatory second
restart, 51 activation checks, and all 51 gallery builds and assertions have
passed. That result closes the combined release gate. Consumer pull requests,
exact-main validation, and publication identities are recorded below only
after each corresponding workflow completes.

## Consumer publications

All three candidates were reviewed in pull request #6 of their respective
repositories and merged with explicit two-parent commits. The second parent
of every final merge is the owner-signed candidate above, and every merge has
the same candidate tree. GitHub's distinct synthetic pull-request checkout is
recorded rather than misreported as the tested feature commit.

| Add-on | Synthetic PR checkout | Final merge | Signed tag object |
| --- | --- | --- | --- |
| [LaserIO #6](https://github.com/jan-guenter/bluemap-laserio-addon/pull/6) | `b75fdc3ed705f3958deb54c3f54f5b1a7fcfb03f` | `e18f93588eacd3a188190a0318b32f11a038f798` | `91fbb3f829b5e5e87dc46868b18169df431f1217` |
| [More Red #6](https://github.com/jan-guenter/bluemap-morered-addon/pull/6) | `009b0017070bb66a6dc0b14608bd423e69a9c34e` | `c5a791d97a7a7980d59310d45878fc5454620139` | `41631f71f7588a11e9badca62e397c4ac81b6d48` |
| [Little Big Redstone #6](https://github.com/jan-guenter/bluemap-little-big-redstone-addon/pull/6) | `140389d6ab6279daff6d2bb678fde989030ec45f` | `8d23ef80411d1b6f06534cbd5cf7d92247f2f74a` | `3a74cc9817ebd47b8b9f68cb37b7b7b9d6cc721c` |

PR and exact-main CI independently reproduced each add-on's four sealed
publication files byte for byte:

| Add-on | PR CI / artifact | Exact-main CI / artifact | Release workflow |
| --- | --- | --- | --- |
| LaserIO | `33295174235` / `9727219153` | `33295357956` / `9727259700` | `33295475488` |
| More Red | `33295218950` / `9727214711` | `33295352406` / `9727259030` | `33295469638` |
| Little Big Redstone | `33295187779` / `9727207769` | `33295348201` / `9727258896` | `33295471993` |

The signed annotated `v0.1.0-alpha.2` tags peel to those exact final merges.
The resulting [LaserIO](https://github.com/jan-guenter/bluemap-laserio-addon/releases/tag/v0.1.0-alpha.2),
[More Red](https://github.com/jan-guenter/bluemap-morered-addon/releases/tag/v0.1.0-alpha.2),
and [Little Big Redstone](https://github.com/jan-guenter/bluemap-little-big-redstone-addon/releases/tag/v0.1.0-alpha.2)
public prereleases are not drafts. Their `SHA256SUMS` files are respectively
440 bytes / `aeeb74f8e793dc11be07efe34b3747909d8cb2f55f21d6c977408e8f649e0ce3`,
440 bytes / `1cd45971087a445836b250b955c4a3119a464f4059efb6920cf6fad9d27acad6`,
and 488 bytes / `812a04fe686c574d86198c2ab7cc9a314ec0f5d8ed81abdc9ad1c6dc25a6a072`.
All public assets passed their checksum manifests and Sigstore provenance
verification against the exact release workflow, tag ref, and merge commit.

The Maven package records exist as version IDs `65999838`, `65999839`, and
`65999835`, and every workflow's publication step passed. Direct registry
byte comparison was unavailable because the current token lacks
`read:packages`; the public release assets remain independently byte-verified.
