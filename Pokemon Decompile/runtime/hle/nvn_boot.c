// NVN entry points: every NVN function is looked up by name and bound to a host stub.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../hle.h"

static uint64_t nvn_proc(const char *name) {
    if (!name || !*name) return 0;
    HostFn fn = hle_lookup_impl(name);
    if (!fn && getenv("PVR_NVN_MISSING")) {  // phase 4.1: which NVN entry points the game asks for that we lack
        static char seen[512][80];
        static int nseen;
        int dup = 0;
        for (int i = 0; i < nseen; i++) dup |= !strcmp(seen[i], name);
        if (!dup && nseen < 512) {
            snprintf(seen[nseen++], sizeof seen[0], "%s", name);
            LOG("[nvn-missing] %s\n", name);
        }
    }
    return hle_register(name, fn);
}

HLE_FUNC("nvnBootstrapLoader", nvn_bootstrap_loader) {
    const char *name = (const char *)(uintptr_t)c->x[0];
    c->x[0] = nvn_proc(name);
}

// void* nvnDeviceGetProcAddress(const NVNdevice*, const char*)
HLE_FUNC("nvnDeviceGetProcAddress", nvn_device_get_proc_address) {
    const char *name = (const char *)(uintptr_t)c->x[1];
    c->x[0] = nvn_proc(name);
}
