import os
import logging
from common.path import Path

logger = logging.getLogger(__name__)


class Launcher(object):
    def __init__(self, presets_dir=None):
        if not presets_dir:
            presets_dir = os.environ.get('LAUNCHER_PRESETS_DIR', None)

        try:
            presets_path = Path(presets_dir)
        except IOError, e:
            logger.error('LAUNCHER_PRESETS_DIR may not be set or does not exist. '
                         'Cannot run preset!')
            raise e

        self._preset_files = presets_path.get_files(ext='json')

    def launch(self, preset=None):
        print self._preset_files


if __name__ == '__main__':
    Launcher(presets_dir='/Users/venuk/develop/scratch/presets').launch()
