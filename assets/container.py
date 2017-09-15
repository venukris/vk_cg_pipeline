import abc


class Container(object):
    def __init__(self):
        self._type = None
        self._contents = []

    def contents(self):
        return self._contents

    def set_contents(self, contents):
        def filter_func(x):
            return self._is_valid(x)
        if len(filter(filter_func, contents)) == len(contents):
            self._contents = contents

    def add_content(self, content):
        if self._is_valid(content) and not self._exists(content):
            self._contents.append(content)

    def remove_content(self, content):
        if len(self._find_content(content)) == content:
            self._contents.remove(content)

    def type(self):
        return self._type

    def set_type(self, type_):
        self._type = type_

    def _exists(self, content):
        return self._find_content(content) is not None

    @abc.abstractmethod
    def _is_valid(self, content):
        raise NotImplementedError

    @abc.abstractmethod
    def _find_content(self, content):
        raise NotImplementedError

    @abc.abstractmethod
    def load_contents(self, slot, version):
        raise NotImplementedError

    def __str__(self):
        return '{class_}:{_type}'.format(
            class_=type(self).__name__,
            **vars(self)
        )

    def __repr__(self):
        return '{class_}()'.format(
            class_=type(self).__name__,
            **vars(self)
        )



