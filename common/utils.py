import collections


def create_constant(**named_attributes):
    constant_container = collections.namedtuple('ConstantContainer', named_attributes.keys())
    return constant_container(*named_attributes.values())
