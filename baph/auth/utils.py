from hashlib import sha1
import random


# port from userena
def generate_sha1(string, salt=None):
    """
    Generates a sha1 hash for supplied string. Doesn't need to be very secure
    because it's not used for password checking. We got Django for that.

    :param string:
        The string that needs to be encrypted.

    :param salt:
        Optionally define your own salt. If none is supplied, will use a random
        string of 5 characters.

    :return: Tuple containing the salt and hash.

    """
    if not salt:
        salt = sha1(str(random.random())).hexdigest()[:5]
    hash = sha1(salt+str(string)).hexdigest()

    return (salt, hash)
