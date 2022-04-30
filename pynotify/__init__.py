#!/usr/bin/env python

#: An inotify watch descriptor. A simple type alias for :py:class:`int`
WatchDescriptor = int

from .event_type import EventType
from .event import Event
from .event_handler import EventHandler
from .notifier import Notifier

__all__ = ["Event", "EventType", "EventHandler", "Notifier", "WatchDescriptor"]
