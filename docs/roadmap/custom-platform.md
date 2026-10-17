# C — Custom platform proof of concept

**State:** not started. **First target:** reversible replacement inside one identified small existing area.
Not a new independent world, scene registry or map editor. Requires [R](scene-study.md) and copied-save safety
from [B](baseline.md). Keep the original packages and normal run path intact.

## C-01 — Identity replacement

- [ ] At the interception layer selected by R-04, substitute an identical selected resource and demonstrate
  unchanged behavior; disable the substitution and demonstrate normal behavior again.

Check inner/outer integrity constraints, size/index/alignment and references; do not assume filesystem hooks
bypass package checks. Implement only the proven layer. New hook names must be introduced/tested, not cited as APIs.
**Acceptance:** matching source/replacement hashes, logged hit at the expected resource, same copied-save route,
no new error, and a verified off switch. A reference run_id and the new run_id are distinct records.
**Old scope:** 10.3.1/10.3.2, relevant round-trip part of 10.2.4.

## C-02 — One visible reversible edit

- [ ] Change one proven transform/material field and observe only the intended change; revert it.

**Acceptance:** known field semantics, before/after observation at matched scene/time, expected resource hit,
no-change control and successful rollback. Do not proceed on a visually plausible but unexplained result.
**Old scope:** 10.3.3. This is a proof of the editing path, not yet custom geometry or collision.

## C-03 — Platform geometry and collision

- [ ] Author a minimal platform resource plus compatible collision, retaining only proven dependencies.

Start with a small bounded shape, conservative materials and valid transforms. Validate generated files against
the parser/schema and game references before loading. Test walking/standing/edges; visual appearance alone fails
acceptance if the character falls through. Do not invent a collision format from the rendering mesh.
**Acceptance:** reproducible authoring input, validated output, intended visible dimensions/placement and actual
standing/walking collision observations with no new FATAL/exception on the specified route.
**Old scope:** 10.4.1/10.4.2/10.4.4. No original assets or generated game-derived data enter git.

## C-04 — Entry, exit, reload and rollback

- [ ] Establish a safe entry/spawn, enter the area, walk on the platform, leave, reenter/reload and disable the mod.

**Acceptance:** entry does not drop the player below collision; the route and copied save remain usable after
leaving/reloading; turning the mod off restores the baseline. Record build ids, real evidence, screenshot paths
and explicit user observations. Declare exactly this platform slice, not arbitrary scene authoring, if it succeeds.
**Old scope:** 10.4.3/10.4.5 and the lifecycle portion of 10.7 (not cell replacement).

## Stop conditions and follow-ups

Stop and report unknown integrity checks, unresolved collision/entry references, unrecoverable copied-save state,
or a reproducible crash. Never silence a failure with a null guard to call the mod successful.
New scenes/warp registration, a JSON/Blender authoring pipeline and open-world replacement remain
[L-11](backlog.md), gated by this narrower experiment.
