#include "VMRange.h"
#include <mach/mach.h>
#include <mach/vm_map.h>

int CJQueryDarwinVMEntry(uintptr_t cursor, CJVMEntry *entry, void *context) {
    (void)context;
    vm_address_t start = cursor;
    vm_size_t size = 0;
    vm_region_basic_info_data_64_t info = {0};
    mach_msg_type_number_t count = VM_REGION_BASIC_INFO_COUNT_64;
    mach_port_t object = MACH_PORT_NULL;
    kern_return_t result = vm_region_64(mach_task_self(), &start, &size, VM_REGION_BASIC_INFO_64,
                                        (vm_region_info_t)&info, &count, &object);
    if (object != MACH_PORT_NULL) mach_port_deallocate(mach_task_self(), object);
    if (result == KERN_SUCCESS) {
        *entry = (CJVMEntry){.address = start, .length = size,
                            .protection = info.protection, .maximum_protection = info.max_protection};
    }
    return result;
}
