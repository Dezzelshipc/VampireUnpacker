import os
import sys
from pathlib import Path
from typing import Iterable, Callable, Any

import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk

from Source.Config.config import Game, DLCType, Config
from Source.Data.meta_data import MetaDataHandler
from Source.UI.ui import UIBase
from Source.Utility.constants import IS_DEBUG
from Source.Utility.logger import Logger
from Source.UI.boxes_tkinter import CheckBoxes, ButtonsBox


class UITkinter(tk.Tk, UIBase):
    def __init__(self, width=600, height=400):
        sys.stdout = Logger(sys.stdout)
        sys.stderr = Logger(sys.stderr)
        IS_DEBUG and print(f"{IS_DEBUG = }\n")

        ###
        UIBase.__init__(self)
        super().__init__()
        ###
        self._pady = 5

        self.minsize(width, height)

        self.title(self._title_text)
        self.iconphoto(True, tk.PhotoImage(file=self._icon_path))

        self.__update_progress_bar: Callable[[int | float, str, str], None] = None
        self.__update_loaded_metadata: Callable[[Game.VS], None] = None

        self._main_frame = ttk.Frame(self)
        self.set_main_layout()

    def set_main_layout(self):
        self.grid_columnconfigure(0, weight=1)

        ###
        _pg_frame = ttk.Frame(self)
        _pg_frame.grid(column=0, row=2, pady=self._pady)

        _progress_bar = ttk.Progressbar(
            _pg_frame,
            orient='horizontal',
            mode='determinate',
            length=300
        )
        _progress_bar_label_above_string = tk.StringVar(name="pg_s_a")
        _progress_bar_label_above = ttk.Label(_pg_frame, textvariable=_progress_bar_label_above_string)
        _progress_bar_label_below_string = tk.StringVar(name="pg_s_b")
        _progress_bar_label_below = ttk.Label(_pg_frame, textvariable=_progress_bar_label_below_string)

        _progress_bar_label_above.grid(column=0, row=0)
        _progress_bar.grid(column=0, row=1)
        _progress_bar_label_below.grid(column=0, row=2)

        def upd_pb(value: int | float, above: str, below: str):
            _progress_bar['value'] = value
            _progress_bar.update()

            _progress_bar_label_above_string.set(above)
            _progress_bar_label_above.update()

            _progress_bar_label_below_string.set(below)
            _progress_bar_label_below.update()

        self.__update_progress_bar = upd_pb
        upd_pb(40, "ABOVE", "BELOW")
        ###

        ###
        _md_frame = ttk.Frame(self)
        _md_frame.grid(column=0, row=3, pady=self._pady)

        _metadata_label_string = tk.StringVar(name="md_s")
        _metadata_label = ttk.Label(_md_frame, textvariable=_metadata_label_string)

        _metadata_label.grid(column=0, row=0)

        def upd_md(text: str):
            _metadata_label_string.set(text)
            _metadata_label.update()

        def after_load(game: Game | None) -> None:
            match game:
                case None:
                    metadata_string = f"Not loaded any metadata"
                case Game.SPECIAL:
                    metadata_string = f"Loaded empty (special) metadata for generating images from meta"
                case _:
                    metadata_string = f"Loaded metadata for {game.get_default_dlc().value.full_name}"

            upd_md(metadata_string)

        self.__update_loaded_metadata = after_load
        after_load(None)

        _md_change_frame = ttk.Frame(_md_frame)
        _md_change_frame.grid(column=0, row=1)

        MetaDataHandler.register("after_load", after_load)
        MetaDataHandler.register("before_load",
                                 lambda o, n: upd_md(f"Loading metadata for {n.get_default_dlc().value.full_name}..."))

        ttk.Button(
            _md_change_frame,
            text="Load VS Metadata",
            command=lambda: MetaDataHandler.load(Game.VS),
        ).grid(column=0, row=0)

        ttk.Button(
            _md_change_frame,
            text="Load VC Metadata",
            command=lambda: MetaDataHandler.load(Game.VC),
        ).grid(column=1, row=0)
        ###

        ###
        _config_frame = ttk.Frame(self)
        _config_frame.grid(column=0, row=4, pady=self._pady)

        ttk.Button(
            _config_frame,
            text="Rip data automatically",
            command=self.rip_data
        ).grid(column=0, row=0)

        ttk.Button(
            _config_frame,
            text="Change config",
            command=self.change_config
        ).grid(column=1, row=0)

        ttk.Button(
            _config_frame,
            text="Open last loaded folder",
            command=self.open_last_loaded_folder
        ).grid(column=0, row=1, columnspan=2)
        ###

        ###
        _by_meta_frame = ttk.Frame(self)
        _by_meta_frame.grid(column=0, row=5, pady=self._pady)

        ttk.Button(
            _by_meta_frame,
            text="Select image atlas to unpack images",
            command=lambda: self.unpack_by_meta(self.generate_images_by_meta)
        ).grid(column=0, row=0)

        ttk.Button(
            _by_meta_frame,
            text="... from spritesheets",
            command=lambda: self.unpack_by_meta_from_spritesheets(self.generate_images_by_meta)
        ).grid(column=1, row=0)

        ttk.Button(
            _by_meta_frame,
            text="Select image atlas to unpack animations",
            command=lambda: self.unpack_by_meta(self.generate_animation_by_meta)
        ).grid(column=0, row=1)

        ttk.Button(
            _by_meta_frame,
            text="... from spritesheets",
            command=lambda: self.unpack_by_meta_from_spritesheets(self.generate_animation_by_meta)
        ).grid(column=1, row=1)
        ###

        ###
        self._main_frame.grid(column=0, row=6, pady=self._pady)

        def set_main_frame(game: Game | None) -> None:
            match game:
                case Game.VS:
                    self.set_vs_frame()
                case Game.VC:
                    self.set_vc_frame()
                case _:
                    self.clear_main_frame()

        MetaDataHandler.register("after_load", set_main_frame)
        ###

    def clear_main_frame(self):
        for child in self._main_frame.winfo_children():
            child.destroy()

    def set_vs_frame(self):
        self.clear_main_frame()
        main_frame = self._main_frame

        ttk.Button(
            main_frame,
            text="Create Game Version file",
            command=self.create_version_file,
        ).grid(column=0, row=0)

    def set_vc_frame(self):
        self.clear_main_frame()
        main_frame = self._main_frame

        ttk.Button(
            main_frame,
            text="Create Game Version file",
            command=self.create_version_file,
        ).grid(column=0, row=0)

    @staticmethod
    def ask_open_file_name(title: str = "Select file", initialdir: set | os.PathLike[str] = None,
                           filetypes: Iterable[tuple[str, str | list[str]]] = None) -> Path | None:
        _path = filedialog.askopenfilename(initialdir=initialdir, title=title, filetypes=filetypes)
        return Path(_path) if _path else None

    @staticmethod
    def ask_open_file_names(title: str = "Select file", initialdir: set | os.PathLike[str] = None,
                            filetypes: Iterable[tuple[str, str | list[str]]] = None) -> Iterable[Path] | None:
        _paths = filedialog.askopenfilenames(initialdir=initialdir, title=title, filetypes=filetypes)
        return [Path(p) for p in _paths] if _paths else None

    @staticmethod
    def ask_yes_no(title: str = None, message: str = None, **options) -> bool:
        return tk.messagebox.askyesno(title, message, **options)

    @staticmethod
    def ask_integer(title: str = None,
                    prompt: str = None,
                    *,
                    initialvalue: int = None,
                    minvalue: int = None,
                    maxvalue: int = None,
                    **options) -> int:
        return tk.simpledialog.askinteger(title, prompt, initialvalue=initialvalue, minvalue=minvalue,
                                          maxvalue=maxvalue, **options)

    @staticmethod
    def show_info(title: str = None, message: str = None, **options) -> None:
        tk.messagebox.showinfo(title, message, **options)

    @staticmethod
    def show_warning(title: str = None, message: str = None, **options) -> None:
        tk.messagebox.showwarning(title, message, **options)

    @staticmethod
    def show_error(title: str = None, message: str = None, **options) -> None:
        tk.messagebox.showerror(title, message, **options)


    def progress_bar_set_percent(self, current: int | float, total: int | float, add_text: str = "") -> None:
        self.__update_progress_bar(current / total * 100 if total else 100, f"{current} / {total}", add_text)

    def progress_bar_set_sec(self, seconds: float, add_text: str = "") -> None:
        self.__update_progress_bar((seconds * 10) % 100, f"{seconds:.2f}", add_text)

    def open_last_loaded_folder(self) -> None:
        if self._last_loaded_folder and self._last_loaded_folder.exists():
            os.startfile(self._last_loaded_folder)

    def change_config(self) -> None:
        Config.invoke_config_changer(self)

    def check_boxes(self, list_to_boxes, title="", label: str | list[str] = "", width: int = 300) -> list[Any]:
        cbs = CheckBoxes(list_to_boxes, title=title, label=label, parent=self, width=width)
        cbs.wait_window()
        return cbs.return_data

    def buttons_box(self, list_to_texts, title="", label: str | list[str] = "", width: int = 300) -> Any | None:
        bb = ButtonsBox(list_to_texts, title=title, label=label, parent=self, width=width)
        bb.wait_window()
        if bb.return_data is None:
            return None
        return list_to_texts[bb.return_data]


if __name__ == '__main__':
    app = UITkinter()
    app.mainloop()
