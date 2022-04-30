.. PyNotify documentation master file, created by
   sphinx-quickstart on Sat Apr 23 16:14:32 2022.

PyNotify Documentation
======================
.. _man: https://man7.org/linux/man-pages/man7/inotify.7.html
.. _README: https://github.com/mcriley821/PyNotify.git
       
.. _WatchDescriptor: #pynotify.WatchDescriptor
.. _Event: #pynotify.Event
.. _Events: #pynotify.Event
.. _EventType: #pynotify.EventType
.. _EventTypes: #pynotify.EventType
.. _EventHandler: #pynotify.EventHandler
.. _EventHandlers: #pynotify.EventHandler
.. _Notifier: #pynotify.Notifier

PyNotify is a Python interface to the Linux inotify API.
See the man_ pages for more details on the inotify API, and
see more details about this project and usage examples in the README_

.. autodata:: pynotify.WatchDescriptor

.. autoclass:: pynotify.Event

.. autointflag:: pynotify.EventType
   :hex:
   :fill: 3

.. autoclass:: pynotify.EventHandler
   :show-inheritance:

.. autoclass:: pynotify.Notifier

