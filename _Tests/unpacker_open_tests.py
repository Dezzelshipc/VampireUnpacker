from unittest import TestCase, main as ut_main

from Source.UI import ui_old, ui_tkinter


class UnpackerOpenTest(TestCase):
    def test_open_unpacker_old(self):
        unp = ui_old.UIOld()
        self.assertEqual(unp.state(), "normal")
        unp.destroy()

    def test_open_unpacker_tkinter(self):
        unp = ui_tkinter.UITkinter()
        self.assertEqual(unp.state(), "normal")
        unp.destroy()

if __name__ == "__main__":
    ut_main()