# -*- coding: utf-8 -*-
#
# Copyright (C) 2026, Pisi Linux Community
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

"""Architecture table.

Every place in PiSi that needs to know something about the machine it
builds for (the GNU host triplet, default compiler flags, the name the
kernel build system uses, where the kernel image ends up, which extra
build types such as emul32 make sense) asks this module instead of
hard-coding x86 values. Adding an architecture means adding one entry to
ARCHITECTURES below.

The names used in pisi.conf, in package file names and in <ExcludeArch>
are the canonical names (x86_64, i686, aarch64). Common aliases (amd64,
arm64, ...) are accepted as input and normalised with canonical().
"""

import os

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.ugettext

import pisi


class Error(pisi.Error):
    pass


class ArchInfo(object):
    """Facts about one architecture, see ARCHITECTURES for the values."""

    def __init__(self, name, aliases, host, cflags, kernel_arch,
                 kernel_image, build_types, multilib_dir):
        # canonical name, as written in pisi.conf and package file names
        self.name = name
        # other spellings of the same architecture (uname, Debian, Linux)
        self.aliases = aliases
        # GNU host triplet; gcc is installed as "<host>-gcc"
        self.host = host
        # default CFLAGS/CXXFLAGS for pisi.conf
        self.cflags = cflags
        # value of ARCH= for the kernel build system
        self.kernel_arch = kernel_arch
        # kernel image produced by "make", relative to the source tree
        self.kernel_image = kernel_image
        # extra build types (besides the default "") this architecture supports
        self.build_types = build_types
        # directory under /usr for the secondary ABI of multilib builds, or None
        self.multilib_dir = multilib_dir

    def supports_build_type(self, build_type):
        """False only for architecture-bound build types this architecture
        lacks (see ARCHITECTURE_BOUND_BUILD_TYPES). Recipe-specific build
        types such as zlib's "minizip" build everywhere."""
        if build_type not in ARCHITECTURE_BOUND_BUILD_TYPES:
            return True
        return build_type in self.build_types


# Build types that only make sense on some architectures. Any other value
# of <Package buildType="..."> is a recipe's own extra pass and is built on
# every architecture, as before.
#   emul32: 32-bit multilib libraries next to the 64-bit ones (x86_64)
#   pae:    32-bit kernel with physical address extension (i686)
ARCHITECTURE_BOUND_BUILD_TYPES = ("emul32", "pae")

_COMMON_FLAGS = "-O2 -pipe -fstack-protector -D_FORTIFY_SOURCE=2"

ARCHITECTURES = {
    "x86_64": ArchInfo(
        name="x86_64",
        aliases=("amd64", "x86-64", "x64"),
        host="x86_64-pc-linux-gnu",
        cflags="-mtune=generic -march=x86-64 %s" % _COMMON_FLAGS,
        kernel_arch="x86_64",
        kernel_image="arch/x86/boot/bzImage",
        # 32-bit userland libraries next to the 64-bit ones (multilib)
        build_types=("emul32",),
        multilib_dir="lib32"),

    "i686": ArchInfo(
        name="i686",
        aliases=("i386", "i486", "i586"),
        host="i686-pc-linux-gnu",
        cflags="-mtune=generic -march=i686 %s" % _COMMON_FLAGS,
        kernel_arch="i386",
        kernel_image="arch/x86/boot/bzImage",
        build_types=("pae",),
        multilib_dir=None),

    "aarch64": ArchInfo(
        name="aarch64",
        aliases=("arm64", "armv8"),
        host="aarch64-pc-linux-gnu",
        cflags="-mtune=generic -march=armv8-a %s" % _COMMON_FLAGS,
        kernel_arch="arm64",
        # UEFI-bootable compressed image; the EFI stub is part of Image
        kernel_image="arch/arm64/boot/Image.gz",
        build_types=(),
        multilib_dir=None),
}


def canonical(name):
    """Return the canonical architecture name for name or one of its aliases.

    Raises Error for an unknown architecture, so that a typo in pisi.conf
    or in <ExcludeArch> is reported instead of silently ignored.
    """
    if name in ARCHITECTURES:
        return name
    for info in ARCHITECTURES.values():
        if name in info.aliases:
            return info.name
    raise Error(_("Unknown architecture: %s") % name)


def get(name):
    """Return the ArchInfo for name (canonical name or alias)."""
    return ARCHITECTURES[canonical(name)]


def machine():
    """Canonical name of the architecture this process runs on.

    Falls back to x86_64 when the machine is not in the table, which keeps
    the historical behaviour of PiSi on unknown hardware.
    """
    try:
        return canonical(os.uname()[4])
    except Error:
        return "x86_64"


def same(first, second):
    """True when two architecture names mean the same architecture."""
    try:
        return canonical(first) == canonical(second)
    except Error:
        return first == second


def excluded(architecture, exclude_list):
    """True when architecture is listed (by any spelling) in exclude_list."""
    for entry in exclude_list:
        if same(architecture, entry.strip()):
            return True
    return False
