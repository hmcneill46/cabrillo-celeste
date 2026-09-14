#!/usr/bin/env python3
"""Apply the bounded ARM64 alias patch to the exact pinned private runtime clone."""
from pathlib import Path
import hashlib,json,subprocess
source=Path(__file__).resolve().parent
root=source.parents[2];runtime=root/'.build/ios-jit/managed-runtime/runtime-v8.0.28'
pin=json.loads((source/'runtime-pin.json').read_text())
assert subprocess.check_output(['git','-C',str(runtime),'rev-parse','HEAD'],text=True).strip()==pin['runtime_commit']
original={};patched={}
def change(name,old,new,count=1):
 name='src/mono/mono/'+name
 if name not in original:
  original[name]=subprocess.check_output(['git','-C',str(runtime),'show','HEAD:'+name],text=True)
  patched[name]=original[name]
 assert patched[name].count(old)==count,(name,old,patched[name].count(old),count)
 patched[name]=patched[name].replace(old,new)

change('utils/mono-codeman.c','#include "config.h"','#include "config.h"\n#include "cjit-mono-bridge.h"')
for file in ['utils/mono-mmap.c','mini/mini.c','mini/mini-runtime.c']:
 change(file,'#include <config.h>','#include <config.h>\n#include "cjit-mono-bridge.h"')
change('arch/arm64/arm64-codegen.h','#include <glib.h>','#include <glib.h>\n#include "cjit-mono-bridge.h"')
change('arch/arm64/arm64-codegen.h','*(guint32*)(p) = (ins);','*(guint32*)CJ_CODE_WRITE((p), 4) = (ins);')
change('arch/arm64/arm64-codegen.h','*(guint32*)p = (*(guint32*)p &','*(guint32*)CJ_CODE_WRITE(p, 4) = (*(guint32*)p &')
# Upstream's register-branch opcode literal overflows signed int when shifted.
# Keep the same bits using an unsigned literal so the real emitter passes UBSan.
change('arch/arm64/arm64-codegen.h','(0x6b << 25)', '(0x6bU << 25)')
change('mini/mini-arm64.c','*(guint64*)code = (guint64)target;','*(guint64*)CJ_CODE_WRITE(code, 8) = (guint64)target;')
change('mini/mini-arm64.c','memcpy (code, ji->data.target, 16);','memcpy (CJ_CODE_WRITE(code, 16), ji->data.target, 16);')
change('mini/mini-arm64.c','mono_arch_flush_icache (guint8 *code, gint size)\n{','mono_arch_flush_icache (guint8 *code, gint size)\n{\n#ifdef CJ_MONO_IOS_JIT\n\tcj_mono_flush (code, size);\n\treturn;\n#endif')
change('mini/tramp-arm64.c','*(gpointer*)slot_addr = addr;','*(gpointer*)CJ_CODE_WRITE((void*)slot_addr, sizeof(gpointer)) = addr;')
change('mini/mini.c','memset (cfg->thunks, 0, cfg->thunk_area);','memset (CJ_CODE_WRITE(cfg->thunks, cfg->thunk_area), 0, cfg->thunk_area);')
change('mini/mini.c','memcpy (code, cfg->native_code, cfg->code_len);','memcpy (CJ_CODE_WRITE(code, cfg->code_len), cfg->native_code, cfg->code_len);')
# Switch metadata is also allocated in executable code pools. Preserve its RX
# identity while translating both the offset table and resolved pointer stores.
change('mini/mini.c','table [i] = GINT_TO_POINTER (patch_info->data.table->table [i]->native_offset);',
       '((gpointer *)CJ_CODE_WRITE(table, sizeof(gpointer) * patch_info->data.table->table_size)) [i] = GINT_TO_POINTER (patch_info->data.table->table [i]->native_offset);')
change('mini/mini.c','table [i] = NULL;',
       '((gpointer *)CJ_CODE_WRITE(table, sizeof(gpointer) * patch_info->data.table->table_size)) [i] = NULL;')
change('mini/mini-runtime.c','jump_table [i] = code + GPOINTER_TO_INT (patch_info->data.table->table [i]);',
       '((gpointer *)CJ_CODE_WRITE(jump_table, sizeof(gpointer) * patch_info->data.table->table_size)) [i] = code + GPOINTER_TO_INT (patch_info->data.table->table [i]);')
change('utils/mono-codeman.c','memset (ptr, 0, size);','memset (CJ_CODE_WRITE(ptr, size), 0, size);')
change('utils/mono-codeman.c','memset (ptr, 0, bsize);','memset (CJ_CODE_WRITE(ptr, bsize), 0, bsize);')
change('utils/mono-codeman.c','memset (chunk->data, fill_value, chunk->size);','memset (CJ_CODE_WRITE(chunk->data, chunk->size), fill_value, chunk->size);',2)
change('utils/mono-codeman.c','#ifdef FORCE_MALLOC','#if defined(CJ_MONO_IOS_JIT)\n\t/* Dynamic methods also use the bounded prepared arena, not executable dlmalloc. */\n\treturn CODE_FLAG_MMAP;\n#elif defined(FORCE_MALLOC)')
for function in ['mono_codeman_enable_write','mono_codeman_disable_write']:
 change('utils/mono-codeman.c',function+' (void)\n{',function+' (void)\n{\n#ifdef CJ_MONO_IOS_JIT\n\t/* All code stores use RW aliases; RX stays executable for other threads. */\n\treturn;\n#endif')
change('utils/mono-mmap.c','mono_valloc (void *addr, size_t length, int flags, MonoMemAccountType type)\n{','''mono_valloc (void *addr, size_t length, int flags, MonoMemAccountType type)
{
#ifdef CJ_MONO_IOS_JIT
	if (flags & MONO_MMAP_EXEC) {
		if (flags & MONO_MMAP_FIXED) return NULL;
		void *prepared = cj_mono_code_alloc (length);
		if (prepared) mono_account_mem (type, (ssize_t)length);
		return prepared;
	}
#endif''', 2)
change('utils/mono-mmap.c','mono_vfree (void *addr, size_t length, MonoMemAccountType type)\n{','''mono_vfree (void *addr, size_t length, MonoMemAccountType type)
{
#ifdef CJ_MONO_IOS_JIT
	if (cj_mono_owns_code (addr)) {
		/* Process-lifetime canary arena: do not unmap prepared pages. */
		mono_account_mem (type, -(ssize_t)length);
		return 0;
	}
#endif''', 2)
receipt={'runtime_commit':pin['runtime_commit'],'files':{}}
previous_path=root/'.build/ios-jit/managed-runtime/runtime-patch-receipt.json'
previous=json.loads(previous_path.read_text()) if previous_path.exists() else {'files':{}}
sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
for name,data in patched.items():
 path=runtime/name;current=path.read_text()
 permitted=[original[name],data]
 old=previous['files'].get(name,{})
 assert current in permitted or sha(current)==old.get('patched_sha256'),f'Unrecognized edits: {name}'
 path.write_text(data)
 receipt['files'][name]={'original_sha256':sha(original[name]),'patched_sha256':sha(data)}
previous_path.write_text(json.dumps(receipt,indent=2)+'\n')
diff=subprocess.check_output(['git','-C',str(runtime),'diff','--',*patched],text=True)
(source/'runtime-alias.patch').write_text(diff)
print('Patched',len(patched),'runtime files; exact sources and patch hashes recorded.')
