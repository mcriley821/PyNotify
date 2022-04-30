#!/usr/bin/env python
import unittest
from unittest.mock import patch
import asyncio
import struct
import pathlib
from pynotify import Notifier, Event, EventType


class TestHandler:
    def __init__(self):
        self.handled_events = []

    def handle_event(self, event: Event):
        self.handled_events.append(event)

    def can_handle_event_type(self, event_type: EventType) -> bool:
        return event_type & EventType.ALL != 0


def wd_to_path(wd: int):
    return pathlib.Path.cwd()


class Test_Notifier_ctors(unittest.IsolatedAsyncioTestCase):
    async def test_default_ctor(self):
        n = Notifier()
        n.close()
        self.assertIs(type(n), Notifier)

    async def test_with_ctor(self):
        with Notifier() as n:
            ...

    async def test_custom_async_loop(self):
        n = Notifier(async_loop=asyncio.get_running_loop())
        n.close()

    async def test_no_libc(self):
        with patch("pynotify.notifier.find_library", return_value=None):
            with self.assertRaises(FileNotFoundError):
                Notifier()

    async def test_bad_libc(self):
        with self.assertRaises(OSError):
            Notifier(libc_path="it/would/never/be/here/normally/libc.so")


class Test_Notifier(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.notifier = Notifier()
        self.cwd = pathlib.Path.cwd()

    async def asyncTearDown(self):
        self.notifier.close()

    def test_define_inotify_functions(self):
        self.notifier._define_inotify_functions()
    
    @patch("pynotify.notifier.ctypes.get_errno")
    def test_handle_inotify_return_throws(self, get_errno):
        get_errno.return_value = 3
        with self.assertRaises(RuntimeError):
            self.notifier._handle_inotify_return(-1)

    def test_handle_inotify_return_valid(self):
        for i in range(10):
            with self.subTest(i=i):
                self.assertEqual(i, self.notifier._handle_inotify_return(i))
    
    @patch("pynotify.notifier.Notifier._read_from_fd")
    def test_no_data_ready_on_fd(self, mocked_method):
        mocked_method.return_value = b""
        self.notifier._on_fd_ready_to_read()

        with self.assertRaises(asyncio.QueueEmpty):
            self.notifier._queue.get_nowait()

    def test_add_watch(self):
        self.notifier.add_watch(self.cwd)

    def test_add_watch_bad_file_path(self):
        p = pathlib.Path("/this/could/never/be/real")

        with self.assertRaises(FileNotFoundError):
            self.notifier.add_watch(p)

    def test_add_watch_duplicate(self):
        self.notifier.add_watch(self.cwd)
        with self.assertRaises(ValueError):
            self.notifier.add_watch(self.cwd)

    def test_modify_watch_mask(self):
        self.notifier.add_watch(self.cwd)
        self.notifier.modify_watch_event_types(self.cwd, EventType.MOVED)
    
    @patch("pynotify.notifier.ioctl")
    def test_remove_watch(self, mocked_method):
        mocked_method.return_value = 0
        self.notifier.add_watch(self.cwd)
        self.notifier.remove_watch(self.cwd)

    def test_remove_watch_raises(self):
        with self.assertRaises(ValueError):
            self.notifier.remove_watch(self.cwd)

    def test_remove_watch_not_raises(self):
        self.notifier.remove_watch(self.cwd, raises=False)

    def test_add_handlers(self): 
        handler = TestHandler()
        self.notifier.add_watch(self.cwd)
        self.notifier.add_handlers(self.cwd, handler)

    def test_duplicate_handler(self):
        handler = TestHandler()
        self.notifier.add_watch(self.cwd)
        self.notifier.add_handlers(self.cwd, handler)
        self.notifier.add_handlers(self.cwd, handler)

    def test_remove_handler(self):
        handler = TestHandler()
        self.notifier.add_watch(self.cwd)
        self.notifier.add_handlers(self.cwd, handler)
        self.notifier.remove_handlers(self.cwd, handler)

    async def test_run(self):
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(self.notifier.run(), timeout=0.5)

    async def test_handle_forever_stop(self):
        stop_event = asyncio.Event()

        async def set_stop():
            await asyncio.sleep(0.5)
            stop_event.set()

        async def run():
            await self.notifier.run(stop_event)

        await asyncio.wait(
                (asyncio.create_task(run()),
                 asyncio.create_task(set_stop())),
                timeout=1)
        

if __name__ == "__main__":
    unittest.main(buffer=True)

