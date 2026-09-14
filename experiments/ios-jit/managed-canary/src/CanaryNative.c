#include <stdint.h>
// Shared by the device app and the host fixture logic check.
int32_t CJCanaryInvokeCallback(int32_t (*callback)(int32_t), int32_t challenge) {
    return callback(challenge) + 13;
}
