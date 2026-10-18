// Test-only interruption after a guest save write, before Flush/Commit; no transaction guarantee.
#pragma once
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static inline void save_test_after_write(bool is_save) {
    const char *flag = getenv("PVR_TEST_SAVE_AFTER_WRITE");
    if (!is_save || !flag || strcmp(flag, "1") != 0) return;
    fputs("[save-test] after write before Flush/Commit\n", stderr);
    fflush(stderr);
    _Exit(86);
}
