import datetime
import json

from .schema_validated import SchemaValidated


class _DocumentObject(dict):
    def __init__(self, *args, **kwargs):
        super(_DocumentObject, self).__init__(*args, **kwargs)
        self.__dict__ = self

    @classmethod
    def create_from(cls, data, schema=None):
        if isinstance(data, dict):
            return cls((k, cls.create_from(v)) for (k, v) in data.items())
        elif isinstance(data, list):
            return list(cls.create_from(x) for x in data)
        return data

    def __getattr__(self, name):
        return None


class Document(SchemaValidated):
    schema_file = 'document-schema.yaml'

    def __init__(self, data=None, errors=None):
        self._data = data or {}
        self._errors = errors or []
        super(Document, self).__init__()

    @property
    def type(self):
        return self._data['type']

    @property
    def event(self):
        return _DocumentObject.create_from(self._data['event'])

    @property
    def errors(self):
        return _DocumentObject.create_from(self._errors)

    def as_dict(self):
        return {
            'document': self._data,
            'errors': self._errors,
        }

    def as_json(self):
        # https://stackoverflow.com/a/22238613

        def json_serial(obj):
            """JSON serializer for objects not serializable by default json code"""

            if isinstance(obj, (datetime.datetime, datetime.date)):
                serial = obj.isoformat()
                return serial
            raise TypeError("Type %s not serializable" % type(obj))

        ret = self.as_dict()

        return json.dumps(ret, indent=4, ensure_ascii=False, default=json_serial)
