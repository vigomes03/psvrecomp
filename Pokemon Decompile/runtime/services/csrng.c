// csrng (spl's random service): GenerateRandomBytes from the host's CSPRNG. PVRecomp: without it the logging stub
// returned zero-filled buffers and the game retried, then svcBreak'd (v400 boot, 14/10).
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <windows.h>
#include <bcrypt.h>

#include "../hle.h"
#include "../ipc.h"

SERVICE("csrng", csrng) {
    (void)s;
    (void)resp;
    if (req->cmd != 0) {
        LOG("[csrng] cmd %u (ok)\n", req->cmd);
        return;
    }
    IpcBuf *b = out_buf(req, 0);
    if (b && b->size &&
        BCryptGenRandom(NULL, (PUCHAR)(uintptr_t)b->addr, (ULONG)b->size, BCRYPT_USE_SYSTEM_PREFERRED_RNG) != 0)
        FATAL("[csrng] BCryptGenRandom failed\n");
}
