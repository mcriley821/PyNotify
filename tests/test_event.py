#!/usr/bin/env python
import unittest

import struct

from pathlib import Path

from pynotify import Event


def wd_to_path(wd: int):
    return Path.cwd()


class Test_Event(unittest.TestCase):
    def test_default_contruction(self):
        with self.assertRaises(TypeError):
            Event()

    def test_constructor(self):
        e = Event(watch_descriptor=0,
                  type=0,
                  is_directory=True,
                  unmounted=True,
                  cookie=0,
                  file_name="",
                  file_path="")
        self.assertIsInstance(e, Event)
        self.assertEqual(e.watch_descriptor, 0)
        self.assertEqual(e.type, 0)
        self.assertEqual(e.is_directory, True)
        self.assertEqual(e.unmounted, True)
        self.assertEqual(e.cookie, 0)
        self.assertEqual(e.file_name, "")
        self.assertEqual(e.file_path, "")
    
    def test_empty_buffer(self):
        with self.assertRaises(struct.error):
            Event.from_buffer(wd_to_path, b"", 0)

    def test_bad_index(self):
        with self.assertRaises(struct.error):
            Event.from_buffer(
                    wd_to_path, struct.pack("@iIII5s", 0, 0, 0, 5, b"test"), 1)

    def test_bad_buffer(self):
        with self.assertRaises(struct.error):
            Event.from_buffer(
                    wd_to_path, struct.pack("@iII5s", 0, 0, 5, b"test"), 0)

    def test_removes_nulls(self):
        buffer = struct.pack("@iIII255s", 0x77777777, 0xffffeeee,
                0xffffdddd, 255, b"test")
        self.assertEqual(buffer.count(b'\0'), 254)  # 3 extra from 255
        e, offset = Event.from_buffer(wd_to_path, buffer, 0)
        self.assertEqual(offset, 255 + 16)
        self.assertEqual(e.file_name, "test")


if __name__ == "__main__":
    unittest.main()

