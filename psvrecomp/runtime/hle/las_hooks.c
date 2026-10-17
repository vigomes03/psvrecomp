// PVRecomp: neutral versions of LAS Recomp's Zelda-specific hooks that the reused services call
// (save editor, extended flags, romfs read hook) plus a headless software keyboard.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void romfs_file_read_hook(const char *path) { (void)path; }
void save_editor_file_read(const char *path, uint64_t addr, int64_t off, int64_t size) {
    (void)path; (void)addr; (void)off; (void)size;
}
void flags_ext_save_read(const char *path, uint64_t addr, int64_t off, int64_t size) {
    (void)path; (void)addr; (void)off; (void)size;
}
void flags_ext_save_written(const char *path, uint64_t addr, int64_t off, int64_t size) {
    (void)path; (void)addr; (void)off; (void)size;
}

// Software keyboard (name entry). PVR_SWKBD_TEXT=<text>: that answer, no window. Timed runs (PVR_RUN_SECONDS > 0, the
// test pipeline): the game's suggestion or "[USER]". Otherwise (playing): a text box in front of the game
// (plat_text_prompt, Windows); Cancel / empty keeps the suggestion.
int plat_text_prompt(const char *title, const char *initial, int max_len, char *out, int cap);
int menu_keyboard_run(const char *initial, int max_len, char *out, int cap) {
    const char *t = getenv("PVR_SWKBD_TEXT"), *rs = getenv("PVR_RUN_SECONDS");
    const char *dflt = initial && *initial ? initial : "[USER]";
    if (!t && !(rs && atoi(rs) > 0)) {
#ifdef _WIN32
        char got[96];
        if (plat_text_prompt("PSV Recomp - enter text", dflt, max_len, got, sizeof got) && got[0]) {
            snprintf(out, (size_t)cap, "%s", got);
            fprintf(stderr, "[swkbd] typed: \"%s\"\n", out);
            return 1;
        }
#endif
    }
    snprintf(out, (size_t)cap, "%.*s", max_len, t ? t : dflt);
    fprintf(stderr, "[swkbd] %s: \"%s\"\n", t ? "PVR_SWKBD_TEXT" : "default", out);
    return 1;
}
