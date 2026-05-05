# How is python integrated into sigrok

Links

* https://github.com/sigrokproject/libsigrokdecode/tree/master/decoders
* SIGROKDECODE_DIR and SIGROKDECODE_PATH


## Python integration

I’ll inspect the C entry points that initialize Python and load decoders, then map that flow to the decoder-side Python files so you get a clear end-to-end explanation.

I’m now locating the exact Python C-API calls and module glue code to explain embedding mechanics precisely, not just conceptually.

**High-level flow**
1. Build links against Python embedding libs  
   See the embed pkg-config checks in configure.ac and configure.ac.

2. Library startup creates the embedded interpreter  
   In srd.c, srd_init:
   - registers a built-in Python module named sigrokdecode via PyImport_AppendInittab in srd.c
   - starts Python via Py_InitializeEx in srd.c
   - prepends decoder search paths into Python sys.path via srd_decoder_searchpath_add in srd.c
   - then loads decoder modules.

3. C provides the sigrokdecode Python module API  
   Module init is in module_sigrokdecode.c.  
   It creates module sigrokdecode, adds the base class and constants:
   - base class from srd_Decoder_type_new in module_sigrokdecode.c
   - output constants in module_sigrokdecode.c

4. The base class methods are implemented in C  
   The Python-visible methods that decoder authors call are C functions in type_decoder.c:
   - put in type_decoder.c
   - register in type_decoder.c
   - wait in type_decoder.c
   and the type object is created in type_decoder.c.

5. Decoder modules are imported dynamically  
   Decoder loading is in decoder.c:
   - import module by name (directory name) using py_import_by_name in decoder.c, which uses PyImport_Import in util.c
   - get module Decoder class in decoder.c
   - verify it subclasses sigrokdecode.Decoder in decoder.c
   - enforce api_version and required methods like start/decode in decoder.c and decoder.c
   - extract class metadata (id, channels, options, annotations, etc.) into C structs.

6. Runtime execution is C-driven, Python-defined  
   - C instantiates each Python Decoder object in instance.c and instance.c
   - C calls start in instance.c and instance.c
   - C runs decode in a worker thread in instance.c and instance.c
   - frontends push sample chunks to C, which feeds decoder threads in session.c and session.c
   - Python wait blocks until C finds matching sample conditions (bridge in type_decoder.c)
   - Python put sends decoded output back through C callbacks and/or up stacked decoders (implemented at type_decoder.c).

7. Stacking decoders uses Python output routed by C  
   For OUTPUT_PYTHON, C forwards one decoder’s put payload into the next decoder’s decode method (inside Decoder_put logic in type_decoder.c). That is how protocol stacks are chained.

8. Shutdown finalizes Python  
   srd_exit in srd.c unloads decoders/sessions and calls Py_Finalize.

A concrete decoder side example is SPI:
- imports sigrokdecode in pd.py
- subclasses base class in pd.py
- registers outputs in pd.py
- runs decode loop with wait in pd.py and pd.py.


## Which python version in which directory is used

I’ll verify this in the build scripts and C startup path so I can answer exactly which Python binary/library is used and how module search directories are discovered at runtime.

Short answer:
- Runtime embedding does not use a python executable. It links against the Python embedding library selected at configure time.
- The python executable variable is only used for installing decoder files.

Details from this repo:

1. Which Python binary/library is used
- Configure selects the first available pkg-config embedding package from this list: python-3.12-embed, python-3.11-embed, python-3.10-embed, and so on, in configure.ac and configure.ac.
- Those selected modules are stored in SRD_PKGLIBS and then expanded into compiler/linker flags through PKG_CHECK_MODULES in configure.ac.
- The library target links with those flags via LIBSIGROKDECODE_LIBS in Makefile.am.
- So on Linux, this typically resolves to a libpython3.x.so from your system toolchain/pkg-config setup, not a python process invocation.
- On Windows this would resolve to python3x.dll via the corresponding import library, but selection still comes from pkg-config at configure time.

2. Is a python executable used at runtime
- No for embedding.
- Yes for install helper only: PYTHON3 is found in configure.ac and used only by install-decoders in Makefile.am.

3. How “python directory” is found
There are two different directories to distinguish:

- Python standard library/module paths:
  - libsigrokdecode initializes Python with Py_InitializeEx in srd.c.
  - It does not set Py_SetPythonHome or Py_SetPath anywhere in this codebase, so Python finds its own stdlib/site paths using normal interpreter rules.
- Protocol decoder directories (libsigrokdecode-specific):
  - Added into sys.path by srd_decoder_searchpath_add in srd.c.
  - Sources are:
    - XDG system data dirs via g_get_system_data_dirs in srd.c
    - optional compiled DECODERS_DIR define (non-Windows) from Makefile.am
    - XDG user data dir in srd.c
    - user-provided path argument to srd_init in srd.c
    - SIGROKDECODE_DIR and SIGROKDECODE_PATH env vars in srd.c and srd.c

If you want, I can also give you the exact command sequence to inspect the final linked libpython on your machine after build (for example with ldd/readelf).

## `Py_InitializeEx()`: default rules to find python installation

Yes. In this project, Python startup is done by a plain call to srd.c, and there is no custom path override before it (no Py_SetPythonHome / Py_SetPath in this init path).

So Py_InitializeEx uses CPython’s default path-resolution rules, roughly:

1. Read environment overrides first  
PYTHONHOME, PYTHONPATH (unless isolated/ignore-env modes are enabled, which they are not here).

2. Determine prefix/exec_prefix  
From compiled-in install prefixes and runtime path config logic.

3. Probe filesystem “landmarks”  
Find the stdlib and extension dirs (for example os.py, lib-dynload) relative to computed prefixes.

4. Consider venv markers  
pyvenv.cfg near the program location can redirect to a virtual environment.

5. Build sys.path  
Standard library + site paths + PYTHONPATH entries.

Then libsigrokdecode adds its own protocol-decoder locations into Python sys.path via srd.c, with sources from XDG dirs, DECODERS_DIR, user path, and SIGROKDECODE_DIR / SIGROKDECODE_PATH in srd.c.

