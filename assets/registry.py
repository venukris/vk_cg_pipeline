import abc


class Registry(object):
    __metaclass__ = abc.ABCMeta
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    @classmethod
    @abc.abstractmethod
    def register(cls, item):
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def unregister(cls, item):
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def find_item(cls, key):
        raise NotImplementedError


class ElementRegistry(Registry):
    _registry_data = {}

    @classmethod
    def register(cls, item):
        if cls.find_item(item.slot()) is None:
            cls._registry_data[item.slot()] = item

    @classmethod
    def unregister(cls, item):
        if cls.find_item(item.slot()) is not None:
            cls._registry_data.pop(item.slot())

    @classmethod
    def find_item(cls, key):
        return cls._registry_data.get(key, None)