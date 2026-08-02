from os import PathLike
from pathlib import Path
from typing import Iterable

from Source.Config.config import Config, DLCType, CfgKey
from Source.Data import game_version
from Source.Data.meta_data import MetaDataHandler
from Source.Utility.constants import to_source_path, IMAGES_FOLDER


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

    def progress_bar_set_percent(self, current: int | float, total: int | float, add_text: str = "") -> None:
        raise NotImplementedError()

    def progress_bar_set_sec(self, seconds: float, add_text: str = "") -> None:
        raise NotImplementedError()

    def check_boxes(self, list_to_boxes, title="", label: str | list[str] = "", width: int = 300) -> list[...]:
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