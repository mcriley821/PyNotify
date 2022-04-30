#!/usr/bin/env python
from __future__ import annotations
import asyncio
import ctypes
import errno
import os

from ctypes import c_int, c_uint, c_char_p
from ctypes.util import find_library

from fcntl import ioctl
from termios import FIONREAD
from signal import SIGINT

from pathlib import Path

from typing import AsyncIterable

from . import Event, EventType, EventHandler, WatchDescriptor


ONLYDIR     = 24  # shift for 0x0100_0000
DONT_FOLLOW = 25  # shift for 0x0200_0000
EXCL_UNLINK = 26  # shift for 0x0400_0000
ONESHOT     = 31  # shift for 0x8000_0000

MASK_ADD    = 29  # shift for 0x2000_0000


class TwoWayDict(dict):
    """Dict subclass to automatically add a value: key pair
       whenever a key: value pair is added.

       This is for convenience sake. Instead of tracking two
       dicts in the owning object, using this class requires
       only one.
    """
    def __setitem__(self, key, value):
        """Add the key: value pair and the value: key pair"""
        dict.__setitem__(self, key, value)
        dict.__setitem__(self, value, key)


def load_libc(path: Path | None = None) -> ctypes.CDLL:
    """Load libc and return a ctypes.CDLL.

       :param path: An optional path to libc.so

       :raises FileNotFoundError: When libc can't be found
    """
    if path is None:
        path = find_library("c")
    if path is None:
        raise FileNotFoundError("Could not find libc!")
    return ctypes.CDLL(path)


