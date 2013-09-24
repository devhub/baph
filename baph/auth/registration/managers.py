from datetime import datetime
import re

from sqlalchemy.orm import joinedload

from baph.auth.models import User, Organization
from baph.auth.registration import settings as auth_settings
from baph.auth.registration.models import UserRegistration
from baph.auth.utils import generate_sha1
from baph.db.orm import ORM


orm = ORM.get()

SHA1_RE = re.compile('^[a-f0-9]{40}$')

class SignupManager(object):

    @staticmethod
    def create_user(username, email, password, active=False, send_email=True,
                     **kwargs):
        uname = username.encode('utf-8') if isinstance(username, unicode) else username
        salt, activation_key = generate_sha1(uname)

        #org_key = Organization._meta.verbose_name
        #org = Organization.get_current()
        #print 'create user:', username, email, password, kwargs
        new_user = User.create_user(username, email, password, **kwargs)
        new_user.is_active = active
        new_user.signup = UserRegistration(activation_key=activation_key)

        session = orm.sessionmaker()
        session.add(new_user)
        session.commit()

        if auth_settings.BAPH_ACTIVATION_REQUIRED:
            new_user.signup.send_activation_email()
        
        return new_user

    @staticmethod
    def check_expired_activation(activation_key):
        """
        Check if ``activation_key`` is still valid.

        Raises a ValueError exception if activation_key is invalid

        Raises a ``sqlalchemy.orm.exc.NoResultFound`` exception if key is not
            present

        :param activation_key:
            String containing the secret SHA1 for a valid activation.

        :return:
            True if the ket has expired, False if still valid.

        """
        if not SHA1_RE.search(activation_key):
            raise ValueError('Invalid activation key')
        session = orm.sessionmaker()
        signup = session.query(UserRegistration) \
            .filter_by(activation_key=activation_key) \
            .one()
        return signup.activation_key_expired()

    @staticmethod
    def activate_user(activation_key):
        """
        Activate an :class:`User` by supplying a valid ``activation_key``.

        If the key is valid and an user is found, activates the user and
        return it. Also sends the ``activation_complete`` signal.

        :param activation_key:
            String containing the secret SHA1 for a valid activation.

        :return:
            The newly activated :class:`User` or ``False`` if not successful.

        """
        if SHA1_RE.search(activation_key):
            session = orm.sessionmaker()
            info = session.query(UserRegistration) \
                .filter_by(activation_key=activation_key) \
                .first()
            if not info:
                return False
            if not info.activation_key_expired():
                info.activation_key = auth_settings.BAPH_ACTIVATED
                user = info.user
                user.is_active = True
                user.save()

                # Send the activation_complete signal
                #userena_signals.activation_complete.send(sender=None,
                #                                         user=user)
                return user
        return False

    @staticmethod
    def reissue_activation(activation_key):
        """
        Creates a new ``activation_key`` resetting activation timeframe when
        users let the previous key expire.

        :param activation_key:
            String containing the secret SHA1 activation key.

        """
        session = orm.sessionmaker()
        signup = session.query(UserRegistration) \
            .options(joinedload('user')) \
            .filter_by(activation_key=activation_key) \
            .first()
        if not signup:
            return False
        try:
            salt, new_activation_key = generate_sha1(signup.user.username)
            signup.activation_key = new_activation_key
            signup.user.date_joined = datetime.now()
            session.commit()
            signup.send_activation_email()
            return True
        except Exception as e:
            raise
            return False

    @staticmethod
    def confirm_email(confirmation_key):
        """
        Confirm an email address by checking a ``confirmation_key``.

        A valid ``confirmation_key`` will set the newly wanted e-mail
        address as the current e-mail address. Returns the user after
        success or ``False`` when the confirmation key is
        invalid. Also sends the ``confirmation_complete`` signal.

        :param confirmation_key:
            String containing the secret SHA1 that is used for verification.

        :return:
            The verified :class:`User` or ``False`` if not successful.

        """
        if SHA1_RE.search(confirmation_key):
            session = orm.sessionmaker()
            signup = session.query(UserRegistration) \
                .options(joinedload('user')) \
                .filter(UserRegistration.email_confirmation_key==confirmation_key) \
                .filter(UserRegistration.email_unconfirmed != None) \
                .first()
            if not signup:
                return False
            user = signup.user
            old_email = user.email
            user.email = signup.email_unconfirmed
            signup.email_unconfirmed, signup.email_confirmation_key = '',''
            session.commit()

            # Send the confirmation_complete signal
            # TODO: implement signals
            #userena_signals.confirmation_complete.send(sender=None,
            #                                           user=user,
            #                                           old_email=old_email)

            return user
        return False

    @staticmethod
    def delete_expired_users():
        """
        Checks for expired users and delete's the ``User`` associated with
        it. Skips if the user ``is_staff``.

        :return: A list containing the deleted users.

        """
        deleted_users = []
        session = orm.sessionmaker()
        users = session.query(User) \
            .filter(User.is_staff==False) \
            .filter(User.is_active==False) \
            .all()
        for user in users:
            if user.signup.activation_key_expired():
                deleted_users.append(user)
                user.delete()
        return deleted_users

    @staticmethod
    def get(pk=None, **kwargs):
        session = orm.sessionmaker()
        if pk:
            obj = session.query(UserRegistration).get(pk)
        else:
            obj = session.query(UserRegistration).filter_by(**kwargs).first()
        return obj

UserRegistration.objects = SignupManager
