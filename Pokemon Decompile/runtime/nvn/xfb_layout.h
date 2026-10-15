// Transform feedback layout of an NVN vertex shader, read from its glslc control section (PVRecomp phase 4).
// Field offsets found by comparing the game's 1009 vertex control sections (28 use transform feedback); see
// work/cards/W19-xfb-layout.md. Implementation: xfb_layout.c (W19, qwen).
#pragma once
#include <stdint.h>

typedef struct {
    uint8_t enabled;       // control[0x6ED]
    uint8_t nbuf;          // control[0x6EC]
    struct {
        uint8_t active;    // control[0x6E8 + b]
        uint16_t stride;   // u16 at 0x6DC + 2*b
        uint8_t output;    // control[0xDC + 0x80*b] - 0x20: captured output varying (v<output>)
        uint8_t ncomp;     // control[0x4DC + 0x80*b]: components captured from .x
    } buf[4];
} XfbLayout;

// 0: transform feedback off (*out zeroed); n > 0: enabled with n buffers; -1: enabled but invalid (*out zeroed).
int xfb_layout_parse(const uint8_t *control, XfbLayout *out);
