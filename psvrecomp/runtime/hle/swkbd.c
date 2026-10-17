// Software keyboard (naming Link on a new file, ...). On the Switch nn::swkbd::ShowKeyboard launches the keyboard
// library applet; our am service has no applets, so the game crashed. ShowKeyboard is replaced here: the overlay
// (runtime/ui/menu.mm menu_keyboard_run) asks for the text - typed directly with a keyboard, an on-screen keyboard
// with a controller - while this (game) thread keeps re-presenting the last frame.
#include <stdio.h>
#include <string.h>

#include "../hle.h"

int menu_keyboard_run(const char *initial, int max_len, char *out, int cap);  // runtime/ui/menu.mm

// nn::swkbd::ShowKeyboard(nn::swkbd::String *out, const nn::swkbd::ShowKeyboardArg &arg) -> nn::Result
// String = {void *ptr; size_t bufSize}
// ShowKeyboardArg (probed 2026-10-08, naming Link): +0x3ac text max length, +0x3b0 min length, +0x3c0 / +0x3c4
// initial text offset / length (UTF-16) in the work buffer at +0x4d0. The game reads the answer as UTF-8.
HLE_FUNC("_ZN2nn5swkbd12ShowKeyboardEPNS0_6StringERKNS0_15ShowKeyboardArgE", swkbd_show) {
    uint64_t out = c->x[0], arg = c->x[1];
    uint64_t ptr = LD64(out), size = LD64(out + 8);
    int max_len = (int)*(const int32_t *)(uintptr_t)(arg + 0x3ac);
    uint32_t off = *(const uint32_t *)(uintptr_t)(arg + 0x3c0), n = *(const uint32_t *)(uintptr_t)(arg + 0x3c4);
    uint64_t wb = LD64(arg + 0x4d0);
    char initial[96] = "";
    for (uint32_t i = 0; wb && i < n && i < sizeof initial - 1; i++) {
        uint16_t ch = *(const uint16_t *)(uintptr_t)(wb + off + 2 * i);
        initial[i] = ch < 0x80 ? (char)ch : '?';
    }
    char text[96];
    int ok = menu_keyboard_run(initial, max_len, text, sizeof text);
    if (!ok) snprintf(text, sizeof text, "%s", initial);  // cancelled: keep what was there
    // (PVRecomp) KeyboardConfig: ... textMaxLength +0x3ac, textMinLength +0x3b0, passwordMode +0x3b4, inputFormMode
    // +0x3b8, isUseNewLine +0x3bc, isUseUtf8 +0x3bd, isUseBlurBackground +0x3be, initial string +0x3c0. Zelda sets
    // isUseUtf8; Violet does not and reads the answer as UTF-16: the UTF-8 bytes of "[USER]" showed up as "?瑱?".
    int utf8 = *(const uint8_t *)(uintptr_t)(arg + 0x3bd);
    {   // (check of the layout above: the bytes the game passed)
        const uint8_t *k = (const uint8_t *)(uintptr_t)(arg + 0x3a8);
        LOG("[swkbd] arg+0x3a8:");
        for (int i = 0; i < 0x20; i++) LOG(" %02x", k[i]);
        LOG("\n");
    }
    LOG("[swkbd] name entry (max %d, initial \"%s\", %s): %s \"%s\"\n", max_len, initial, utf8 ? "utf-8" : "utf-16",
        ok ? "entered" : "cancelled", text);
    if (ptr && size) {
        memset((void *)(uintptr_t)ptr, 0, size);
        if (utf8) {
            snprintf((char *)(uintptr_t)ptr, size, "%s", text);
        } else {  // UTF-8 -> UTF-16LE (BMP), NUL-terminated, at most max_len characters
            uint16_t *o = (uint16_t *)(uintptr_t)ptr;
            size_t cap = size / 2, k = 0;
            for (const unsigned char *q = (const unsigned char *)text; *q && k + 1 < cap && (max_len <= 0 || (int)k < max_len);) {
                uint32_t cp = *q++;
                if (cp >= 0xE0 && q[0] && q[1]) { cp = ((cp & 0x0F) << 12) | ((q[0] & 0x3F) << 6) | (q[1] & 0x3F); q += 2; }
                else if (cp >= 0xC0 && q[0]) { cp = ((cp & 0x1F) << 6) | (q[0] & 0x3F); q += 1; }
                else if (cp >= 0x80) cp = '?';
                o[k++] = (uint16_t)cp;
            }
            o[k] = 0;
        }
    }
    c->x[0] = 0;
}
