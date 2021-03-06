# -*- coding: utf-8 -*-
# Copyright (c) 2014, Vispy Development Team.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

"""
Implements the global singleton app object.

"""

from __future__ import division

import os
import sys

from . import backends
from .backends import CORE_BACKENDS, BACKEND_NAMES, BACKENDMAP, TRIED_BACKENDS
from .. import config
from .base import BaseApplicationBackend as ApplicationBackend  # noqa
from ..util import logger


class Application(object):
    """Representation of the vispy application

    This wraps a native GUI application instance. Vispy has a default
    instance of this class that can be created/obtained via 
    `vispy.app.use_app()`.

    Parameters
    ----------
    backend_name : str | None
        The name of the backend application to use. If not specified,
        Vispy tries to select a backend automatically. See ``vispy.use()``
        for details.
    
    Notes
    -----
    Upon creating an Application object, a backend is selected, but the
    native backend application object is only created when `create()`
    is called or `native` is used. The Canvas and Timer do this
    automatically.
    
    """

    def __init__(self, backend_name=None):
        self._backend_module = None
        self._backend = None
        self._use(backend_name)
    
    def __repr__(self):
        name = self.backend_name
        if not name:
            return '<Vispy app with no backend>'
        else:
            return '<Vispy app, wrapping the %s GUI toolkit>' % name

    @property
    def backend_name(self):
        """ The name of the GUI backend that this app wraps.
        """
        if self._backend is not None:
            return self._backend._vispy_get_backend_name()
        else:
            return ''

    @property
    def backend_module(self):
        """ The module object that defines the backend.
        """
        return self._backend_module

    def process_events(self):
        """ Process all pending GUI events. If the mainloop is not
        running, this should be done regularly to keep the visualization
        interactive and to keep the event system going.
        """
        return self._backend._vispy_process_events()

    def create(self):
        """ Create the native application.
        """
        # Ensure that the native app exists
        self.native

    def run(self):
        """ Enter the native GUI event loop.
        """
        return self._backend._vispy_run()

    def quit(self):
        """ Quit the native GUI event loop.
        """
        return self._backend._vispy_quit()

    @property
    def native(self):
        """ The native GUI application instance.
        """
        return self._backend._vispy_get_native_app()

    def _use(self, backend_name=None):
        """Select a backend by name. See class docstring for details.
        """
        # See if we're in a specific testing mode
        test_name = os.getenv('_VISPY_TESTING_TYPE', None)
        if test_name not in BACKENDMAP:
            test_name = None

        # Check whether the given name is valid
        if backend_name is not None:
            if backend_name.lower() == 'default':
                backend_name = None  # Explicitly use default, avoid using test
            elif backend_name.lower() not in BACKENDMAP:
                raise ValueError('backend_name must be one of %s or None, not '
                                 '%r' % (BACKEND_NAMES, backend_name))
        elif test_name is not None:
            backend_name = test_name.lower()
            assert backend_name in BACKENDMAP

        # Should we try and load any backend, or just this specific one?
        try_others = backend_name is None

        # Get backends to try ...
        imported_toolkits = []  # Backends for which the native lib is imported
        backends_to_try = []
        if not try_others:
            # We should never hit this, since we check above
            assert backend_name.lower() in BACKENDMAP.keys()
            # Add it
            backends_to_try.append(backend_name.lower())
        else:
            # See if a backend is loaded
            for name, module_name, native_module_name in CORE_BACKENDS:
                if native_module_name and native_module_name in sys.modules:
                    imported_toolkits.append(name.lower())
                    backends_to_try.append(name.lower())
            # See if a default is given
            default_backend = config['default_backend'].lower()
            if default_backend.lower() in BACKENDMAP.keys():
                if default_backend not in backends_to_try:
                    backends_to_try.append(default_backend)
            # After this, try each one
            for name, module_name, native_module_name in CORE_BACKENDS:
                name = name.lower()
                if name not in backends_to_try:
                    backends_to_try.append(name)

        # Now try each one
        for key in backends_to_try:
            name, module_name, native_module_name = BACKENDMAP[key]
            TRIED_BACKENDS.append(name)
            mod_name = 'backends.' + module_name
            __import__(mod_name, globals(), level=1)
            mod = getattr(backends, module_name)
            if not mod.available:
                msg = ('Could not import backend "%s":\n%s'
                       % (name, str(mod.why_not)))
                if not try_others:
                    # Fail if user wanted to use a specific backend
                    raise RuntimeError(msg)
                elif key in imported_toolkits:
                    # Warn if were unable to use an already imported toolkit
                    msg = ('Although %s is already imported, the %s backend '
                           'could not\nbe used ("%s"). \nNote that running '
                           'multiple GUI toolkits simultaneously can cause '
                           'side effects.' % 
                           (native_module_name, name, str(mod.why_not))) 
                    logger.warning(msg)
                else:
                    # Inform otherwise
                    logger.info(msg)
            else:
                # Success!
                self._backend_module = mod
                logger.debug('Selected backend %s' % module_name)
                break
        else:
            raise RuntimeError('Could not import any of the backends.')

        # Store classes for app backend and canvas backend
        self._backend = self.backend_module.ApplicationBackend()
