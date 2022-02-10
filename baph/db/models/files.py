from __future__ import absolute_import
from django.core.files.images import ImageFile
import hashlib

def md5_checksum(filepath):
    if type(filepath) == str:
        fh = open(filepath, 'rb')
    elif hasattr(filepath, 'read'):
        fh = filepath
    else:
        raise Exception('Invalid type for md5_checksum: %s' % type(filepath))
    m = hashlib.md5()
    while True:
        data = fh.read(8192)
        if not data:
            break
        m.update(data)
    return m.hexdigest()

class ChecksumImageFile(ImageFile):

    def __init__(self, *args, **kwargs):
        self.storage = kwargs.pop('storage', None)
        super(ChecksumImageFile, self).__init__(*args, **kwargs)

    @property
    def checksum(self):
        if not hasattr(self, '_checksum'):
            if hasattr(self.file, 'checksum'):
                self._checksum = self.file.checksum
            else:
                self._checksum = md5_checksum(self)
        return self._checksum
        
    def save(self):
        if not self.storage:
            raise Exception('ChecksumImageFile.save() cannot be called unless '
                'it was initialized with the "storage" kwarg')
        self.name = self.storage.save(self.name, self.file)
        return self.name
        
    @property
    def url(self):
        if not self.storage:
            raise Exception('ChecksumImageFile.url cannot be called unless '
                'it was initialized with the "storage" kwarg')
        return self.storage.url(self.name)
