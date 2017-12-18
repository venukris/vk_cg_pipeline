import os
import json


class Store(object):
    __instance = None
    _data = {}

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    @classmethod
    def load_data(cls, source):
        if isinstance(source, dict):
            cls._data = source
        elif isinstance(source, str) and \
                source.endswith(".json") and \
                os.path.exists(source):
            data_dict = json.load(open(source, "r"))
            cls._data = data_dict.get('data', {})

    @classmethod
    def get_entries(cls, slot):
        return cls._data.get(slot, None)

    @classmethod
    def get_type_data(cls, slot):
        slot_data = cls.get_entries(slot)
        if slot_data is not None:
            return slot_data.get('type', None)

    @classmethod
    def get_versions_data(cls, slot):
        slot_data = cls.get_entries(slot)
        if slot_data is not None:
            versions_data = slot_data.get('versions', None)
            if versions_data is not None:
                # Json format only allows string key values.
                # Since versions are integers but stored as keys
                # in json to work as keys, we convert them to
                # integer here before its used by client code.
                new_versions_data = {}
                for key in versions_data:
                    new_versions_data[int(key)] = versions_data[key]
                versions_data = new_versions_data
            return versions_data


    @classmethod
    def get_version_data(cls, slot, version):
        versions_data = cls.get_versions_data(slot)
        if versions_data is not None:
            return versions_data.get(version, None)

    @classmethod
    def get_dependency_data(cls, slot, version):
        version_data = cls.get_version_data(slot, version)
        if version_data is not None:
            return version_data.get('dependencies', [])
        return []

    @classmethod
    def get_content_data(cls, slot, version):
        version_data = cls.get_version_data(slot, version)
        if version_data is not None:
            return version_data.get('contents', [])
        return []
