// btm:u (Bluetooth manager, user): no Bluetooth on the host. GetCore returns an IBtmUserCore whose Acquire*Event
// commands hand out never-signalled events; everything else succeeds with zeroed output. PVRecomp: without the core
// object nn::btm::user::InitializeBtmUserInterface aborted (v400 boot, 14/10). Command ids from the public
// switchbrew / yuzu-family service tables.
#include <stdint.h>
#include <stdio.h>

#include "../hle.h"
#include "../ipc.h"
#include "../kernel.h"

static void btm_user_core(Service *s, IpcReq *req, IpcResp *resp) {
    (void)s;
    switch (req->cmd) {
    case 0:   // AcquireBleScanEvent
    case 17:  // AcquireBleConnectionEvent
    case 26:  // AcquireBleServiceDiscoveryEvent
    case 33: {  // AcquireBleMtuConfigEvent
        uint32_t w, r;
        kernel_create_event_pair(&w, &r);
        OUT(uint8_t, 0) = 1;  // is_valid
        resp_size(resp, 4);
        resp->copy_handles[resp->ncopy++] = r;
        break;
    }
    default:
        LOG("[btm] IBtmUserCore cmd %u (no bluetooth, ok)\n", req->cmd);
        resp_size(resp, 0x40);  // zeroed outputs
    }
}

SERVICE("btm:u", btm_u) {
    (void)s;
    if (req->cmd == 0) {  // GetCore
        ipc_return_object(resp, service_new("IBtmUserCore", btm_user_core, NULL));
        return;
    }
    LOG("[btm] btm:u cmd %u (ok)\n", req->cmd);
}
