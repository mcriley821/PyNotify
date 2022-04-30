# Configuration file for the Sphinx documentation builder.

# -- Environment setup ------------------------------------------------------

# Patch TypeAliasForwardRef for nested type aliases
from sphinx.util import inspect
inspect.TypeAliasForwardRef.__repr__ = lambda self: self.name
inspect.TypeAliasForwardRef.__hash__ = lambda self: hash(self.name)

# Add lookup for custom extensions
import sys
import os

sys.path.append(os.path.abspath("./_ext"))

# -- Project information -----------------------------------------------------

project = 'PyNotify'
copyright = '2022, Matt Riley'
author = 'Matt Riley'
release = '0.1'

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "autodoc_intflag",
    "reflinks"
]

templates_path = ['_templates']

exclude_patterns = [
    "*/__pycache__/*",
    "tests",
    "docs"
]

python_use_unqualified_type_names = True

# -- Autodoc configuration ---------------------------------------------------

autodoc_default_options = {
    "members":  True,
    "member-order": "bysource"
}

autodoc_type_aliases = {
    "WatchDescriptor": "~pynotify.WatchDescriptor"
}

autodoc_typehints_format = "short"

autodoc_preserve_defaults = True

# -- Intersphinx configuration ----------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- Reflinks configuration ------------------------------------------------------

reflinks = {
    "WatchDescriptor": "#pynotify.WatchDescriptor",
    "pynotify.WatchDescriptor": "#pynotify.WatchDescriptor",
    "asyncio.events.AbstractEventLoop": 
        "https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.AbstractEventLoop",
    "Path": "https://docs.python.org/3/library/pathlib.html#pathlib.Path",
    "asyncio.locks.Event": "https://docs.python.org/3/library/asyncio-sync.html#asyncio.Event",
}

reflinks_should_trim = {
    "pynotify.WatchDescriptor",
    "asyncio.events.AbstractEventLoop"
}

reflinks_should_replace = {
    "asyncio.locks.Event": "asyncio.Event",
}

# -- Options for HTML output -------------------------------------------------

html_use_index = False
html_domain_indices = False

html_theme = "bizstyle"

html_theme_options = {
    "nosidebar": True,
}

html_static_path = ['_static']

html_css_files = [
    "css/newline_params.css",
    "css/class_sep.css"
]

