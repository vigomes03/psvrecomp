// W19 (qwen3-coder-64k, reviewed by Claude): transform feedback layout from an NVN vertex control section.
// Review fixes: *out is zeroed on every -1 path (was left half-filled) and out is checked before the memset.
#include <string.h>
#include "xfb_layout.h"

int xfb_layout_parse(const uint8_t *control, XfbLayout *out) {
    if (!out) return -1;
    memset(out, 0, sizeof(XfbLayout));
    if (!control)
        { memset(out, 0, sizeof(XfbLayout)); return -1; }

    out->enabled = control[0x6ED];
    if (out->enabled == 0)
        return 0;
        
    out->nbuf = control[0x6EC];
    if (out->nbuf < 1 || out->nbuf > 4)
        { memset(out, 0, sizeof(XfbLayout)); return -1; }
        
    for (int b = 0; b < 4; b++) {
        uint8_t active = control[0x6E8 + b];
        if (active) {
            out->buf[b].active = 1;
            
            // Read stride
            uint16_t stride;
            memcpy(&stride, &control[0x6DC + 2*b], sizeof(uint16_t));
            out->buf[b].stride = stride;
            
            if (stride == 0)
                { memset(out, 0, sizeof(XfbLayout)); return -1; }
                
            // Read output
            uint8_t output_byte = control[0xDC + 0x80*b];
            if (output_byte < 0x20) {
                out->buf[b].output = 0xFF;
                { memset(out, 0, sizeof(XfbLayout)); return -1; }
            }
            out->buf[b].output = output_byte - 0x20;
            
            // Read ncomp
            uint8_t ncomp = control[0x4DC + 0x80*b];
            if (ncomp < 1 || ncomp > 4)
                { memset(out, 0, sizeof(XfbLayout)); return -1; }
            out->buf[b].ncomp = ncomp;
            
            // Validate stride >= 4 * ncomp
            if (stride < 4 * ncomp)
                { memset(out, 0, sizeof(XfbLayout)); return -1; }
        }
    }
    
    return out->nbuf;
}
