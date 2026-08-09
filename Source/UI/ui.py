from os import PathLike
from pathlib import Path
from typing import Iterable, Any

from Source.Config.config import Config, DLCType, CfgKey, Game
from Source.Data import game_version, data_vc
from Source.Data.meta_data import MetaDataHandler, to_current_game_path
from Source.Images import transparent_save
from Source.Images.image_gen_general import generate_images_by_meta, generate_animation_by_meta
from Source.Translations import language_vc
from Source.Utility.constants import to_source_path, IMAGES_FOLDER, GENERATED, COMPOUND_DATA_TYPE, COMPOUND_DATA, \
    DEFAULT_ANIMATION_FRAME_RATE
from Source.Utility.popups import ErrorPopup, BasePopup, InfoPopup, WarningPopup


class UIBase:
    def __init__(self):
        self._title_text = 'Vampire Unpacker'
        self._icon_path = to_source_path(IMAGES_FOLDER) / "Show" / "_Sprite-Atlas Gate.png"

        self._last_loaded_folder: Path | None = None

    @staticmethod
    def ask_open_file_name(title: str = "Select file", initialdir: set | PathLike[str] = None,
                           filetypes: Iterable[tuple[str, str | list[str]]] = None) -> Path | None:
        raise NotImplementedError()

    @staticmethod
    def ask_open_file_names(title: str = "Select file", initialdir: set | PathLike[str] = None,
                            filetypes: Iterable[tuple[str, str | list[str]]] = None) -> Iterable[Path] | None:
        raise NotImplementedError()

    @staticmethod
    def ask_yes_no(title: str = None, message: str = None, **options) -> bool:
        raise NotImplementedError()

    @staticmethod
    def ask_integer(title: str = None,
                    prompt: str = None,
                    *,
                    initialvalue: int = None,
                    minvalue: int = None,
                    maxvalue: int = None,
                    **options) -> int:
        raise NotImplementedError()

    @staticmethod
    def show_info(title: str = None, message: str = None, **options) -> None:
        raise NotImplementedError()

    @staticmethod
    def show_warning(title: str = None, message: str = None, **options) -> None:
        raise NotImplementedError()

    @staticmethod
    def show_error(title: str = None, message: str = None, **options) -> None:
        raise NotImplementedError()

    def show_popup(self, popup: BasePopup) -> None:
        match popup:
            case InfoPopup(t, m):
                self.show_info(t, m)
            case WarningPopup(t, m):
                self.show_warning(t, m)
            case ErrorPopup(t, m):
                self.show_error(t, m)

    def progress_bar_set_percent(self, current: int | float, total: int | float, add_text: str = "") -> None:
        raise NotImplementedError()

    def progress_bar_set_sec(self, seconds: float, add_text: str = "") -> None:
        raise NotImplementedError()

    def check_boxes(self, list_to_boxes, title="", label: str | list[str] = "", width: int = 300) -> list[bool]:
        raise NotImplementedError()

    def buttons_box(self, list_to_texts, title="", label: str | list[str] = "", width: int = 300) -> Any:
        raise NotImplementedError()

    def open_last_loaded_folder(self) -> None:
        raise NotImplementedError()

    def change_config(self) -> None:
        raise NotImplementedError()

    ###
    def rip_data(self) -> None:
        if not Config[CfgKey.RIPPER]:
            self.show_error("Error", "Not found path to AssetRipper")
            return

        dlc_types_list = []
        for d in DLCType.get_all_types():
            if Config[d.value.config_key]:
                dlc_types_list.append(d)

        data_from_popup = self.check_boxes(dlc_types_list, label="Select DLCs to rip", title="Select DLCs")
        if not data_from_popup:
            return

        dlc_types_set = {t for i, t in enumerate(dlc_types_list) if data_from_popup[i]}
        if not dlc_types_set:
            return

        print(f"Started ripping files: {dlc_types_set}")
        from Source.Ripper.ripper import rip_files
        rip_files(dlc_types_set, self.__class__)

        print("Finished ripping files")
        MetaDataHandler.unload()

    @staticmethod
    def get_assets_dir(key: DLCType = DLCType.VS) -> Path:
        path = Config.get_assets_dir(key)
        return path.exists() and path or Path()

    @staticmethod
    def create_version_file():
        game_version.load_version_file()

    def dlc_selector(self, allow_compound: bool = False, parent=None) -> DLCType | COMPOUND_DATA_TYPE | None:
        all_dlcs = DLCType.get_all_types()
        compound = repr(COMPOUND_DATA)
        if allow_compound:
            all_dlcs.append(compound)

        ret = self.buttons_box(all_dlcs, "Select DLC", "Select DLC from which data file will be selected", parent)

        return COMPOUND_DATA if ret == compound else ret

    def unpack_by_meta_from_spritesheets(self, generate_function):
        folder = self.get_assets_dir().joinpath("Resources", "spritesheets")

        if not folder.exists():
            self.show_warning("Warning", "Spritesheets folder does not found.")
            return

        self.generate_by_meta_selector(folder, generate_function)

    def unpack_by_meta(self, generate_function):
        selected_dlc = self.dlc_selector()
        if not selected_dlc:
            return

        _start_path = self.get_assets_dir(selected_dlc)
        start_paths = [_start_path.joinpath("Texture2D"), _start_path]

        while (start_path := start_paths.pop(0)) and not start_path.exists():
            pass

        if not start_paths:
            self.show_warning("Warning", "Assets folder not found.")
            return

        self.generate_by_meta_selector(start_path, generate_function)

    def generate_by_meta_selector(self, selecting_path: Path, generate_function):
        filetypes = [
            ('Images', '*.png')
        ]

        full_path = self.ask_open_file_name(
            title='Select a file',
            initialdir=selecting_path,
            filetypes=filetypes
        )

        if not full_path:
            return

        generate_function(Path(full_path))

    def generate_images_by_meta(self, full_path: Path):
        scale_factor = self.ask_integer("Scale", "Input scale multiplier", initialvalue=1)
        if not scale_factor or scale_factor <= 0: return

        try:
            llf = generate_images_by_meta(
                full_path,
                scale_factor=scale_factor,
                func_progress_bar_set_percent=self.progress_bar_set_percent)
            if llf:
                self._last_loaded_folder = llf
        except BasePopup as p:
            self.show_popup(p)

    def generate_animation_by_meta(self, full_path: Path):
        scale_factor = self.ask_integer("Scale", "Input scale multiplier", initialvalue=1)
        if not scale_factor or scale_factor <= 0: return

        frame_rate = self.ask_integer("Frame rate", "Input frame rate (frames per second)",
                                      initialvalue=DEFAULT_ANIMATION_FRAME_RATE)
        if not frame_rate or frame_rate <= 0: return

        selected_anim_types = self.check_boxes(
            transparent_save.ANIM_SAVE_TYPES,
            label="Select animation extension to use.\n(GIF does not support partial transparency)",
            title="Select anim types")

        try:
            llf = generate_animation_by_meta(
                full_path,
                scale_factor=scale_factor,
                frame_rate=frame_rate,
                selected_anim_types=selected_anim_types,
                func_progress_bar_set_percent=self.progress_bar_set_percent)
            if llf:
                self._last_loaded_folder = llf
        except BasePopup as p:
            self.show_popup(p)

    def get_languages_vs_all(self):
        self._last_loaded_folder = language_vc.save_all_langs(self.progress_bar_set_percent)

    def get_data_vc_all(self):
        dumpers = data_vc.get_available_dumpers()
        selected = self.check_boxes([d.data_type.value for d in dumpers], title="Select data to dump",
                                    label="Select data to dump")

        if selected is None or not any(selected): return

        self._last_loaded_folder = data_vc.dump_selected_data(selected, self.progress_bar_set_percent)

        data_vc.make_meta_file_folder_structure()
