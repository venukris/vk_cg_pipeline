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

from database.store import Store
from assets.exceptions import DataMismatchException, MissingDBDataException
from assets.container import Container
import utils
import constants
import logging

logger = logging.getLogger(__name__)


class AssetBase(object):
    def __init__(self, name):
        self._name = name
        self._name_generator = name_generator_factory(self)

    def name(self):
        if not self._name:
            self._name = self._name_generator.generate_name()
        return self._name

    def set_name(self, name):
        self._name = name


class Asset(AssetBase):
    def __init__(self, slot, name=None):
        """
            @:param slot: instance of slot.Slot object representing the place
                          or the location of the asset. Location does not
                          refer to the location in the file system. It is a
                          uniquely identifiable path in the data structure
                          established for production.
        """
        super(Asset, self).__init__(name)
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
            logger.warning("No versions found for {}".format(self.name()))
            return
        asset_type = Store.get_type_data(self.slot())

        if asset_type != self.type():
            logger.error("Mismatch in asset type between Asset object"
                         " and Asset entry in database:\n"
                         "\tslot -> {}\n"
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
        logger.debug("Loaded {} versions for {} (latest:v{})"
                     .format(len(self.versions()),
                             self.name(),
                             self.latest_version()
                             )
                     )

    def __eq__(self, other):
        if isinstance(other, Asset):
            return self.slot() == other.slot()
        else:
            raise TypeError

    def __str__(self):
        return '{class_}:{_name}'.format(
            class_=type(self).__name__,
            **vars(self)
        )

    def __repr__(self):
        return '{class_}({_slot})'.format(
            class_=type(self).__name__,
            **vars(self)
        )


class AssetVersion(AssetBase):
    def __init__(self, version, slot=None, asset=None, name=None):
        super(AssetVersion, self).__init__(name)
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

    def name(self):
        super(AssetVersion, self).name()
        return "{name}_v{version}".format(name=self._name,
                                          version=self.version())

    def contents(self):
        return None if not self._container else self._container.contents()

    def asset(self):
        return self._asset if self._asset else Asset(self._slot)

    def dependencies(self):
        if not self._dependencies_loaded:
            logger.debug("Loading dependencies for {}.."
                         .format(self.name()))
            self._load_dependencies()
            self._dependencies_loaded = True
            logger.debug("Loaded {} dependencies"
                         .format(len(self.dependencies())))
        return self._dependencies

    def add_dependency(self, dependency):
        # TODO : implement AssetVersion.add_dependency()
        pass

    def _load_dependencies(self):
        for dep in Store.get_dependency_data(self.slot(), self.version()):
            # TODO: Create Asset object and use it to create AssetVersion
            self._dependencies.append(AssetVersion(slot=dep[0],
                                                   version=dep[1]))

    def _load_container(self):
        version_data = Store.get_version_data(self.slot(), self.version())
        if version_data is None:
            logger.warning("Unable to load container for {}"
                           " as the version data is missing"
                           .format(self.name()))
            return

        content_type = Store.get_type_data(self.slot())
        if content_type is None:
            logger.error("Unable to load container for {}"
                         "as the content type is missing"
                         .format(self.name()))
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
        return '{class_}:{_name}'.format(
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
            logger.warning("No contents found in {}->{}"
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


def name_generator_factory(item):
    """
    Factory method to name generators.
    For now there is only one way to generate
    names. Potentially there could be many different
    ways to do that based on the "item"
    :param item: Specifies criteria to create a generator
    :return:  Name generator object
    """
    if isinstance(item, Asset) or isinstance(item, AssetVersion):
        return utils.AssetNameGenerator(item)
