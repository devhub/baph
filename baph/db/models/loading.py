import imp
import os
import sys

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.datastructures import SortedDict
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule
#from django.utils import six


class AppCache(object):

    __shared_state = dict(
        # Keys of app_store are the model modules for each application.
        app_store=SortedDict(),

        # Mapping of installed app_labels to model modules for that app.
        app_labels={},

        # Mapping of app_labels to a dictionary of model names to model code.
        # May contain apps that are not installed.
        app_models=SortedDict(),

        # Mapping of app_labels to errors raised when trying to import the app.
        app_errors={},

        # -- Everything below here is only used when populating the cache --
        loaded=False,
        handled={},
        postponed=[],
        nesting_level=0,
        _get_models_cache={},
    )

    def __init__(self):
        self.__dict__ = self.__shared_state

    def _label_for(self, app_mod):
        """
        Return app_label for given models module.

        """
        return app_mod.__name__.rsplit('.',1)[0]

    def _populate(self):
        """
        Fill in all the cache information. This method is threadsafe, in the
        sense that every caller will see the same state upon return, and if the
        cache is already initialised, it does no work.
        """
        if self.loaded:
            return
        # Note that we want to use the import lock here - the app loading is
        # in many cases initiated implicitly by importing, and thus it is
        # possible to end up in deadlock when one thread initiates loading
        # without holding the importer lock and another thread then tries to
        # import something which also launches the app loading. For details of
        # this situation see #18251.
        imp.acquire_lock()
        try:
            if self.loaded:
                return
            for app_name in settings.INSTALLED_APPS:
                if app_name in self.handled:
                    continue
                self.load_app(app_name, True)
            if not self.nesting_level:
                for app_name in self.postponed:
                    self.load_app(app_name)
                self.loaded = True
        finally:
            imp.release_lock()

    def extract_app_name(self, app_label):
        " determine the relevant entry in settings.INSTALLED_APPS "
        " which corresponds to this string-based module import "
        for app_name in sorted(settings.INSTALLED_APPS, key=lambda x: -1*len(x)):
            # we go from longest to shortest, so earlier matches are longer
            if len(app_name) > len(app_label):
                continue
            if app_label.startswith(app_name):
                return app_name
                
        # no result yet, try matching the short name
        short = app_label.split('.',1)[0]
        for app_name in settings.INSTALLED_APPS:
            if app_name.rsplit('.',1)[-1] == short:
                return short

        return None

    def app_cache_ready(self):
        """
        Returns true if the model cache is fully populated.

        Useful for code that wants to cache the results of get_models() for
        themselves once it is safe to do so.
        """
        return self.loaded

    def get_app(self, app_label, emptyOK=False):
        """
        Returns the module containing the models for the given app_label. If
        the app has no models in it and 'emptyOK' is True, returns None.
        """
        self._populate()
        imp.acquire_lock()
        try:
            app_name = extract_app_name(app_label)
            if app_name is None:
                raise ImproperlyConfigured('App with label %s could not be '
                    'found' % app_label)
            
            mod = self.load_app(app_name, False)
            if mod is None:
                if emptyOK:
                    return None
                raise ImproperlyConfigured('App with label %s is '
                    'missing a models.py module' % app_label)
            else:
                return mod
        finally:
            imp.release_lock()

    def get_apps(self):
        "Returns a list of all installed modules that contain models."
        self._populate()

        # Ensure the returned list is always in the same order (with new apps
        # added at the end). This avoids unstable ordering on the admin app
        # list page, for example.
        apps = [(v, k) for k, v in self.app_store.items()]
        apps.sort()
        return [elt[1] for elt in apps]


    def get_app_errors(self):
        "Returns the map of known problems with the INSTALLED_APPS."
        self._populate()
        return self.app_errors

    def load_app(self, app_name, can_postpone=False):
        """
        Loads the app with the provided fully qualified name, and returns the
        model module.
        """
        self.handled[app_name] = None
        self.nesting_level += 1
        app_module = import_module(app_name)
        try:
            models = import_module('.models', app_name)
        except ImportError:
            self.nesting_level -= 1
            # If the app doesn't have a models module, we can just ignore the
            # ImportError and return no models for it.
            if not module_has_submodule(app_module, 'models'):
                return None
            # But if the app does have a models module, we need to figure out
            # whether to suppress or propagate the error. If can_postpone is
            # True then it may be that the package is still being imported by
            # Python and the models module isn't available yet. So we add the
            # app to the postponed list and we'll try it again after all the
            # recursion has finished (in populate). If can_postpone is False
            # then it's time to raise the ImportError.
            else:
                if can_postpone:
                    self.postponed.append(app_name)
                    return None
                else:
                    raise

        self.nesting_level -= 1
        if models not in self.app_store:
            self.app_store[models] = len(self.app_store)
            self.app_labels[self._label_for(models)] = models
        return models

    def get_models(self, app_mod=None, include_auto_created=False,
                                       include_deferred=False):
        cache_key = (app_mod, include_auto_created, include_deferred)
        try:
            return self._get_models_cache[cache_key]
        except KeyError:
            pass
        self._populate()
        if app_mod:
            if app_mod in self.app_store:
                app_list = [self.app_models.get(self._label_for(app_mod),
                                                SortedDict())]
            else:
                app_list = []
        else:
            if only_installed:
                app_list = [self.app_models.get(app_label, SortedDict())
                            for app_label in six.iterkeys(self.app_labels)]
            else:
                app_list = six.itervalues(self.app_models)
        model_list = []
        for app in app_list:
            model_list.extend(
                model for model in app.values()
                if ((not model._meta.auto_created or include_auto_created) and
                    (not model._meta.swapped or include_swapped))
            )
        self._get_models_cache[cache_key] = model_list
        return model_list

    def get_model(self, app_label, model_name,
                  seed_cache=True, only_installed=True):
        """
        Returns the model matching the given app_label and case-insensitive
        model_name.

        Returns None if no model is found.
        """
        if seed_cache:
            self._populate()
        if only_installed and app_label not in self.app_labels:
            return None
        return self.app_models \
            .get(app_label, SortedDict()) \
            .get(model_name.lower())

    def register_models(self, app_label, *models):
        """
        Register a set of models as belonging to an app.
        """
        for model in models:
            # Store as 'name: model' pair in a dictionary
            # in the app_models dictionary
            model_name = model._meta.model_name
            model_dict = self.app_models.setdefault(app_label, SortedDict())
            if model_name in model_dict:
                # The same model may be imported via different paths (e.g.
                # appname.models and project.appname.models). We use the source
                # filename as a means to detect identity.
                fname1 = os.path.abspath(upath(
                    sys.modules[model.__module__].__file__))
                fname2 = os.path.abspath(upath(
                    sys.modules[model_dict[model_name].__module__].__file__))
                # Since the filename extension could be .py the first time and
                # .pyc or .pyo the second time, ignore the extension when
                # comparing.
                if os.path.splitext(fname1)[0] == os.path.splitext(fname2)[0]:
                    continue
            model_dict[model_name] = model
        self._get_models_cache.clear()

    def unregister_models(self, app_label, *models):
        for model in models:
            del self.app_models[app_label][model]



cache = AppCache()

get_apps = cache.get_apps
get_app = cache.get_app
get_app_errors = cache.get_app_errors
get_models = cache.get_models
get_model = cache.get_model
load_app = cache.load_app
app_cache_ready = cache.app_cache_ready
extract_app_name = cache.extract_app_name
register_models = cache.register_models
unregister_models = cache.unregister_models
