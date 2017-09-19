import os
import re
import abc
import json

import logging
logger = logging.getLogger(__name__)

NAME_RULE_CONFIG = os.path.abspath("assets/config/asset_name_rules.json")


class NameGenerator(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        config_file = NAME_RULE_CONFIG
        if kwargs.get('config', None):
            config_file = kwargs['config']
        if not os.path.exists(config_file):
            logger.error("Name rules could not be loaded. Invalid config file {}"
                         .format(config_file))
        self._name_rules = json.load(open(config_file, 'r'))

    @abc.abstractmethod
    def generate_name(self):
        raise NotImplementedError


class AssetNameGenerator(NameGenerator):
    def __init__(self, *args, **kwargs):
        super(AssetNameGenerator, self).__init__(args, kwargs)
        if len(args) > 0:
            self._asset = args[0]

        logger.debug("Hello world")

        if not self._asset:
            logger.error("Initialization failed as asset was not given!")
            return

    def generate_name(self):
        return "_".join(slot_parser(self._asset.slot(), x)
                        for x in self._get_tokens(self._asset.slot()))

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
