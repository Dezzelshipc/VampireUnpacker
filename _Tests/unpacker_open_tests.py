from unittest import TestCase, main as ut_main

from Source.UI import ui_old


class UnpackerOpenTest(TestCase):
    def test_unpacker_open(self):
        unp = ui_old.UIOld()
        self.assertEqual(unp.state(), "normal")

if __name__ == "__main__":
    ut_main()