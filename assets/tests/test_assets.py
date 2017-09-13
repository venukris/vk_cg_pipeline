import unittest
from assets import asset, slot
from assets import constants
from database.store import Store

TEST_DATA_FILE = "/Users/venuk/develop/pipeline/assets/tests/test_data.json"


class SlotTestCase(unittest.TestCase):
    def test_create_slot(self):
        path = "PROJECT:tintin/GLOBAL_CATEGORY:characters/GLOBAL_OBJECT:brad/ASSET:model"
        slot_ = slot.Slot(path=path,
                          type=constants.CONTENT_TYPE.File)
        self.assertTrue(str(slot_) == path)


class AssetsTestCase(unittest.TestCase):
    def setUp(self):
        path = "PROJECT:tintin/GLOBAL_CATEGORY:characters/GLOBAL_OBJECT:brad/ASSET:model"
        self.new_slot = slot.Slot(path=path,
                                  type=constants.CONTENT_TYPE.File)

        path = "PROJECT:tintin/SEQUENCE:sq100/SHOT:s10/OBJECT_TYPE:char/OBJECT:david/ASSET:anim_export"
        self.existing_slot = slot.Slot(path=path,
                                       type=constants.CONTENT_TYPE.File)

    def test_create_asset_new_slot(self):
        asset_ = asset.Asset(self.new_slot)
        self.assertEqual(asset_.slot(), str(self.new_slot))
        self.assertEqual(asset_.type(), constants.CONTENT_TYPE.File.key)
        self.assertEqual(asset_.versions(), [])
        self.assertEqual(asset_.version(1), None)

    def test_create_asset_existing_slot(self):
        Store.load_data(TEST_DATA_FILE)
        asset_ = asset.Asset(self.existing_slot)
        self.assertEqual(asset_.slot(), str(self.existing_slot))
        self.assertEqual(asset_.type(), constants.CONTENT_TYPE.File.key)
        self.assertEqual(len(asset_.versions()), 2)
        self.assertEqual(asset_.version(1).contents(),
                         ['/project/sq100/s10/char/david/anim_export/david1_body.mc',
                          '/project/sq100/s10/char/david/anim_export/david1_face.mc'])


if __name__ == "__main__":
    unittest.main()
