import json
import os

import jsonschema
import yaml


class SchemaValidated(object):
    schema = None

    def __init__(self, *args, **kwargs):
        self.validate()
        super(SchemaValidated, self).__init__(*args, **kwargs)

    def validate(self):
        jsonschema.validate(json.loads(self.as_json()), self.get_schema())

    @classmethod
    def get_schema(cls):
        if cls.schema is None:
            with open(cls._get_schema_file_full_path(), 'rb') as fp:
                cls.schema = yaml.load(fp.read())
        return cls.schema

    @classmethod
    def _get_schema_file_full_path(cls):
        directory = os.path.dirname(__file__)
        return os.path.join(directory, cls.schema_file)
