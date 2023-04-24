from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
import getpass
import locale
import unicodedata

from django.core import exceptions
from django.core.management.base import CommandError
from django.db import DEFAULT_DB_ALIAS, router, connections
from django.utils.encoding import DEFAULT_LOCALE_ENCODING
#from django.utils import six
#from django.utils.six.moves import input
try:
    from django.utils.text import slugify
except:
    from django.template.defaultfilters import slugify
from sqlalchemy.ext.declarative import has_inherited_table

from baph.auth import models as auth_app #, get_user_model
from baph.db.models import get_models
from baph.db.orm import Base, ORM
#from baph.db import Session
#from baph.db.models import signals, get_models


orm = ORM.get()

def _get_permission_codename(action, opts, label=None):
    label = label if label else opts.model_name
    codename = '%s_%s' % (action, label)
    return slugify(codename.replace(' ','_'))
    
def _get_all_permissions(opts):
    """
    Returns (action, scope, codename, name) for all permissions in the given opts.
    """
    perms = []
    resources = opts.permission_resources
    handler = opts.permission_handler
    if handler or not resources:
        return perms
    fks = opts.model.get_fks()
    for resource in resources:
        for action in resources[resource]:
            for limiter, key, value, rel_key, base_class in fks:
                if (action,limiter) == ('add', 'single'):
                    # this permission makes no sense, skip it
                    continue

                if not key:
                    # this is a boolean permission, no key processing needed
                    pass
                elif key.find(',') == -1:
                    # permission uses a single key filter
                    key, limiter_ = opts.model.normalize_key(key)
                    limiter += limiter_
                elif key.find(',') > -1:
                    # multiple filters present, determine a common prefix
                    # and use it to format the limiter text
                    keys = key.split(',')
                    limiters = set()
                    keys_ = []
                    for k in keys:
                        k_, l_ = opts.model.normalize_key(k)
                        keys_.append(k_)
                        limiters.add(l_)
                    if len(limiters) != 1:
                        # we'll worry about this if it ever happens
                        assert False
                    
                    key = ','.join(keys)
                    limiter += limiters.pop()

                perm_name = 'Can %s %s %s' % (action, limiter, resource)
                perms.append({
                    'name': perm_name,
                    'codename': perm_name.lower().replace(' ','_')[4:],
                    'resource': resource,
                    'action': action,
                    'key': key,
                    'value': value,
                    })

    return perms
        
def create_permissions(app, created_models, verbosity, db=DEFAULT_DB_ALIAS,
                       **kwargs):
    pkg, _ = app.__name__.rsplit('.', 1)
    app_models = []
    for k, v in vars(app).items():
        if k not in orm.Base._decl_class_registry:
            continue
        if v not in list(orm.Base._decl_class_registry.values()):
            continue
        if pkg + '.models' != v.__module__:
            continue
        #if hasattr(app, '__package__') and app.__package__ + '.models' != v.__module__:
        #    continue
        app_models.append( (k,v) )
    if not app_models:
        return

    try:
        Permission = getattr(auth_app, 'Permission')
    except:
        return

    searched_perms = list()
    ctypes = set()
    searched_codenames = set()
    for k, klass in sorted(app_models, key=lambda x: x[0]):
        if klass.__mapper__.polymorphic_on is not None:
            if has_inherited_table(klass):
                # ignore polymorphic subclasses
                continue
        elif klass.__subclasses__():
            # ignore base if subclass is present
            continue
        if not klass._meta.permission_resources:
            # no resource types
            continue

        ctypes.update(klass._meta.permission_resources)
        for perm in _get_all_permissions(klass._meta):
            if perm['codename'] in searched_codenames:
                continue
            searched_perms.append(perm)
            searched_codenames.add(perm['codename'])

    if not ctypes:
        return
    #connection = connections[db]
    session = orm.sessionmaker()

    all_perms = session.query(Permission.codename) \
                       .filter(Permission.resource.in_(ctypes)) \
                       .all()
    all_perms = set([perm[0] for perm in all_perms])

    perms = [
        perm for perm in searched_perms
        if perm['codename'] not in all_perms
        ]

    session.execute(Permission.__table__.insert(), perms)
    session.flush()

    if verbosity >= 2:
        for perm in perms:
            print(("Adding permission '%s:%s'" % (perm['resource'],
                                                 perm['codename'])))

'''
def create_superuser(app, created_models, verbosity, db, **kwargs):
    from baph.auth.models import User as UserModel
    from django.core.management import call_command
    
    if UserModel in created_models and kwargs.get('interactive', True):
        msg = ("\nYou just installed Baph's auth system, which means you "
            "don't have any superusers defined.\nWould you like to create one "
            "now? (yes/no): ")
        confirm = input(msg)
        while 1:
            if confirm not in ('yes', 'no'):
                confirm = input('Please enter either "yes" or "no": ')
                continue
            if confirm == 'yes':
                call_command("createsuperuser", interactive=True, database=db)
            break

def get_system_username():
    """
    Try to determine the current system user's username.

    :returns: The username as a unicode string, or an empty string if the
        username could not be determined.
    """
    try:
        result = getpass.getuser()
    except (ImportError, KeyError):
        # KeyError will be raised by os.getpwuid() (called by getuser())
        # if there is no corresponding entry in the /etc/passwd file
        # (a very restricted chroot environment, for example).
        return ''
    try:
        result = result.decode(DEFAULT_LOCALE_ENCODING)
    except UnicodeDecodeError:
        # UnicodeDecodeError - preventive treatment for non-latin Windows.
        return ''
    return result

def get_default_username(check_db=True):
    """
    Try to determine the current system user's username to use as a default.

    :param check_db: If ``True``, requires that the username does not match an
        existing ``auth.User`` (otherwise returns an empty string).
    :returns: The username, or an empty string if no username can be
        determined.
    """
    default_username = get_system_username()
    try:
        default_username = unicodedata.normalize('NFKD', default_username)\
            .encode('ascii', 'ignore').decode('ascii').replace(' ', '').lower()
    except UnicodeDecodeError:
        return ''

    # Run the username validator
    # TODO: per-field validation
    #try:
    #    auth_app.User._meta.get_field('username').run_validators(default_username)
    #except exceptions.ValidationError:
    #    return ''

    # Don't return the default username if it is already taken.
    if check_db and default_username:
        session = orm.sessionmaker()
        user = session.query(auth_app.User).filter_by(username=default_username).first()
        if user:
            return ''

    return default_username

#signals.post_syncdb.connect(create_permissions,
#    dispatch_uid="django.contrib.auth.management.create_permissions")
#signals.post_syncdb.connect(create_superuser,
#    sender=auth_app, dispatch_uid="django.contrib.auth.management.create_superuser")
'''
