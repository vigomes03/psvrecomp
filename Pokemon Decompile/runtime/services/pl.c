#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../hle.h"
#include "../ipc.h"
#include "../kernel.h"

static uint8_t g_font_mem[0x1100000];
static bool g_fonts_loaded = false;
static uint32_t g_font_handle = 0;
static KSharedMem *g_shared_mem = NULL;
static uint32_t g_region_offset[6], g_region_size[6];

static void on_map(KSharedMem *s) {
    if (s->guest_addr) {
        memcpy((void *)(uintptr_t)s->guest_addr, g_font_mem, sizeof(g_font_mem));
    }
}

static void load_fonts(void) {
    if (g_fonts_loaded) return;
    
    const char *font_dir = getenv("PVR_SYSFONT_DIR");
    if (!font_dir) font_dir = "sysfont";
    
    uint32_t total_bytes = 0;
    int loaded_count = 0;
    
    for (int i = 0; i < 6; i++) {
        char path[512];
        snprintf(path, sizeof(path), "%s/%d.ttf", font_dir, i);
        
        FILE *f = fopen(path, "rb");
        if (!f) {
            LOG("[pl] font %u missing (%s)\n", i, path);
            g_region_offset[i] = 0;
            g_region_size[i] = 0;
            continue;
        }
        
        fseek(f, 0, SEEK_END);
        long ttf_size = ftell(f);
        fseek(f, 0, SEEK_SET);
        
        if (ttf_size <= 0) {
            fclose(f);
            g_region_offset[i] = 0;
            g_region_size[i] = 0;
            continue;
        }
        
        uint32_t offset = total_bytes;
        uint32_t aligned_offset = (offset + 8 + 3) & ~3; // align to 4 bytes
        uint32_t header_offset = aligned_offset - 8;
        
        if (header_offset + 8 + ttf_size > sizeof(g_font_mem)) {
            LOG("[pl] font %u too large, skipping\n", i);
            fclose(f);
            g_region_offset[i] = 0;
            g_region_size[i] = 0;
            continue;
        }
        
        // Write header
        uint32_t *header = (uint32_t *)(g_font_mem + header_offset);
        header[0] = 0x18029a7f;
        header[1] = ttf_size ^ 0x49621806;
        
        // Write TTF data
        fread(g_font_mem + aligned_offset, 1, ttf_size, f);
        fclose(f);
        
        g_region_offset[i] = aligned_offset;
        g_region_size[i] = ttf_size;
        
        total_bytes = aligned_offset + ttf_size;
        loaded_count++;
    }
    
    LOG("[pl] shared fonts: %u loaded, %u bytes\n", loaded_count, total_bytes);
    g_fonts_loaded = true;
}

SERVICE("pl:u", pl_u) {
    (void)s;
    
    switch (req->cmd) {
        case 0: { // RequestLoad
            uint32_t type = IN(uint32_t, 0);
            if (type < 6) {
                load_fonts();
            }
            break;
        }
        case 1: { // GetLoadState
            uint32_t type = IN(uint32_t, 0);
            OUT(uint32_t, 0) = (type < 6) ? 1 : 0; // Loaded
            resp_size(resp, 4);
            break;
        }
        case 2: { // GetSize
            uint32_t type = IN(uint32_t, 0);
            if (type >= 6) {
                OUT(uint32_t, 0) = 0;
            } else {
                load_fonts();
                OUT(uint32_t, 0) = g_region_size[type];
            }
            resp_size(resp, 4);
            break;
        }
        case 3: { // GetSharedMemoryAddressOffset
            uint32_t type = IN(uint32_t, 0);
            if (type >= 6) {
                OUT(uint32_t, 0) = 0;
            } else {
                load_fonts();
                OUT(uint32_t, 0) = g_region_offset[type];  // (already past the 8-byte header)
            }
            resp_size(resp, 4);
            break;
        }
        case 4: { // GetSharedMemoryNativeHandle
            if (!g_shared_mem) {
                load_fonts();
                g_shared_mem = kernel_create_shared_memory(0x1100000, on_map, &g_font_handle);
            }
            resp->copy_handles[resp->ncopy++] = g_font_handle;
            break;
        }
        case 5:
        case 6: { // GetSharedFontInOrderOfPriority(ForSystem)
            load_fonts();
            
            IpcBuf *buf0 = out_buf(req, 0);
            IpcBuf *buf1 = out_buf(req, 1);
            IpcBuf *buf2 = out_buf(req, 2);
            
            uint32_t n = 0;
            if (buf0 && buf1 && buf2) {
                int max_entries = 6;
                max_entries = (int)(buf0->size / sizeof(uint32_t)) < max_entries ? 
                              (int)(buf0->size / sizeof(uint32_t)) : max_entries;
                max_entries = (int)(buf1->size / sizeof(uint32_t)) < max_entries ? 
                              (int)(buf1->size / sizeof(uint32_t)) : max_entries;
                max_entries = (int)(buf2->size / sizeof(uint32_t)) < max_entries ? 
                              (int)(buf2->size / sizeof(uint32_t)) : max_entries;
                
                for (int i = 0; i < max_entries; i++) {
                    if (buf0 && buf0->size >= (i + 1) * sizeof(uint32_t)) {
                        ((uint32_t *)buf0->addr)[i] = i;
                    }
                    
                    if (buf1 && buf1->size >= (i + 1) * sizeof(uint32_t)) {
                        ((uint32_t *)buf1->addr)[i] = g_region_offset[i];
                    }
                    
                    if (buf2 && buf2->size >= (i + 1) * sizeof(uint32_t)) {
                        ((uint32_t *)buf2->addr)[i] = g_region_size[i];
                    }
                }
                
                n = max_entries;
            }
            
            OUT(uint8_t, 0) = 1; // fonts loaded
            OUT(uint32_t, 4) = n;
            resp_size(resp, 8);
            break;
        }
        default:
            LOG("[pl] cmd %u (ok)\n", req->cmd);
            break;
    }
}
