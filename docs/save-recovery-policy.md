# Save isolation and recovery policy

## Scope

This policy covers controlled local experiments on copied Pokemon Violet v4.0.0 saves. It does not promise
transactional guest Commit, protection against hardware power loss, or unconditional safety for the manual-play
save directory. Automatic checkpoint history is separate planned scope (REF-03).

## Required operating rules

1. Keep the original source save immutable. Automated game processes receive only a disjoint sandbox under lab/.
2. Reject missing sources, linked entries, source/target overlap and targets outside lab/ before deleting anything.
3. Verify a staging copy by its file-hash manifest before replacing the expendable sandbox.
4. Retain a known-good backup from before each experiment and its source manifest. A newer file is not automatically
   a valid recovery point.
5. Restore only when the owned test game has exited. Never restore under an unrelated or manual game process.
6. Check the original source manifest after every run. After recovery, compare the restored manifest with the
   immutable backup and load a further copy with the actual game.
7. Treat failure injection as explicit test scope. Normal window environments clear PVR_TEST_SAVE_AFTER_WRITE;
   the interruption gate enables it only for its owned copied-save process. No automatic retries mask the first result.

## Observed guest write protocol

The copied-save scenario has run_id=f933f43273. Host tracing observed two reads, a CreateFile attempt for the
existing main file, one write at offset zero, Flush and Commit. No rename appeared in this scenario. A trace
before CreateFile does not establish that creation succeeded. The resulting file hash differed from the input;
backup/corruption/restore has run_id=4ec8dcdc29 and actual reload of that restored new save has run_id=a9bef169e1.

The new save's SHA-256 is `31aa44f401014dd93479a526979853c8417d668338e5ff7266502e16a307019f`.
Private copies and their full manifests remain in ignored lab/; no save bytes are included here.

The host uses in-place pwrite, file-level fsync, and a filesystem Commit handler with no transaction operation.
The observation does not prove every save path follows the same protocol or establish power-loss durability.
A host transaction layer is not required for this bounded lab policy because the source/backup remain immutable
and the disposable copy can be replaced. Unprotected manual-save transactions would need a separate design.

## Deliberate interruption and actual recovery

The native fault oracle checks absent/zero flags, non-save writes and the explicit save-fault case. Only flag
value 1 on a save write exits with code 86; it emits a dedicated marker. It is a test-only boundary after host
pwrite returned without a reported error, before the handler lets the guest continue to Flush/Commit.
It does not simulate a physical power cut or prove an arbitrary partially completed operating-system write.

Matching Vulkan build/link: run_id=6ca1db9532 and run_id=57eeeefd76.
The first interruption attempt, run_id=30cee1fb8b (FAIL), did not reach a write: its input sequence contained modal
acknowledgments needed by the older seed, but the freshly saved state had already acknowledged the tutorial.
The result is retained, not retried invisibly or reclassified as success.

The fresh-state scenario has run_id=7ea127f858. It observed one deliberate fault marker, a real guest write,
child exit code 86, no subsequent Flush/Commit, no unrelated fatal/host exception, byte-exact backup restoration
and an unchanged original source. There was one child attempt, not a retry loop.

Post-interruption restoration reload has run_id=d6946b460e on the matching current-source Vulkan host. The game
read the restored save, presented 1,621 frames without a recorded FATAL/host exception, and the final measured
windows were 28.9/28.9 fps. The copied bytes matched the pre-interruption checkpoint hash. Local Windows OCR of
the retained menu capture found Bag/Boxes/Options/Save, supporting the specific menu-load checkpoint; it is not
human visual approval of the whole route. The source manifest remained unchanged.

## Reproduction entry points

- `gates.py run save_safety --save <immutable seed> --agent user` exercises verified copy/corruption/restoration.
- `gates.py run save_interruption --version v400 --save <immutable seed> --input-script <matched scenario> --agent user`
  launches exactly one owned game process, tests the write boundary and restores its sandbox from backup.
- `gates.py run window --version v400 --save <restored sandbox> --input-script <matched reload scenario> --agent user`
  loads a further copy and records original-source preservation. Use the actual matching Vulkan host/link records.

Run those through `python tools/verify/gates.py`. Scenario state matters: an old seed's tutorial acknowledgment
sequence is not interchangeable with a fresh save's menu sequence. Use each gate record's exact input_script
and source-manifest metadata rather than guessing buttons or selecting the newest directory by timestamp.

## Achieved guarantees and remaining limits

- Verified source isolation, recoverable backup copies, fresh guest-write persistence, a controlled write-boundary
  process interruption, exact restoration and actual game reload are demonstrated by the gate chain above.
- Synthetic interrupted-copy tests additionally cover damage/recovery at the copy-policy level. They are not a
  substitute for the separate real guest write-boundary experiment.
- No atomic multi-file transaction or power-loss test is claimed; no fsync/Commit semantics beyond the observed
  host handlers are inferred. Checkpoint retention and automatic post-save publication belong to REF-03.
- B-03 semantic routes, hardware/controller/audio checks and subjective visual acceptance remain separate.
