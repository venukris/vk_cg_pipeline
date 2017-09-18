class DataMismatchException(Exception):
    def __init__(self):
        super(DataMismatchException, self).__init__()


class MissingDBDataException(Exception):
    def __init__(self):
        super(MissingDBDataException, self).__init__()