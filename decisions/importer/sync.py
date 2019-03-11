import logging


logger = logging.getLogger(__name__)


class ModelSyncher(object):

    def __init__(self, queryset, generate_obj_id, delete_func=None,
                 delete_limit=0.4, skip_delete=False):
        """
        Initialize a ModelSyncher.

        :param queryset: Django queryset containing currently known objects
        :param generate_obj_id: function that should generate same ids for "same" objects
        :param delete_func: function for de-persisting objects
        :param delete_limit: failsafe maximum fraction of objects to delete
        """
        d = {}
        self.generate_obj_id = generate_obj_id
        # Generate a list of all objects
        for obj in queryset:
            d[generate_obj_id(obj)] = obj
            obj._found = False
            obj._changed = False

        self.obj_dict = d
        self.delete_limit = delete_limit
        self.delete_func = delete_func
        self.skip_delete = skip_delete

    def mark(self, obj):
        """
        Mark object to be kept (ie. it still exists at source)

        :param obj: Object to be marked
        :raises Exception: if object has already been marked
        """
        if getattr(obj, '_found', False):
            raise Exception("Object %s (%s) already marked" % (obj, self.generate_obj_id(obj)))

        obj._found = True
        obj_id = self.generate_obj_id(obj)
        if obj_id not in self.obj_dict:
            self.obj_dict[obj_id] = obj
        assert self.obj_dict[obj_id] == obj

    def get(self, obj_id):
        """
        Get an object per its synchronization id

        :param obj_id: synchronization id of the object
        :returns: a django model for the object
        """
        return self.obj_dict.get(obj_id, None)

    def finish(self):
        """
        Run synchronization, applying delete_func to items not mark():ed
        """
        if self.skip_delete:
            return

        delete_list = []
        for obj_id, obj in self.obj_dict.items():
            if not obj._found:
                delete_list.append(obj)

        if self.delete_limit is not None:
            max_delete_count = len(self.obj_dict) * self.delete_limit
            if len(delete_list) > 5 and len(delete_list) > max_delete_count:
                raise Exception("Attempting to delete more than %d%% of total items" % int(self.delete_limit * 100))

        for obj in delete_list:
            if self.delete_func:
                self.delete_func(obj)
            else:
                logger.info("Deleting object %s" % obj)
                obj.delete()
