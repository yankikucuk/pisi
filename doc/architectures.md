# Architectures in PiSi

PiSi builds and installs packages for one architecture per system, named in
`/etc/pisi/pisi.conf` (`[general] architecture`). Everything that depends on
the architecture comes from one table, `pisi/archinfo.py`.

## Supported architectures

| Name (canonical) | Aliases accepted | GNU host triplet | Kernel `ARCH=` | Kernel image | Architecture-bound build types |
|---|---|---|---|---|---|
| `x86_64` | `amd64`, `x86-64`, `x64` | `x86_64-pc-linux-gnu` | `x86_64` | `arch/x86/boot/bzImage` | `emul32`, `_emul32` (32-bit multilib, `/usr/lib32`) |
| `i686` | `i386`, `i486`, `i586` | `i686-pc-linux-gnu` | `i386` | `arch/x86/boot/bzImage` | `pae` |
| `aarch64` | `arm64`, `armv8` | `aarch64-pc-linux-gnu` | `arm64` | `arch/arm64/boot/Image.gz` | none |

Canonical names are used in `pisi.conf`, in package file names
(`zlib-1.3.2-19-p2-aarch64.pisi`) and should be used in recipes. Aliases are
accepted wherever an architecture is compared, so `<ExcludeArch>arm64</ExcludeArch>`
excludes `aarch64`. An unknown name is an error, not a silent mismatch.

## Configuration defaults

When `pisi.conf` does not set them, `architecture`, `host`, `cflags` and
`cxxflags` default to the values of the machine PiSi runs on
(`os.uname()`). Reference configurations are shipped as `pisi.conf-x86_64`,
`pisi.conf-i686` and `pisi.conf-aarch64`.

## In recipes (`actions.py`)

| Function | Returns |
|---|---|
| `get.ARCH()` | canonical architecture name |
| `get.ARCHINFO()` | the full table entry |
| `get.isX86_64()`, `get.isI686()`, `get.isAARCH64()`, `get.isX86()` | booleans |
| `get.kernelARCH()` | value for the kernel's `ARCH=` |
| `get.multilibDIR()` | `lib32` on x86_64, `None` elsewhere |

Prefer these to comparing `get.ARCH()` with string literals: aliases are
handled and a new architecture only needs a table entry.

`kerneltools` uses the table for `ARCH=` and for the kernel image path, so
kernel recipes need a `configs/kernel-<arch>-config` file per architecture
and nothing else.

## Excluding packages and build types

- `<ExcludeArch>` in `pspec.xml` stops `pisi build` for the listed
  architectures, and `pisi emerge` skips such sources (with a message)
  instead of stopping at the first one.
- Architecture-bound build types are skipped automatically where they do not
  exist: a `<Package buildType="emul32">` is simply not built on aarch64, so
  multilib recipes need no per-architecture conditionals. Recipe-specific
  build types (for example zlib's `minizip`) are built on every architecture.
- `ignored_build_types` in `pisi.conf` still works as before.

## Adding an architecture

Add an `ArchInfo` entry to `ARCHITECTURES` in `pisi/archinfo.py`, a
`pisi.conf-<arch>` reference file, and tests in `tests/archinfotest.py`.
