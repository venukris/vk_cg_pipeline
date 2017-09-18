"""
    The Asset and the AssetVersion classes form the fundamental data
    representations in the pipeline. They represent a "product" committed
    by an individual/department in production. A product can either be
    a group of files or other Asset objects.

    Ex:
        Model asset -> geometry file output by modeling dept
        Anim curve asset -> animation data files output by animators
        Surfacing asset -> list of dif, spec, bump maps that make up
                            the look for a model

    An Asset by itself just represents a "slot" where AssetVersions
    can be committed and thus a "slot" uniquely identifies an Asset.
    Every commit of data is given a "version" which is represented
    by an AssetVersion object. A combination of "slot" and "version"
    uniquely identifies an AssetVersion.

    Furthermore, an AssetVersion stores "dependencies" which basically
    are references to other AssetVersions that were used as source
    to generate it.

    AssetVersions can bundle a bunch of other AssetVersions to represent
    a bigger package of data.
    Ex: Layout output package -> camera rig asset + set model asset +
                                 character rig assets + etc..

"""
import logging
from database.store import Store
from assets.exceptions import DataMismatchException, MissingDBDataException
from assets.container import Container
import constants

logging.basicConfig(level=logging.DEBUG)


class Asset(object):
    def __init__(self, slot):
        """
            @:param slot: instance of slot.Slot object representing the place
                          or the location of the asset. Location does not
                          refer to the location in the file system. It is a
                          uniquely identifiable path in the data structure
                          established for production.
        """
        self._slot = slot
        self._versions = []
        self._latest_version = 0
        self._metadata = {}
        self._load_versions()

    def slot(self):
        return self._slot.id()

    def type(self):
        return str(self._slot.type())

    def versions(self):
        return self._versions

    def version(self, version):
        filtered_versions = filter(
            lambda x: int(x.version()) == version,
            self._versions
        )
        return None if len(filtered_versions) == 0 else filtered_versions[0]

    def latest_version(self):
        return self._latest_version

    def add_version(self):
        self._versions.append(
            AssetVersion(
                asset=self,
                version=self._latest_version + 1,
                slot=self.slot()
            )
        )
        self._latest_version = self._latest_version + 1

    def _load_versions(self):
        if Store.get_entries(self.slot()) is None:
            logging.warning("No versions found for asset at {}".format(self.slot()))
            return
        asset_type = Store.get_type_data(self.slot())

        if asset_type != self.type():
            logging.error("Mismatch in asset type between Asset object"
                          " and Asset entry in database:\n"
                          "\tSlot -> {}\n"
                          "\tobject asset type   -> {}\n"
                          "\tdatabase asset type -> {}"
                          .format(self.slot(), self.type(), asset_type))
            raise DataMismatchException

        for version in Store.get_versions_data(self.slot()):
            self._versions.append(
                AssetVersion(
                    asset=self,
                    version=version,
                    slot=self.slot()
                )
            )
        self._latest_version = 0 if len(self._versions) == 0 \
            else self._versions[-1].version()
        logging.debug("Loaded {} versions for {} (latest:v{})"
                      .format(len(self.versions()),
                              self.slot(),
                              self.latest_version()
                              )
                      )

    def __eq__(self, other):
        if isinstance(other, Asset):
            return self.slot() == other.slot()
        else:
            raise TypeError

    def __str__(self):
        return '{class_}:{_slot}'.format(
            class_=type(self).__name__,
            **vars(self)
        )

    def __repr__(self):
        return '{class_}({_slot})'.format(
            class_=type(self).__name__,
            **vars(self)
        )


class AssetVersion(object):
    def __init__(self, version, slot=None, asset=None):
        if slot is None and asset is None:
            raise ValueError
        self._asset = asset
        self._version = version
        self._dependencies = []
        self._dependencies_loaded = False
        self._container = None
        self._slot = slot if slot is not None else asset.slot()

        self._load_container()

    def slot(self):
        return self._slot

    def version(self):
        return self._version

    def set_version(self, version):
        self._version = version

    def contents(self):
        return None if not self._container else self._container.contents()

    def asset(self):
        return self._asset if self._asset else Asset(self._slot)

    def dependencies(self):
        if not self._dependencies_loaded:
            logging.debug("Loading dependencies for {}->v{}.."
                          .format(self.slot(), self.version()))
            self._load_dependencies()
            self._dependencies_loaded = True
            logging.debug("Loaded {} dependencies"
                          .format(len(self.dependencies())))
        return self._dependencies

    def add_dependency(self, dependency):
        # TODO : implement AssetVersion.add_dependency()
        pass

    def _load_dependencies(self):
        for dep in Store.get_dependency_data(self.slot(), self.version()):
            self._dependencies.append(AssetVersion(slot=dep[0],
                                                   version=dep[1]))

    def _load_container(self):
        version_data = Store.get_version_data(self.slot(), self.version())
        if version_data is None:
            logging.warning("Unable to load container for {}->v{}"
                            " as the version data is missing"
                            .format(self.slot(), self.version()))
            return

        content_type = Store.get_type_data(self.slot())
        if content_type is None:
            logging.error("Unable to load container for {}->v{}"
                          "as the content type is missing"
                          .format(self.slot(), self.version()))
            raise MissingDBDataException

        self._container = container_factory(content_type)
        self._container.load_contents(self.slot(), self.version())

    def __eq__(self, other):
        if isinstance(other, AssetVersion):
            return self.slot() == other.slot() and \
                   self.version() == other.version()
        else:
            raise TypeError

    def __str__(self):
        return '{class_}:{_slot}->v{_version}'.format(
            class_=type(self).__name__,
            **vars(self)
        )

    def __repr__(self):
        return '{class_}({_version}, {_slot}, {_asset})'.format(
            class_=type(self).__name__,
            **vars(self)
        )


class FileContainer(Container):
    def __init__(self):
        super(FileContainer, self).__init__()
        self._type = constants.CONTENT_TYPE.File.key

    def load_contents(self, slot, version):
        with CheckZeroContents(self, slot, version):
            self.set_contents(Store.get_content_data(slot, version))

    def _is_valid(self, content):
        return isinstance(content, str) or isinstance(content, unicode)

    def _find_content(self, content):
        return content if content in self._contents else None


class AssetContainer(Container):
    def __init__(self):
        super(AssetContainer, self).__init__()
        self._type = constants.CONTENT_TYPE.Asset.key

    def load_contents(self, slot, version):
        with CheckZeroContents(self, slot, version):
            for item in Store.get_content_data(slot, version):
                self.add_content(item)

    def _is_valid(self, content):
        return isinstance(content, Asset)

    def _find_content(self, content):
        def filter_func(x):
            return x.slot() == content.slot() and \
                   x.version() == content.version()

        return filter(filter_func, self.contents())


class CheckZeroContents(object):
    def __init__(self, container, slot, version):
        self._container = container
        self._slot = slot
        self._version = version

    def __enter__(self):
        return self._container

    def __exit__(self, type, value, traceback):
        if len(self._container.contents()) == 0:
            logging.warning("No contents found in {}->{}"
                            .format(self._slot, self._version))


def container_factory(type_):
    """
    Factory method to create containers
    :param type_: Type of container to create.
    :return: Concrete container object
    """
    if type_ == constants.CONTENT_TYPE.File.key:
        return FileContainer()
    if type_ == constants.CONTENT_TYPE.Asset.key:
        return AssetContainer()
