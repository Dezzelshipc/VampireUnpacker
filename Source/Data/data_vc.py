import json
from enum import Enum

from Source.Config.config import Game
from Source.Data.meta_data import MetaDataHandler
from Source.Utility.unity_parser import UnityDoc
from Source.Utility.unity_unravel import unity_unravel_doc
from Utility.constants import ROOT_FOLDER, VAMPIRE_CRAWLERS


class DataTypeVC(Enum):
    ENEMY = "EnemyDatabase"
    COFFIN_GUARDIAN = "GuardianEncounterDatabase"
    REWARD_CONFIG = "RewardConfig_Default"

    ### Unused
    _AchievementCD = "AchievementConfigDatabase"
    _ArcanaCD = "ArcanaConfigDatabase"
    _CardD = "CardDatabase"
    _CardGD = "CardGroupDatabase"
    _CardTD = "CardTypeDatabase"
    _DungeonED = "DungeonEventDatabase"
    _DungeonTD = "DungeonTagDatabase"
    _EncounterD = "EncounterDatabase"
    _EncounterTD = "EncounterTemplateDatabase"
    _EventDD = "EventDetailsDatabase"
    _FccD = "FccDatabase"
    _GemD = "GemDatabase"
    _DemTD = "GemTagDatabase"
    _MapTileDD = "MapTileDefinitionDatabase"
    _PassiveED = "PassiveEventDatabase"
    _PowerUpD = "PowerUpDatabase"
    _PropDD = "PropDefinitionDatabase"  # '_assetReference'
    _RelicD = "RelicDatabase"
    _RoomTD = "RoomTemplateDatabase"  # '_assetReference'
    _TownBD = "TownBuildingDatabase"

    _AllDecks = "AllDecks"  # Not full list of decks
    _AllDungeons = "AllDungeons"

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

    @classmethod
    def get_udoc(cls, depth: int):
        path = MetaDataHandler.get_path_by_name_no_meta(cls._type.value)
        doc = UnityDoc.yaml_parse_file_smart(path)
        return unity_unravel_doc(doc, depth=depth)

    @classmethod
    def save_data(cls, full_data: dict | list):
        save_path = ROOT_FOLDER / "Data" / VAMPIRE_CRAWLERS
        with open(save_path / f"{cls._type.value}.json", "w") as f:
            f.write(json.dumps(full_data, indent=4, ensure_ascii=False))


class EnemyDataDumper(BaseDataDumper):
    _type = DataTypeVC.ENEMY

    @classmethod
    def format_data(cls, enemy_config: UnityDoc) -> tuple[str, dict]:
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

        return name, data_taken

    @classmethod
    def dump_data(cls):
        udoc = cls.get_udoc(2)

        full_data: dict[str, dict] = {}

        for enemy_config in udoc.entry.data['_assetList']:
            name, data_taken = cls.format_data(enemy_config)
            full_data[name] = data_taken

        cls.save_data(full_data)


# class DeckDataDumper(BaseDataDumper):
#     _type = DataTypeVC.DECK
#
#     @classmethod
#     def dump_data(cls):
#         udoc = cls.get_udoc(2)
#
#         full_data: dict[str, list[str]] = {}
#
#         for deck_config in udoc.entry.data['_assetList']:
#             data: dict = deck_config.entry.data
#             name = data['deckName']
#
#             full_data[name] = [card_config['cardConfig'].entry.data['m_Name'] for card_config in data['cards']]
#
#         cls.save_data(full_data)


class CoffinGuardianDataDumper(BaseDataDumper):
    _type = DataTypeVC.COFFIN_GUARDIAN

    @classmethod
    def format_data(cls, guardian_config: UnityDoc) -> tuple[str, dict]:
        data: dict = guardian_config.entry.data
        name = data['_assetId']

        keys = data.keys()
        keys = filter(lambda k: not k.startswith("m_"), keys)
        keys = filter(lambda k: k not in [
            'serializationData', '_destructiblePropDefinition', '_overriddenCameraSettings', '_edgeEventBumpSFX',
            'unlockedAchievement', 'guardianPulseCurve',
        ], keys)

        data_taken = {k: data.get(k) for k in keys}
        data_taken['_treasureEventDetailsReference'] = data['_treasureEventDetailsReference'].get('_assetId')
        data_taken['_defaultEventDetailsReference'] = data['_defaultEventDetailsReference']["_assetId"]
        name_guardian, config_guardian = EnemyDataDumper.format_data(data_taken['guardian'])
        config_guardian["__name"] = name_guardian
        data_taken['guardian'] = config_guardian
        if isinstance(ach_doc := data.get('unlockedAchievement'), UnityDoc):
            data_taken['unlockedAchievement'] = ach_doc.entry.data['m_Name']

        return name, data_taken

    @classmethod
    def dump_data(cls):
        udoc = cls.get_udoc(3)

        full_data: dict[str, dict] = {}

        for guardian_config in udoc.entry.data['_assetList']:
            name, data_taken = cls.format_data(guardian_config)
            full_data[name] = data_taken

        cls.save_data(full_data)


class RewardConfigDataDumper(BaseDataDumper):
    _type = DataTypeVC.REWARD_CONFIG

    @classmethod
    def dump_data(cls):
        udoc = cls.get_udoc(2)

        full_data: list[dict] = []

        for reward_config in udoc.entry.data['_levelRanges']:
            data_taken = reward_config
            data_taken['_cards'] = [card_doc.entry.data['m_Name'] for card_doc in data_taken['_cards']]
            data_taken['_cardGroups'] = [card_doc.entry.data['_assetId'] for card_doc in data_taken['_cardGroups']]

            full_data.append(data_taken)

        cls.save_data(full_data)


if __name__ == "__main__":
    MetaDataHandler.load(Game.VC)
    RewardConfigDataDumper.dump_data()
