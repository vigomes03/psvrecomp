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

// Software keyboard (name entry): headless, take PVR_SWKBD_TEXT or keep the game's suggestion.
int menu_keyboard_run(const char *initial, int max_len, char *out, int cap) {
    const char *t = getenv("PVR_SWKBD_TEXT");
    snprintf(out, (size_t)cap, "%.*s", max_len, t ? t : (initial && *initial ? initial : "[USER]"));
    fprintf(stderr, "[swkbd] headless: \"%s\"\n", out);
    return 1;
}
