import os
import re
import abc
import json
import logging
from .exceptions import TokenNotFoundException

logger = logging.getLogger(__name__)
NAME_RULE_CONFIG = os.path.abspath("../config/asset_name_rules.json")


class NameGenerator(object):
    """
    Abstract class for name generators.

    Name generators are used to come up with names for pipeline objects
    based on certain pre-configured set of rules.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        config_file = os.environ.get('NAME_RULE_CONFIG', None)
        if not config_file:
            config_file = NAME_RULE_CONFIG
        if not os.path.exists(config_file):
            logger.error("Name rules could not be loaded. Invalid config file {}"
                         .format(config_file))
        self._name_rules = json.load(open(config_file, 'r'))

    @abc.abstractmethod
    def generate_name(self):
        raise NotImplementedError


class AssetNameGenerator(NameGenerator):
    """
    Name generator for Asset and AssetVersion objects.

    It creates names from slots by grabbing values of slot tokens
    and concatenating them into a string. The rules for grabbing
    specific token values are configured in NAME_RULE_CONFIG.
    """

    def __init__(self, *args, **kwargs):
        super(AssetNameGenerator, self).__init__(args, kwargs)
        if len(args) > 0:
            self._asset = args[0]

        if not self._asset:
            logger.error("Initialization failed as asset was not given!")
            return

    def generate_name(self):
        try:
            return "_".join(slot_parser(self._asset.slot(), x)
                            for x in self._get_tokens(self._asset.slot()))
        except TokenNotFoundException:
            logger.error("Name generation failed! "
                         "Please check the name rule config.")

    def _get_tokens(self, slot):
        re_tokens = []
        for _, rule in self._name_rules.items():
            match = re.match("({})".format(rule["regex"]), slot)
            if not match:
                continue
            if match.groups()[0] == slot:
                re_tokens = rule.get("tokens", [])
                if len(re_tokens) > 0:
                    return re_tokens
        return re_tokens


def slot_parser(slot, token):
    m = re.match(".*\/{}:([a-z0-9]+)".format(token), slot)
    if m:
        return m.groups()[0]
    logger.warning("Token {} not found in {}".format(token, slot))
    raise TokenNotFoundException




