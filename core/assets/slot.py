class Slot(object):
    def __init__(self, **kwargs):
        self._slot_id = None
        self._type = kwargs.get('type', None)
        self._generate_slot_id(kwargs)

    def id(self):
        return self._slot_id

    def type(self):
        return self._type

    def _generate_slot_id(self, params):
        if 'path' in params:
            self._slot_id = params['path']

    def __str__(self):
        return self._slot_id
