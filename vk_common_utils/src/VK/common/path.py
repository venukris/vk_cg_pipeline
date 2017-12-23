import os
import glob
import logging

logger = logging.getLogger(__name__)


class Path(object):
    def __init__(self, path):
        self._path = path

        if not os.path.exists(self._path):
            logger.error("Invalid path: {}".format(self._path))
            raise IOError()

    def get_files(self, ext=None, recursive=False):
        if os.path.isfile(self._path):
            logger.error("Invalid call to get_files(). This path instance is a file")
            raise IOError()

        def get_files_rec(path):
            files = list()
            basedir, subdirs, _ = list(os.walk(path))[0]
            if ext:
                files.extend(glob.glob("{}/*.{}".format(path, ext)))
            else:
                files.extend([x for x in glob.glob("{}/*".format(path))
                              if os.path.isfile(x)])

            if not recursive or len(subdirs) == 0:
                return files

            for subdir in subdirs:
                files.extend(get_files_rec("{}/{}".format(basedir, subdir)))
                return files

        return get_files_rec(self._path)
