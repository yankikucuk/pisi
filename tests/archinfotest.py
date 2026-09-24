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

"""Tests for the architecture table (pisi/archinfo.py)."""

import os
import unittest

import pisi.archinfo as archinfo


class ArchInfoTestCase(unittest.TestCase):

    def testCanonicalNames(self):
        for name in ("x86_64", "i686", "aarch64"):
            self.assertEqual(archinfo.canonical(name), name)

    def testAliases(self):
        self.assertEqual(archinfo.canonical("amd64"), "x86_64")
        self.assertEqual(archinfo.canonical("x86-64"), "x86_64")
        self.assertEqual(archinfo.canonical("arm64"), "aarch64")
        self.assertEqual(archinfo.canonical("i386"), "i686")

    def testUnknownArchitectureIsAnError(self):
        self.assertRaises(archinfo.Error, archinfo.canonical, "sparc64")

    def testKernelValues(self):
        self.assertEqual(archinfo.get("x86_64").kernel_arch, "x86_64")
        self.assertEqual(archinfo.get("i686").kernel_arch, "i386")
        self.assertEqual(archinfo.get("aarch64").kernel_arch, "arm64")
        self.assertEqual(archinfo.get("x86_64").kernel_image, "arch/x86/boot/bzImage")
        self.assertEqual(archinfo.get("arm64").kernel_image, "arch/arm64/boot/Image.gz")

    def testHostTriplets(self):
        self.assertEqual(archinfo.get("x86_64").host, "x86_64-pc-linux-gnu")
        self.assertEqual(archinfo.get("aarch64").host, "aarch64-pc-linux-gnu")

    def testFlagsDoNotLeakAcrossArchitectures(self):
        self.assertTrue("-march=x86-64" in archinfo.get("x86_64").cflags)
        self.assertTrue("-march=armv8-a" in archinfo.get("aarch64").cflags)
        self.assertFalse("x86" in archinfo.get("aarch64").cflags)

    def testEmul32OnlyOnX86_64(self):
        self.assertTrue(archinfo.get("x86_64").supports_build_type("emul32"))
        self.assertFalse(archinfo.get("aarch64").supports_build_type("emul32"))
        self.assertFalse(archinfo.get("i686").supports_build_type("emul32"))
        # the variant for recipes with their own 32-bit setup is bound too
        self.assertTrue(archinfo.get("x86_64").supports_build_type("_emul32"))
        self.assertFalse(archinfo.get("aarch64").supports_build_type("_emul32"))
        for name in archinfo.ARCHITECTURES:
            self.assertTrue(archinfo.get(name).supports_build_type(""))

    def testRecipeBuildTypesBuildEverywhere(self):
        # zlib builds minizip as an extra pass; that is not architecture-bound
        for name in archinfo.ARCHITECTURES:
            self.assertTrue(archinfo.get(name).supports_build_type("minizip"))

    def testMultilibDirectory(self):
        self.assertEqual(archinfo.get("x86_64").multilib_dir, "lib32")
        self.assertEqual(archinfo.get("aarch64").multilib_dir, None)

    def testSame(self):
        self.assertTrue(archinfo.same("arm64", "aarch64"))
        self.assertTrue(archinfo.same("amd64", "x86_64"))
        self.assertFalse(archinfo.same("aarch64", "x86_64"))

    def testExcluded(self):
        self.assertTrue(archinfo.excluded("aarch64", ["i686", "arm64"]))
        self.assertTrue(archinfo.excluded("x86_64", [" amd64 "]))
        self.assertFalse(archinfo.excluded("x86_64", ["aarch64"]))
        self.assertFalse(archinfo.excluded("x86_64", []))

    def testMachineIsKnown(self):
        # whatever the test machine is, the result is a canonical name
        self.assertTrue(archinfo.machine() in archinfo.ARCHITECTURES)

    def testMachineMatchesUname(self):
        uname = os.uname()[4]
        try:
            expected = archinfo.canonical(uname)
        except archinfo.Error:
            expected = "x86_64"
        self.assertEqual(archinfo.machine(), expected)


class ConfigDefaultsTestCase(unittest.TestCase):

    def testDefaultsFollowTheMachine(self):
        import pisi.configfile as configfile
        machine = archinfo.get(archinfo.machine())
        self.assertEqual(configfile.GeneralDefaults.architecture, machine.name)
        self.assertEqual(configfile.BuildDefaults.host, machine.host)
        self.assertEqual(configfile.BuildDefaults.cflags, machine.cflags)


class _Package(object):
    def __init__(self, name, build_type=None):
        self.name = name
        self.buildType = build_type


class _Spec(object):
    def __init__(self, packages):
        self.packages = packages


class _Values(object):
    """Stands in for ctx.config.values with only what get_build_types reads."""
    def __init__(self, architecture, ignored=""):
        class General(object):
            pass
        class Build(object):
            pass
        self.general = General()
        self.general.architecture = architecture
        self.build = Build()
        self.build.ignored_build_types = ignored


class BuildTypesTestCase(unittest.TestCase):
    """Builder.get_build_types skips build types the architecture lacks."""

    def setUp(self):
        import pisi.context as ctx
        import pisi.ui
        self.ctx = ctx
        self.saved = ctx.config, ctx.ui
        class Config(object):
            pass
        ctx.config = Config()
        ctx.ui = pisi.ui.UI()

    def tearDown(self):
        self.ctx.config, self.ctx.ui = self.saved

    def build_types(self, architecture, ignored=""):
        import pisi.operations.build as build
        self.ctx.config.values = _Values(architecture, ignored)
        class Builder(build.Builder):
            # skip the real constructor: it needs a pspec.xml on disk
            def __init__(self):
                pass
        builder = Builder()
        builder.spec = _Spec([_Package("zlib"), _Package("zlib-32bit", "emul32"),
                              _Package("minizip", "minizip")])
        types = builder.get_build_types()
        return types, [p.name for p in builder.spec.packages]

    def testEmul32BuiltOnX86_64(self):
        types, packages = self.build_types("x86_64")
        self.assertEqual(types, ["", "emul32", "minizip"])
        self.assertEqual(packages, ["zlib", "zlib-32bit", "minizip"])

    def testEmul32SkippedOnAarch64(self):
        types, packages = self.build_types("aarch64")
        self.assertEqual(types, ["", "minizip"])
        self.assertEqual(packages, ["zlib", "minizip"])

    def testIgnoredBuildTypesStillHonoured(self):
        types, packages = self.build_types("x86_64", ignored="emul32")
        self.assertEqual(types, ["", "minizip"])
        self.assertEqual(packages, ["zlib", "minizip"])


if __name__ == "__main__":
    unittest.main()
