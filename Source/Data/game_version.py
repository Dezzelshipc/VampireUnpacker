import shutil
import sys

from Source.Config.config import PROJECT_SETTINGS, Game, DLCType, Config
from Source.Data.meta_data import MetaDataHandler
from Source.Utility.constants import VERSION_DATA, VAMPIRE_SURVIVORS
from Source.Utility.unity_parser import UnityDoc


def get_game_bundle_version() -> str | None:
    MetaDataHandler.assert_loaded_game()

    proj_settings = MetaDataHandler.get_path_by_name_no_meta(PROJECT_SETTINGS)
    if not proj_settings:
        return None

    doc = UnityDoc.yaml_parse_file_smart(proj_settings)
    if not doc:
        return None

    return doc.entry.data['bundleVersion']


def get_game_build_version() -> tuple[str | None, str | None]:
    MetaDataHandler.assert_loaded_game()

    version_data = MetaDataHandler.get_path_by_name_no_meta(VERSION_DATA)
    if not version_data:
        return None, None

    doc = UnityDoc.yaml_parse_file_smart(version_data)
    if not doc:
        return None, None

    data = doc.entry.data
    return data['_BuildId'], data['_BuildTime']

def get_dlc_version() -> list[tuple[DLCType, str, str]]:
    MetaDataHandler.assert_loaded_game()

    assets = []
    match MetaDataHandler.loaded_game:
        case Game.VS:
            assets = [
                (DLCType.MS, "Moonspell"),
                (DLCType.FS, "Foscari"),
                (DLCType.EM, "Chalcedony"),
                (DLCType.OG, "FirstBlood"),
                (DLCType.OC, "ThosePeople"),
                (DLCType.ED, "Emeralds"),
                (DLCType.AC, "Lemon"),
            ]
        case Game.VC:
            pass ## Not implemented; not any DLC yet

    result = []
    for dlc, asset in assets:
        bundle = MetaDataHandler.get_path_by_name_no_meta_suffixes(asset, 'asset')
        if not bundle:
            print(f"Not found asset ({asset}) for DLC ({dlc})", file=sys.stderr)
            continue

        doc = UnityDoc.yaml_parse_file(bundle)
        data = doc.entry.data

        result.append((dlc, data['_Title'], data['_ExpectedVersion']))

    return result


def load_version_file():
    MetaDataHandler.assert_loaded_game()

    data_folder_key = MetaDataHandler.loaded_game.get_data_folder_key()
    Config.assert_key(data_folder_key)
    data_folder = Config[data_folder_key]

    match MetaDataHandler.loaded_game:
        case Game.VS:
            game_version = get_game_bundle_version()
            build_num, build_time = get_game_build_version()
            dlc_list = get_dlc_version()

            text = ""
            for dlc, name, version in dlc_list:
                text += f"{name} - {version}\n"
            text = f"{VAMPIRE_SURVIVORS} - {game_version}\n" + text
            text += f"{build_time} [{build_num}R]"

            with open(data_folder / 'Game Version.txt', 'w') as f:
                print(text, file=f)
        case Game.VC:
            build_info = MetaDataHandler.get_path_by_name_no_meta_suffixes("BuildInfo", 'txt')
            if not build_info:
                return None

            shutil.copy(build_info, data_folder / 'Game Version.txt')

    return None


if __name__ == "__main__":
    # MetaDataHandler.load(Game.VS)
    MetaDataHandler.load(Game.VC)

    load_version_file()
