import json
from enum import Enum

from Source.Config.config import Game
from Source.Data.meta_data import MetaDataHandler
from Source.Utility.unity_parser import UnityDoc
from Source.Utility.unity_unravel import unity_unravel_doc
from Utility.constants import ROOT_FOLDER, VAMPIRE_CRAWLERS


class DataTypeVC(Enum):
    ENEMY = "EnemyDatabase"

    NONE = None

    def get_dumper(self) -> "BaseDataDumper".__class__:
        match self:
            case DataTypeVC.ENEMY:
                return EnemyDataDumper
            case _:
                return BaseDataDumper


class BaseDataDumper:
    _type: DataTypeVC = DataTypeVC.NONE

    @classmethod
    def dump_data(cls):
        assert False, "Data dumper not specified or supported"


class EnemyDataDumper(BaseDataDumper):
    _type = DataTypeVC.ENEMY

    @classmethod
    def dump_data(cls):
        path = MetaDataHandler.get_path_by_name_no_meta(cls._type.value)
        doc = UnityDoc.yaml_parse_file_smart(path)
        udoc = unity_unravel_doc(doc, depth=2)

        full_data: dict[str, dict] = {}

        for enemy_config in udoc.entry.data['_assetList']:
            data: dict = enemy_config.entry.data
            name = data['m_Name'].replace('EnemyConfig_', '')

            keys = data.keys()
            keys = filter(lambda k: not k.startswith("m_"), keys)
            keys = filter(lambda k: k not in [
                'serializationData', '<AssetId>k__BackingField', 'AllowInTemplate',
                'Prefab', '_idleAnimation', '_deathAnimation', '_spriteMaterial', '_spriteMaterialFar',
                'OutlineColor', '_audioData', '_enableSeparateShadow',
            ], keys)

            data_taken = {k: data.get(k) for k in keys}
            data_taken['_dungeonTags'] = [dt.entry.data['_assetId'] for dt in data_taken['_dungeonTags']]
            data_taken['_enemyTypeTags'] = [et.entry.data['_typeName'] for et in data_taken['_enemyTypeTags']]

            full_data[name] = data_taken

        save_path = ROOT_FOLDER / "Data" / VAMPIRE_CRAWLERS
        with open(save_path / f"{cls._type.value}.json", "w") as f:
            f.write(json.dumps(full_data, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    MetaDataHandler.load(Game.VC)
    EnemyDataDumper.dump_data()