class Notifier:
    """Notifier
    """
    def __init__(self, 
                 async_loop: asyncio.AbstractEventLoop | None = None,
                 libc_path: Path | None = None):
        self._libc = load_libc(libc_path)
        self._define_inotify_functions()

        self._loop = async_loop if async_loop else asyncio.get_running_loop()
        self._wd_paths: TwoWayDict[WatchDescriptor, Path] = TwoWayDict()
        self._queue = asyncio.Queue()
        self._handlers: dict[WatchDescriptor, set[EventHandler]] = {}

        self._fd = self._inotify_init()
        self._loop.add_reader(self._fd, self._on_fd_ready_to_read) 

    def _define_inotify_functions(self):
        """Define inotify functions from libc as required by ctypes.
           Note that return values are error-checked by the
           _handle_inotify_return method."""
        self._libc.inotify_init.restype = self._handle_inotify_return
        self._libc.inotify_init.argtypes = tuple()

        self._libc.inotify_add_watch.restype = self._handle_inotify_return
        self._libc.inotify_add_watch.argtypes = (c_int, c_char_p, c_uint)

        self._libc.inotify_rm_watch.restype = self._handle_inotify_return
        self._libc.inotify_rm_watch.argtypes = (c_int, c_int)

    @staticmethod
    def _handle_inotify_return(value: int) -> int:
        """Handle the return from an inotify function. Each inotify function 
           will return -1 to indicate an error and set errno accordingly.
           Otherwise the return is valid."""
        if value == -1:
            err = ctypes.get_errno()
            raise RuntimeError(f"{errno.errorcode[err]}: {os.strerror(err)}")
        return value

    def _inotify_init(self) -> int:
        """Initializes a new inotify instance and returns a
           file descriptor associated with the new inotify event queue."""
        return self._libc.inotify_init()

    def _on_fd_ready_to_read(self):
        """Callback method when the asyncio loop determines that the
           inotify file descriptor is ready to read."""
        raw_data = self._read_from_fd()
        self._create_and_put_events(raw_data)

    def _read_from_fd(self) -> bytes:
        """Read and return all bytes available on the file descriptor.

           :return: raw :class:`bytes` from the file descriptor
        """
        available = c_int()
        try:
            ioctl(self._fd, FIONREAD, available)
        except OSError:  # happens if last watch is removed 
            return b""
        return os.read(self._fd, available.value)
    
    def _create_and_put_events(self, raw_data: bytes):
        """Deserialize Event objects from the raw data and put
           the Event on the queue.

           :param raw_data: The raw bytes to convert to Events_
        """
        offset = 0
        while offset != len(raw_data):
            event, offset = Event.from_buffer(
                    self.watch_descriptor_to_path, raw_data, offset)
            self._queue.put_nowait(event)
    
    def watch_descriptor_to_path(self,
            watch_descriptor: WatchDescriptor) -> Path:
        """Return the corresponding :class:`Path` of a WatchDescriptor_

           :param watch_descriptor: The WatchDescriptor_ to convert to a 
                                    :class:`Path`
        """
        return self._wd_paths[watch_descriptor]

    def add_watch(self,
                  file_path: Path,
                  *handlers: EventHandler,
                  only_event_types: EventType = EventType.ALL,
                  follow_symlinks: bool = True,
                  if_directory_only: bool = False,
                  oneshot: bool = False,
                  exclude_unlinks: bool = True):
        """Add a watch to the specified *file_path*.

           :param file_path: :class:`Path` to watch
           :param handlers: Any number of EventHandlers_ to handle
                             Events_ from the created watch

           :param only_event_types: Generate an Event_ only for the 
                                    specified EventTypes_

           :param follow_symlinks: If :data:`True`, watch even if *file_path*
                                   is a symlink

           :param if_directory_only: If :data:`True`, watch only if *file_path*
                                     is a directory

           :param oneshot: If :data:`True`, delete the watch on *file_path*
                           after the first Event_ is generated

           :param exclude_unlinks: Stop watching children when unlinked from
                                   a watch directory. See the man_ for
                                   more details.

           :raises FileNotFoundError: If *file_path* does not exist
           :raises ValueError: If a watch already exists for *file_path*
           :raises OSError: If *follow_symlinks* is :data:`False` and 
                            *file_path* is a symlink
           :raises OSError: If *if_directory_only* is :data:`True` and 
                            *file_path* is not a directory
        """
        file_path = file_path.expanduser()
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot find file: {file_path}")
        if file_path in self._wd_paths:
            raise ValueError(f"File '{file_path}' already has a watch!")

        bytes_path = str(file_path).encode()

        mask = (   only_event_types 
                | (follow_symlinks << DONT_FOLLOW)
                | (if_directory_only << ONLYDIR)
                | (exclude_unlinks << EXCL_UNLINK)
                | (oneshot << ONESHOT) )

        wd = self._libc.inotify_add_watch(self._fd, bytes_path, mask)
        self._wd_paths[wd] = file_path
        self._handlers[wd] = set(handlers)

    def modify_watch_event_types(self,
                                 descriptor: Path | WatchDescriptor,
                                 new_types: EventType,
                                 merge: bool = False):
        """Modify the possible Events_ that can be generated for
           the watch at *descriptor* by modifying the EventTypes_ for 
           said watch.

           :param descriptor: A :class:`Path` or WatchDescriptor_ to change
                              the EventTypes_ for

           :param new_types: EventTypes_ of Events_ to generate
           :param merge: If :data:`True` merge *new_types* with the existing
                         EventTypes_ for the watch

           :raises ValueError: If there is no watch on *descriptor*

        """
        if isinstance(descriptor, Path):
            descriptor = descriptor.expanduser()

        if not descriptor in self._wd_paths:
            raise ValueError(f"No watch on descriptor '{descriptor}'!")
        
        if isinstance(descriptor, Path):
            file_path = descriptor
        else:
            file_path = self._wd_paths[descriptor]
        bytes_path = str(file_path).encode()

        # inotify_add_watch also modifies existing watch masks
        mask = new_types | (merge << MASK_ADD)
        _ = self._libc.inotify_add_watch(self._fd, bytes_path, mask)

    def remove_watch(self, 
                     descriptor: Path | WatchDescriptor,
                     raises: bool = True):
        """Remove a watch on the *descriptor*
        
           :param descriptor: A :class:`Path` or WatchDescriptor_ to remove
           :param raises: If :data:`True`, raise a :class:`ValueError` if
                          the *descriptor* does not have a watch

           :raises ValueError: If *raises* and there is no watch on *descriptor*
        """
        if isinstance(descriptor, Path):
            descriptor = descriptor.expanduser()
        if descriptor not in self._wd_paths:
            if raises:
                raise ValueError(f"No watch on descriptor '{descriptor}'!")
            return
        
        wd = self._wd_paths.pop(descriptor)
        del self._wd_paths[wd]

        if isinstance(wd, Path):
            wd = descriptor

        self._libc.inotify_rm_watch(self._fd, wd)

    def add_handlers(self,
                     descriptor: Path | WatchDescriptor,
                     *handlers: EventHandler):
        """Add the EventHandlers_ *handlers* to the watch on *descriptor*

           .. note:: Skips a handler if it is already on the *descriptor*

           :param descriptor: A :class:`Path` or WatchDescriptor_ to add
                              *handlers* to
           :param handlers: New EventHandlers_ to add to *descriptor*
        """
        if isinstance(descriptor, Path):
            descriptor = self._wd_paths[descriptor]
        self._handlers[descriptor] |= set(handlers)

    def clear_handlers(self, descriptor: Path | WatchDescriptor):
        """Clear all EventHandlers_ for the watch on *descriptor*

           :param descriptor: A :class:`Path` or WatchDescriptor_ to
                              clear EventHandlers_ from

           :raises ValueError: If there is no watch on *descriptor*
        """
        if descriptor not in self._wd_paths:
            raise ValueError(f"No watch on descriptor '{descriptor}'!")
        if isinstance(descriptor, Path):
            descriptor = self._wd_paths[descriptor]
        self._handlers[descriptor].clear()

    def remove_handlers(self,
                        descriptor: Path | WatchDescriptor,
                        *handlers: EventHandler):
        """Remove the EventHandlers_ *handlers* from the watch on *descriptor*

           :param descriptor: A :class:`Path` or WatchDescriptor_ to remove
                              EventHandlers_ from
           :param handlers: EventHandlers_ to remove from *descriptor*

           :raises ValueError: If there is no watch on *descriptor*
        """
        if descriptor not in self._wd_paths:
            raise ValueError("No watch on descriptor '{descriptor}'!")
        if isinstance(descriptor, Path):
            descriptor = self._wd_paths[descriptor]
        self._handlers[descriptor] -= set(handlers)

    async def run(self, 
                  stop_event: asyncio.Event | None = None,
                  handle_once: bool = False,
                  warn_unhandled: bool = True):
        """Asynchronously generate Events_ until *stop_event* is set.
           When an Event_ is generated, the :func:`EventHandler.handle_event`
           method for each EventHandler_ for the watch, from
           :func:`Notifier.add_watch`, is called with the generated Event_.

           :param stop_event: :class:`asyncio.Event` to stop generating
                              Events_ when set.
           :param handle_once: If :data:`True` the generated Event_ is
                               discarded after it is handled by the first
                               capable EventHandler_.
           :param warn_unhandled: Emit a warning via :func:`warnings.warn`
                                  if an Event_ is not handled.
        """
        while stop_event is None or not stop_event.is_set():
            event = await self._queue.get()
            handled = False
            for handler in self._handlers[event.watch_descriptor]:
                if not handler.can_handle_event_type(event.type):
                    continue
                handler.handle_event(event)
                handled = True
                if handle_once:
                    break
            if warn_unhandled and not handled:
                warnings.warn("Unhandled Event! {event}", RuntimeWarning)

    def close(self):
        """Close the inotify fd"""
        os.close(self._fd)

    def __enter__(self):
        """Nothing special on entry"""
        return self

    def __exit__(self, *exception):
        """Close the inotify fd when exiting"""
        self.close()

