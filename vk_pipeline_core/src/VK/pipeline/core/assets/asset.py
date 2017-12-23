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
import utils
import constants
import logging
from VK.pipeline.database.store import Store
from .exceptions import DataMismatchException, \
                        AssetVersionInitializationException
from .container import Container
from .slot import Slot


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

    def slot_type(self):
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

    def add_version(self, contents):
        self._versions.append(
            AssetVersion(
                asset=self,
                version=self._latest_version + 1,
                contents=contents
            )
        )
        self._latest_version = self._latest_version + 1

    def _load_versions(self):
        if Store.get_entries(self.slot()) is None:
            logger.warning("No versions found for {}".format(self.name()))
            return
        asset_type = Store.get_type_data(self.slot())

        if asset_type != self.slot_type():
            logger.error("Mismatch in asset type between Asset object"
                         " and Asset entry in database:\n"
                         "\tslot -> {}\n"
                         "\tobject asset type   -> {}\n"
                         "\tdatabase asset type -> {}"
                         .format(self.slot(), self.slot_type(), asset_type))
            raise DataMismatchException

        logger.info(self)
        for version in Store.get_versions_data(self.slot()):
            self._versions.append(
                AssetVersion(
                    asset=self,
                    version=version,
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
        return '{class_}:{name}'.format(
            class_=type(self).__name__,
            name=self.name()
        )

    def __repr__(self):
        return '{class_}({_slot})'.format(
            class_=type(self).__name__,
            **vars(self)
        )


class AssetVersion(AssetBase):
    def __init__(self, asset, version, contents=None, name=None):
        super(AssetVersion, self).__init__(name)
        self._asset = asset
        self._version = version
        self._dependencies = []
        self._dependencies_loaded = False
        self._container = None

        self._initialize_container(contents)

    def slot(self):
        return self._asset.slot()

    def version(self):
        return self._version

    def slot_type(self):
        return self._asset.slot_type()

    def name(self):
        super(AssetVersion, self).name()
        return "{name}_v{version}".format(name=self._name,
                                          version=self.version())

    def contents(self):
        return None if not self._container else self._container.contents()

    def asset(self):
        return self._asset

    def dependencies(self):
        if not self._dependencies_loaded:
            logger.debug("Loading dependencies for {}..".format(self.name()))
            self._load_dependencies()
            self._dependencies_loaded = True
            logger.debug("Loaded {} dependencies".format(len(self.dependencies())))
        return self._dependencies

    def add_dependency(self, asset_version):
        for dep in self._dependencies:
            if dep == asset_version:
                return
        self._dependencies.append(asset_version)

    def _initialize_container(self, contents):
        self._container = container_factory(self.slot_type())
        if self._is_new_version():
            if not contents:
                logger.error("Cannot create an AssetVersion: no contents passed.")
                raise AssetVersionInitializationException
            logger.debug("Setting contents on new asset version..")
            self._container.set_contents(contents)
        else:
            logging.debug("Loading contents on existing asset version..")
            self._container.load_contents(self.slot(), self.version())

    def _load_dependencies(self):
        for dep in Store.get_dependency_data(self.slot(), self.version()):
            stype_ = Store.get_type_data(dep[0])
            slot_ = Slot(type=stype_, path=dep[0])
            asset_ = Asset(slot=slot_)
            for asset_version in asset_.versions():
                if asset_version.version() == dep[1]:
                    self._dependencies.append(asset_version)

    def _is_new_version(self):
        return Store.get_version_data(self.slot(), self.version()) is None

    def __eq__(self, other):
        if isinstance(other, AssetVersion):
            return self.slot() == other.slot() and \
                   self.version() == other.version()
        else:
            raise TypeError

    def __str__(self):
        return '{class_}:{name}'.format(
            class_=type(self).__name__,
            name=self.name()
        )

    def __repr__(self):
        return '{class_}({_version}, {_slot}, {_asset})'.format(
            class_=type(self).__name__,
            **vars(self)
        )


class FileContainer(Container):
    def __init__(self):
        super(FileContainer, self).__init__()
        self._type = constants.CONTENT_TYPE.File

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
        self._type = constants.CONTENT_TYPE.Asset

    def load_contents(self, slot, version):
        with CheckZeroContents(self, slot, version):
            for item in Store.get_content_data(slot, version):
                self.add_content(item)

    def _is_valid(self, content):
        return isinstance(content, AssetVersion)

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

    def __exit__(self, type_, value, traceback):
        if len(self._container.contents()) == 0:
            logger.warning("No contents found in {}->{}"
                           .format(self._slot, self._version))


def container_factory(type_):
    """
    Factory method to create containers.
    :param type_: Type of container to create.
    :return: Concrete container object
    """
    if type_ == constants.CONTENT_TYPE.File:
        return FileContainer()
    if type_ == constants.CONTENT_TYPE.Asset:
        return AssetContainer()


def name_generator_factory(item):
    """
    Factory method to create name generators.
    For now there is only one way to generate names. Potentially there
    could be many different ways to do that based on the given "item".
    :param item: Specifies criteria to create a generator
    :return: Name generator object
    """
    if isinstance(item, Asset) or isinstance(item, AssetVersion):
        return utils.AssetNameGenerator(item)
