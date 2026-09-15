/* Host-only overrides for code-manager sizing; never linked into the IPA. */
int cjit_test_pagesize(void) { return 16384; }
int cjit_test_valloc_granule(void) { return 16384; }
