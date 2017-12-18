class DataMismatchException(Exception):
    def __init__(self):
        super(DataMismatchException, self).__init__()


class MissingDBDataException(Exception):
    def __init__(self):
        super(MissingDBDataException, self).__init__()


class TokenNotFoundException(Exception):
    def __init__(self):
        super(TokenNotFoundException, self).__init__()


class AssetVersionInitializationException(Exception):
    def __init__(self):
        super(AssetVersionInitializationException, self).__init__()
