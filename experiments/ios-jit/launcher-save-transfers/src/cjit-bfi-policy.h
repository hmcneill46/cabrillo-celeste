#ifndef CJIT_BFI_POLICY_H
#define CJIT_BFI_POLICY_H
#include <string.h>
#include <mono/metadata/class-internals.h>
#include <mono/metadata/image.h>
// This opt-in affects only FemtoHelper's beforefieldinit types. The launcher
// independently requires the exact pinned original archive. Core libraries,
// explicit static constructors and other mods retain the accepted Mono policy.
// ECMA-335 I.8.9.5 permits initialization at the first static field access.
static inline gboolean cjit_defer_beforefieldinit(MonoClass *klass) {
    const char *image=mono_image_get_name(m_class_get_image(klass));
    return mono_class_is_before_field_init(klass) && image &&
        (!strcmp(image,"FemtoHelper") || !strcmp(image,"FemtoHelper.dll"));
}
#endif
