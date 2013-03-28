

class Options(object):
    def __init__(self, meta, app_label=None):
        # cache_detail_keys are primary cache keys which are invalidated
        # anytime the object changes. Because this key cannot exist prior
        # to create of the object, these are not processed during CREATE.
        # format: (cache_key_template, columns)
        # cache_key_template is a string, with placeholders for formatting
        # using data from the instance (ex: businesses:detail:id=%(id)s)
        # columns is a list of columns to monitor for changes (ex: ['city'])
        # the key will only be invalidated if at least one specified column
        # has changed, or columns is None
        self.cache_detail_keys = []
        # cache_list_keys are keys for lists of objects. These keys are not
        # singular keys, but "version keys", which are bases for multiple
        # subsets of the base set (subsets being caused by filters or searches)
        # format: (cache_key_template, columns) (same as above)
        # when invalidated, rather than deleting the key, the key is
        # incremented, so all subsets attempting to use the contained value
        # for key generation will be invalidated at once
        self.cache_list_keys = []
        # cache_pointers is a list of identity keys which contain no data
        # other than the primary key of the object being pointed at.
        # format: (cache_key_template, columns, name)
        # cache_key_template and columns function as above, and 'name' is
        # an alias to help distinguish between keys during unittesting
        # when an update occurs, two actions occur: the new value is set
        # to the current object, and the previous value (if different) is
        # set to False (not deleted)
        self.cache_pointers = []
        # cache_relations is a list of relations which should be monitored
        # for changes when generating cache keys for invalidation. This should
        # be used for relationships to composite keys, which cannot be
        # handled properly via cache_cascades
        self.cache_relations = []
        # cache_cascades is a list of relations through which to cascade
        # invalidations. Use this when an object is cached as a subobject of
        # a larger cache, to signal the parent that it needs to recache
        self.cache_cascades = []
        
        self.limit = 1000
        self.model_name, self.verbose_name = None, None
        self.verbose_name_plural = None
        self.permissions = []
        self.object_name, self.app_label = None, app_label
        self.pk = None
        
        if meta:
            for k,v in meta.__dict__.items():
                setattr(self, k, v)

