# W29 — Small opt-in diagnostic C header

Write ONE C11 header for D:/Dev/REA/lab/reports/W29-save_test_fault.h, nothing else.
This is a test-only process interruption, not an atomic-save mechanism.

API: static inline void save_test_after_write(bool is_save).
Include pragma once and standard stdbool.h, stdio.h, stdlib.h, string.h.
If is_save is false, or getenv("PVR_TEST_SAVE_AFTER_WRITE") is NULL or not exactly "1", return normally.
Otherwise emit exactly "[save-test] after write before Flush/Commit\n" to stderr, fflush(stderr), then _Exit(86).
Do not mutate files, use other APIs, cache environment variables, or add other features.

Native oracle exists: tools/verify/test_save_fault.py. Expected process exits:
flag absent/save -> 0; flag 0/save -> 0; flag 1/non-save -> 0; flag 1/save -> 86 with the exact stderr marker.
The caller will invoke this ONLY after a successful guest pwrite, before its later Flush/Commit commands.
Return a COMPLETE header inside ONE closed fenced c block. At most 25 code lines, no prose.
