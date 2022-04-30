#!/usr/bin/env python
from enum import IntFlag


class EventType(IntFlag):
    """EventTypes_ map to different filesystem events.
       
       In the man_ page, event types are listings under the
       *inotify events* section. (They also correspond in name.)
    """

    ACCESS        = 0x001  #: File was accessed
    MODIFY        = 0x002  #: File was modified
    ATTRIB        = 0x004  #: File attribute metadata changed
    CLOSE_WRITE   = 0x008  #: File opened for writing was closed
    CLOSE_NOWRITE = 0x010  #: File opened for reading only was closed
    OPEN          = 0x020  #: File was opened
    MOVED_FROM    = 0x040  #: A file was moved from the watch directory
    MOVED_TO      = 0x080  #: A file was moved to the watch directory
    CREATE        = 0x100  #: File was created
    DELETE        = 0x200  #: File was deleted
    DELETE_SELF   = 0x400  #: File was deleted
    MOVE_SELF     = 0x800  #: File was moved

    #: File was closed: (:py:attr:`CLOSE_WRITE` | :py:attr:`CLOSE_NOWRITE`)
    CLOSE         = CLOSE_WRITE | CLOSE_NOWRITE 

    #: File was moved: (:py:attr:`MOVED_FROM` | :py:attr:`MOVED_TO`)
    MOVED         = MOVED_FROM | MOVED_TO

    #: Convenience EventType_ for all above EventTypes_
    ALL           = 0xfff  # combined value for brevity

