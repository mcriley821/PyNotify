#!/usr/bin/env python
import docutils.nodes as nodes

"""
This script is taken from a Stack Overflow solution for an issue
where Sphinx does not create hyperlinks for type hints that are
also type aliases.

https://stackoverflow.com/questions/61719978/how-to-link-typing-like-nested-classes-and-other-urls-with-sphinx-and-rst

"""

_cache = {}

def fill_cache(app):
    if app.config.reflinks:
        _cache.update(app.config.reflinks)

def missing_reference(app, env, node, contnode):
    target = node['reftarget']
    uri = _cache.get(target, None)
    if uri is None:
        return
    newnode = nodes.reference('', '', internal=False, refuri=uri)
    if not node.get('refexplicit'):
        if target in app.config.reflinks_should_replace:
            target = app.config.reflinks_should_replace[target]
        if target in app.config.reflinks_should_trim:
            target = target[target.rindex('.') + 1:]
        name = target.replace('_', ' ')
        contnode = contnode.__class__(name, name)
    newnode.append(contnode)
    return newnode

def setup(app):
    app.add_config_value('reflinks', {}, "html", [dict])
    app.add_config_value("reflinks_should_trim", set(), "html", [set])
    app.add_config_value("reflinks_should_replace", {}, "html", [dict])
    app.connect('builder-inited', fill_cache)
    app.connect('missing-reference', missing_reference, priority = 1000)

