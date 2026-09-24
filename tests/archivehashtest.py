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

"""Tests for source archive hashes: sha1sum, sha256sum or both."""

import hashlib
import os
import re
import shutil
import tempfile
import unittest

import pisi.specfile as specfile
import pisi.util as util

TEMPLATE = "repos/repo1/util/misc/spam/pspec.xml"
PAYLOAD = "pisi archive hash test\n"
SHA1 = hashlib.sha1(PAYLOAD).hexdigest()
SHA256 = hashlib.sha256(PAYLOAD).hexdigest()


def spec_with_hashes(attributes):
    """Write the template recipe with the given hash attributes on <Archive>."""
    text = open(TEMPLATE).read()
    text = re.sub(r'\s(sha1sum|sha256sum)="[^"]*"', "", text)
    text = text.replace("<Archive ", "<Archive %s " % attributes, 1)
    directory = tempfile.mkdtemp()
    path = os.path.join(directory, "pspec.xml")
    open(path, "w").write(text)
    return directory, path


class ArchiveHashTestCase(unittest.TestCase):

    def setUp(self):
        self.directories = []
        self.payload = tempfile.NamedTemporaryFile(delete=False)
        self.payload.write(PAYLOAD)
        self.payload.close()

    def tearDown(self):
        os.unlink(self.payload.name)
        for directory in self.directories:
            shutil.rmtree(directory)

    def read(self, attributes):
        directory, path = spec_with_hashes(attributes)
        self.directories.append(directory)
        spec = specfile.SpecFile()
        spec.read(path)
        return spec.source.archive[0]

    def testSha1Only(self):
        archive = self.read('sha1sum="%s"' % SHA1)
        self.assertEqual(archive.hashes(), [("sha1", SHA1)])

    def testSha256Only(self):
        archive = self.read('sha256sum="%s"' % SHA256)
        self.assertEqual(archive.hashes(), [("sha256", SHA256)])

    def testBothHashesAreChecked(self):
        archive = self.read('sha1sum="%s" sha256sum="%s"' % (SHA1, SHA256))
        self.assertEqual(archive.hashes(), [("sha256", SHA256), ("sha1", SHA1)])

    def testNoHashIsRejected(self):
        self.assertRaises(Exception, self.read, "")

    def testFileHashing(self):
        self.assertEqual(util.sha1_file(self.payload.name), SHA1)
        self.assertEqual(util.sha256_file(self.payload.name), SHA256)
        self.assertTrue(util.check_file_hash(self.payload.name, SHA1))
        self.assertTrue(util.check_file_hash(self.payload.name, SHA256, "sha256"))
        self.assertFalse(util.check_file_hash(self.payload.name, SHA1, "sha256"))

    def testSourceArchiveMatching(self):
        import pisi.sourcearchive as sourcearchive
        for attributes, expected in (
                ('sha256sum="%s"' % SHA256, True),
                ('sha1sum="%s" sha256sum="%s"' % (SHA1, SHA256), True),
                ('sha1sum="%s" sha256sum="%s"' % (SHA1, "0" * 64), False),
                ('sha1sum="%s"' % ("0" * 40), False)):
            class Source(sourcearchive.SourceArchive):
                # skip the real constructor: it prepares a download location
                def __init__(self):
                    pass
            source = Source()
            source.archive = self.read(attributes)
            source.archiveFile = self.payload.name
            self.assertEqual(source.hashes_match(), expected, attributes)


if __name__ == "__main__":
    unittest.main()
