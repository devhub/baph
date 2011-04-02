# -*- coding: utf-8 -*-
'''\
:mod:`baph.utils.s3` -- Amazon S3 Utilities
===========================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>

Available Settings
------------------

.. setting:: AWS_ACCESS_KEY_ID

``AWS_ACCESS_KEY_ID``
    The "public key" for Amazon Web Services authentication.

.. setting:: AWS_SECRET_ACCESS_KEY

``AWS_SECRET_ACCESS_KEY``
    The "private key" for Amazon Web Services authentication.

.. setting:: AWS_STORAGE_BUCKET_NAME

``AWS_STORAGE_BUCKET_NAME``

The name of the default bucket where files are loaded/saved.

Classes
-------
'''

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from cStringIO import StringIO
from django.conf import settings
from PIL import Image

# Amazon S3 connection
connection = S3Connection(settings.AWS_ACCESS_KEY_ID,
                          settings.AWS_SECRET_ACCESS_KEY)


class Bucket(object):
    '''Handles the uploading of files to an S3 bucket.

    :param str bucket: The name of the S3 bucket.
    '''

    def __init__(self, bucket=None):
        self.bucket_name = bucket or settings.AWS_STORAGE_BUCKET_NAME
        self.bucket = connection.create_bucket(bucket)

    def __contains__(self, key):
        '''Tests whether a key is in the bucket.'''
        return self.bucket.get_key(key) is not None

    def __getitem__(self, key):
        if not isinstance(key, basestring):
            raise TypeError('key is not a string')
        item = self.bucket.get_key(key)
        if not item:
            raise KeyError('key "%s" does not exist in the bucket' % key)
        try:
            item.open_read()
            return item.read()
        finally:
            item.close()

    def __delitem__(self, key):
        if not isinstance(key, basestring):
            raise TypeError('key is not a string')
        item = self.bucket.get_key(key)
        if not item:
            raise KeyError('key "%s" does not exist in the bucket' % key)
        item.delete()

    def upload(self, data, key, content_type, headers=None, public=True):
        '''Uploads a file to S3 as the given key.

        :param data: the file data
        :type data: a file-like object or a :class:`str`
        :param str key: the name associated with the file (usually looks like a
                        path).
        :param str content_type: The MIME type of the data.
        :param headers: Any extra headers associated with the file that will be
                        sent any time the file is accessed.
        :type headers: :class:`dict` or :const:`None`
        :returns: the protocol-agnostic URL of the new file on S3.
        :rtype: :class:`str`
        '''
        if not headers:
            headers = {}
        headers.update({
            'Content-Type': content_type,
        })
        key = Key(self.bucket, key)
        if hasattr(data, 'read'):
            key.set_contents_from_file(data, headers=headers)
        else:
            key.set_contents_from_string(data, headers=headers)
        if public:
            key.set_acl('public-read')
        return '//%s.s3.amazonaws.com/%s' % (self.bucket_name, key.name)


class ImageBucket(Bucket):
    '''Handles the uploading of images to an S3 bucket.

    :param str bucket: The name of the S3 bucket.
    :param str img_type: The image file type that is being uploaded. Value
                         must be one of ``png``, ``jpg``, or :const:`None` (to
                         autodetect)
    :param dict save_options: Options used when saving the thumbnails. They are
                              generally image type-specific.
    '''

    __mime_types = {
        'jpg': 'image/jpeg',
        'png': 'image/png'}
    __pil_types = {
        'jpg': 'jpeg',
        'png': 'png'}

    SCALE_NONE = 0
    SCALE_HEIGHT = 1
    SCALE_WIDTH = 2
    SCALE_BOTH = 3

    def __init__(self, bucket=None, img_type=None, save_options={}):
        super(ImageBucket, self).__init__(bucket)
        self.img_type = img_type
        self.save_options = save_options

    def upload(self, image, basename):
        '''Uploads an image to S3 with the given basename.

        :param image: the image data, conforming to the image type
        :type image: a file-like object
        :param str basename: the base filename of the uploaded image (sans
                             extension).
        :returns: the URL of the image on S3.
        :rtype: :class:`str`
        '''
        image.seek(0)
        if self.img_type is None:
            img = Image.open(image)
            format = img.format.lower()
            types = [k for k, v in self.__pil_types.iteritems() if v == format]
            if len(types) > 0:
                img_type = types[0]
            else:
                raise ValueError(u'Unknown image type.')
            image.seek(0)
        else:
            img_type = self.img_type
        key = '%s.%s' % (basename, img_type)
        return super(ImageBucket, self).upload(image, key,
                                               self.__mime_types[img_type])

    def upload_with_thumbnails(self, image, basename, sizes, scale_type,
                               upload_original=True, original_basename=None):
        '''Uploads an image its thumbnails to S3.

        :param image: the image data, conforming to the image type
        :type image: a file-like object
        :param str basename: the base filename of the uploaded image (sans
                             extension).
        :param list sizes: The sizes of the thumbnails (contents dependent
                           upon scale_type)
        :param int scale_type: If ``SCALE_NONE``, ``sizes`` needs to be a list
                               of 2-tuples. If ``SCALE_HEIGHT`` or
                               ``SCALE_WIDTH``, ``sizes`` needs to be a
                               :class:`list` of :class:`int` sizes.
                               ``SCALE_HEIGHT`` means that the sizes are the
                               widths, and the height is automatically
                               generated via the original image ratio.
                               ``SCALE_WIDTH`` is the same, but reversed. If
                               ``SCALE_BOTH``, ``sizes`` is a :class:`list` of
                               percentages by which to scale the image.
        :param bool upload_original: If :const:`True`, uploads the original
                                     image as well.
        '''
        original_url = None
        if upload_original:
            if original_basename is None:
                raise ValueError('The original_basename parameter needs ' + \
                                 'to be specified.')
            original_url = self.upload(image, original_basename)
            image.seek(0)
        img = Image.open(image)
        for size in sizes:
            thumb = img.copy()
            width, height = img.size
            if scale_type == self.SCALE_NONE:
                t_width, t_height = size
                str_size = '%sx%s' % size
            elif scale_type == self.SCALE_HEIGHT:
                t_width = size
                t_height = height * t_width / width
                str_size = str(size)
            elif scale_type == self.SCALE_WIDTH:
                t_height = size
                t_width = width * t_height / height
                str_size = str(size)
            elif scale_type == self.SCALE_BOTH:
                t_width = int((size / 100.0) * width)
                t_height = int((size / 100.0) * height)
                str_size = str(size)
            thumb.thumbnail((t_width, t_height), Image.ANTIALIAS)
            fp = StringIO()
            thumb.save(fp, self.__pil_types[self.img_type],
                       **self.save_options)
            if '%s' in basename:
                t_basename = basename % str_size
            self.upload(fp, t_basename)
        return original_url
