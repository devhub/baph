from baph.db.models import signals, get_apps
from baph.db.orm import ORM, Base


def emit_post_sync_signal(created_models, verbosity, interactive, db):
    # Emit the post_sync signal for every application.
    for app in get_apps():
        app_name = app.__name__.rsplit('.',1)[0]
        if verbosity >= 2:
            print("Running post-sync handlers for application %s" % app_name)
        signals.post_syncdb.send(sender=app, app=app,
            created_models=created_models, verbosity=verbosity,
            interactive=interactive, db=db)
