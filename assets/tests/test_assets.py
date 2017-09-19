import unittest
from assets import asset, slot
from assets import constants
from database.store import Store

TEST_DATA_FILE = "/Users/venuk/develop/pipeline/assets/tests/test_data.json"


class SlotTestCase(unittest.TestCase):
    def test_create_slot(self):
        path = "PROJECT:tintin/GLOBALOBJECT_TYPE:characters/" \
               "GLOBALOBJECT:brad/ASSET:model"
        slot_ = slot.Slot(path=path,
                          type=constants.CONTENT_TYPE.File)
        self.assertTrue(str(slot_) == path)


class AssetsTestCase(unittest.TestCase):
    def setUp(self):
        path = "PROJECT:tintin/GLOBALOBJECT_TYPE:characters/" \
               "GLOBALOBJECT:brad/ASSET:model"
        self.new_slot = slot.Slot(path=path,
                                  type=constants.CONTENT_TYPE.File)

        path = "PROJECT:tintin/SEQUENCE:sq100/SHOT:s10/OBJECT_TYPE:char/" \
               "OBJECT:david/ASSET:animexport"
        self.existing_slot = slot.Slot(path=path,
                                       type=constants.CONTENT_TYPE.File)
        Store.load_data(TEST_DATA_FILE)

    def test_create_asset_new_slot(self):
        asset_ = asset.Asset(self.new_slot)
        self.assertEqual(asset_.slot(), str(self.new_slot))
        self.assertEqual(asset_.type(), constants.CONTENT_TYPE.File.key)
        self.assertEqual(asset_.versions(), [])
        self.assertEqual(asset_.version(1), None)
        self.assertEqual(asset_.name(), 'characters_brad_model')

    def test_create_asset_existing_slot(self):
        asset_ = asset.Asset(self.existing_slot)
        contents = ['/project/sq100/s10/char/david/anim_export/david1_body.mc',
                    '/project/sq100/s10/char/david/anim_export/david1_face.mc']
        self.assertEqual(asset_.slot(), str(self.existing_slot))
        self.assertEqual(asset_.type(), constants.CONTENT_TYPE.File.key)
        self.assertEqual(len(asset_.versions()), 2)
        self.assertEqual(asset_.version(1).contents(), contents)

    def test_load_dependencies(self):
        asset_ = asset.Asset(self.existing_slot)
        asset_version = asset_.version(1)
        self.assertEqual(asset_version.name(), 'sq100_s10_char_david_animexport_v1')
        self.assertEqual(len(asset_version.dependencies()), 2)

        asset_version_dep0 = asset_version.dependencies()[0]
        self.assertEqual(len(asset_version_dep0.dependencies()), 1)
        self.assertEqual(asset_version_dep0.dependencies()[0].slot(),
                         "PROJECT:tintin/GLOBALOBJECT_TYPE:characters/"
                         + "GLOBALOBJECT:david/ASSET:model")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()
