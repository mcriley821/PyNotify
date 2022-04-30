#!/usr/bin/env python
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from pathlib import Path
import struct

from . import EventType, WatchDescriptor

ISDIR     = 0x4000_0000
UNMOUNTED = 0x0000_2000

@dataclass(frozen=True)
class Event:
    """Events_ port an inotify_event struct into a Python class,
       with some additional attributes.

       :note: An Event_ is a frozen :py:func:`~dataclasses.dataclass`
       :raises dataclasses.FrozenInstanceError: 
            Upon attempted attribute change
    """

    #: Corresponding inotify watch descriptor of this Event_
    watch_descriptor: WatchDescriptor

    type: EventType        #: EventType_ of this Event_
    is_directory: bool     #: :data:`True` if the watched file is a directory
    unmounted: bool        #: :data:`True` if the watched file was unmounted
    cookie: int            #: Corresponding inotify cookie
    file_name: str         #: File name that caused this Event_

    #: :class:`~pathlib.Path` to the file that caused this Event_
    file_path: Path       

    @staticmethod
    def from_buffer(
            wd_to_path: Callable[ [WatchDescriptor], Path],
            buffer: bytes, 
            offset: int = 0) -> tuple[Event, int]:
        """Starting at *offset*, unpack *buffer* to create 
           an Event_ object.

           :param wd_to_path: A callable to convert a :data:`WatchDescriptor`
                              into a :class:`~pathlib.Path`
           :param buffer: The buffer to unpack from
           :param offset: An offset into *buffer* to begin unpacking

           :return: :class:`tuple` of the new Event_ and new *offset*
        """
        # Unpack raw inotify_event struct
        wd, mask, cookie, _len = struct.unpack_from("@iIII", buffer, offset)
        offset += struct.calcsize("@iIII")
        file_name, = struct.unpack_from(f"@{_len}s", buffer, offset)
        offset += struct.calcsize(f"@{_len}s")
        
        # Process into Event attributes        
        file_name = file_name.strip(b'\0').decode()
        file_path = wd_to_path(wd) / file_name
        type = EventType(mask & EventType.ALL)

        is_dir = (mask & ISDIR) != 0
        unmounted = (mask & UNMOUNTED) != 0
        
        # Create and return
        event = Event(watch_descriptor=wd, type=type,
                      is_directory=is_dir, unmounted=unmounted,
                      cookie=cookie, file_name=file_name, file_path=file_path)

        return event, offset

