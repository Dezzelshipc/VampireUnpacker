import itertools
import json
import sys
from enum import Enum
from itertools import cycle

from Source.Config.config import Game
from Source.Data.meta_data import MetaDataHandler
from Source.Utility.unity_parser import UnityDoc
from Source.Utility.unity_unravel import unity_unravel_doc
from Utility.constants import ROOT_FOLDER, VAMPIRE_CRAWLERS
from Utility.multirun import run_concurrent_sync
from Utility.unity_parser import UnityReference


class DataTypeVC(Enum):
    ENEMY = "EnemyDatabase"
    DECK = "AllDecks"  # Not full list of decks
    CARD = "CardDatabase"
    POWER_UP = "PowerUpDatabase"
    RELIC = "RelicDatabase"
    DUNGEON = "AllDungeons"

    TOWN_BUILDING = "TownBuildingDatabase"

    ACHIEVEMENT_CONFIG = "AchievementConfigDatabase"
    GUARDIAN_COFFIN = "GuardianEncounterDatabase"
    REWARD_CONFIG = "RewardConfig_Default"
    LEVEL_CONFIG = "PlayerLevelConfig"
    PLAYER_CONFIG = "PlayerConfig"

    ### Unused
    _ARCANA_CONFIG = "ArcanaConfigDatabase"
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
    _PropDD = "PropDefinitionDatabase"  # '_assetReference'
    _RoomTD = "RoomTemplateDatabase"  # '_assetReference'

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
        return unity_unravel_doc(doc, depth=depth, is_load_sprites=False)

    @staticmethod
    def get_m_Name(doc: UnityDoc | UnityReference | None) -> str | None:
        if doc is None:
            return None
        elif isinstance(doc, UnityDoc):
            return doc.entry.data.get("m_Name")
        elif not doc.is_valid():
            return None
        _text = f"{doc} not dereferenced"
        print(_text, file=sys.stderr)
        return _text

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


class DeckDataDumper(BaseDataDumper):
    _type = DataTypeVC.DECK

    @classmethod
    def get_udoc(cls, depth: int):
        assert False, f"Unsupported function. Use {cls.__class__.__name__}.get_deck_udocs(depth)"

    @classmethod
    def get_deck_udocs(cls, depth: int, verbose: int = 0) -> list[UnityDoc]:
        paths = MetaDataHandler.filter_paths(lambda name_path: name_path[0].endswith('deck'))
        docs = run_concurrent_sync(UnityDoc.yaml_parse_file_smart, (p.with_suffix("") for n, p in paths))
        return run_concurrent_sync(unity_unravel_doc, zip(docs, cycle((depth,)), cycle((verbose,))))

    @classmethod
    def dump_data(cls):
        udocs = cls.get_deck_udocs(2)
        udocs.sort(key=lambda d: cls.get_m_Name(d))

        full_data: dict[str, list[str]] = {}

        for deck_config in udocs:
            data: dict = deck_config.entry.data
            name = data['deckName']

            if name in full_data:
                name += "_" + data['m_Name']
            full_data[name] = [cls.get_m_Name(card_config) for card_config in data['cards']]

        cls.save_data(full_data)


class CardDataDumper(BaseDataDumper):
    _type = DataTypeVC.CARD

    @classmethod
    def format_data(cls, card_config: UnityDoc) -> tuple[str, dict]:
        data: dict = card_config.entry.data

        keys = data.keys()
        keys = filter(lambda k: not k.startswith("m_"), keys)
        keys = filter(lambda k: k not in [
            'serializationData',
            # TODO: lang file support
            'cardName', 'cardDescription', 'levelZeroDescription', '_additionalOnPlayDescription',
            'sprites', 'references',
        ], keys)

        data_taken = {k: data.get(k) for k in keys}

        data_taken['cardType'] = cls.get_m_Name(data_taken['cardType'])
        data_taken['cardGroup'] = cls.get_m_Name(data_taken['cardGroup'])

        data_taken['_evolutionComponents'] = [cls.get_m_Name(d) for d in data_taken['_evolutionComponents']]
        data_taken['_excludeGemTags'] = [cls.get_m_Name(d) for d in data_taken['_excludeGemTags']]
        data_taken['_excludeGemTagGroups'] = [cls.get_m_Name(d) for d in data_taken['_excludeGemTagGroups']]

        return cls.get_m_Name(card_config), data_taken

    @classmethod
    def dump_data(cls):
        udoc = cls.get_udoc(2)

        full_data: dict[str, dict] = {}

        for card_config in itertools.chain(udoc.entry.data['_assetList'], [udoc.entry.data['_cursedLancet']]):
            name, data_taken = cls.format_data(card_config)
            full_data[name] = data_taken

        cls.save_data(full_data)


class CoffinGuardianDataDumper(BaseDataDumper):
    _type = DataTypeVC.GUARDIAN_COFFIN

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
            data_taken['unlockedAchievement'] = cls.get_m_Name(ach_doc)

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
            data_taken['_cards'] = [cls.get_m_Name(card_doc) for card_doc in data_taken['_cards']]
            data_taken['_cardGroups'] = [card_doc.entry.data['_assetId'] for card_doc in data_taken['_cardGroups']]

            full_data.append(data_taken)

        cls.save_data(full_data)


class LevelConfigDataDumper(BaseDataDumper):
    _type = DataTypeVC.LEVEL_CONFIG

    @classmethod
    def dump_data(cls):
        udoc = cls.get_udoc(0)

        full_data = {
            k: v
            for k, v in udoc.entry.data.items()
            if k in ['_baseXpReq', '_levelRanges']
        }

        cls.save_data(full_data)


class PlayerConfigDataDumper(BaseDataDumper):
    _type = DataTypeVC.PLAYER_CONFIG

    @classmethod
    def dump_data(cls):
        udoc = cls.get_udoc(0)

        data = udoc.entry.data

        keys = data.keys()
        keys = filter(lambda k: not k.startswith("m_"), keys)
        keys = filter(lambda k: k not in [
            '_playerAudioConfig'
        ], keys)

        full_data = {k: data.get(k) for k in keys}

        cls.save_data(full_data)


class AchievementDataDumper(BaseDataDumper):
    _type = DataTypeVC.ACHIEVEMENT_CONFIG

    @classmethod
    def format_data(cls, ach_config: UnityDoc) -> tuple[str, dict]:
        data: dict = ach_config.entry.data

        keys = data.keys()
        keys = filter(lambda k: not k.startswith("m_"), keys)
        keys = filter(lambda k: k not in {
            'serializationData',
            # TODO: lang file support
            '_achievementName', '_achievementDescription', '_platformTrophyDescription',
            '_unlockRewardIcon', '_rewardName', '_rewardDescription',
            '_hiddenString', '_flavourText',
            'references',
        }, keys)

        data_taken = {k: data.get(k) for k in keys}

        data_taken['_dungeonConfig'] = cls.get_m_Name(data_taken.get('_dungeonConfig'))
        data_taken['_fccConfig'] = cls.get_m_Name(data_taken.get('_fccConfig'))
        data_taken['_encounterConfig'] = cls.get_m_Name(data_taken.get('_encounterConfig'))
        data_taken['_powerUpConfig'] = cls.get_m_Name(data_taken.get('_powerUpConfig'))

        data_taken['_achievementsRequired'] = [cls.get_m_Name(d) for d in data_taken.get('_achievementsRequired', [])]

        if '_criteriasToMeet' in data_taken:
            for ci in data_taken['_criteriasToMeet']:
                ci['FccToCheck'] = cls.get_m_Name(ci['FccToCheck'])
        else:
            data_taken['_criteriasToMeet'] = []

        return cls.get_m_Name(ach_config), data_taken

    @classmethod
    def dump_data(cls):
        udoc = cls.get_udoc(2)

        full_data: dict[str, dict] = {}

        for ach_config in udoc.entry.data['_assetList']:
            name, data_taken = cls.format_data(ach_config)
            full_data[name] = data_taken

        cls.save_data(full_data)


class PowerUpDataDumper(BaseDataDumper):
    _type = DataTypeVC.POWER_UP

    @classmethod
    def format_data(cls, power_up_config: UnityDoc) -> tuple[str, dict]:
        data: dict = power_up_config.entry.data

        keys = data.keys()
        keys = filter(lambda k: not k.startswith("m_"), keys)
        keys = filter(lambda k: k not in {
            'serializationData', 'imageSprite',
            # TODO: lang file support
            'itemName', 'description',
            'references',
        }, keys)

        data_taken = {k: data.get(k) for k in keys}

        return cls.get_m_Name(power_up_config), data_taken

    @classmethod
    def dump_data(cls):
        udoc = cls.get_udoc(2)

        full_data: dict[str, dict] = {}

        for power_up_config in udoc.entry.data['_assetList']:
            name, data_taken = cls.format_data(power_up_config)
            full_data[name] = data_taken

        cls.save_data(full_data)


class RelicDataDumper(BaseDataDumper):
    _type = DataTypeVC.RELIC

    @classmethod
    def format_data(cls, relic_config: UnityDoc) -> tuple[str, dict]:
        data: dict = relic_config.entry.data

        keys = data.keys()
        keys = filter(lambda k: not k.startswith("m_"), keys)
        keys = filter(lambda k: k not in {
            'serializationData', 'imageSprite',
            # TODO: lang file support
            'LocalizedName', '_localizedDescription',
            'IconSprite',
            'references',
        }, keys)

        data_taken = {k: data.get(k) for k in keys}

        return cls.get_m_Name(relic_config), data_taken

    @classmethod
    def dump_data(cls):
        udoc = cls.get_udoc(2)

        full_data: dict[str, dict] = {}

        for relic_config in udoc.entry.data['_assetList']:
            name, data_taken = cls.format_data(relic_config)
            full_data[name] = data_taken

        cls.save_data(full_data)


class DungeonsDataDumper(BaseDataDumper):
    _type = DataTypeVC.DUNGEON

    @classmethod
    def format_data(cls, dungeon_config: UnityDoc) -> tuple[str, dict]:
        data: dict = dungeon_config.entry.data

        keys = data.keys()
        keys = filter(lambda k: not k.startswith("m_"), keys)
        keys = filter(lambda k: k not in {
            'serializationData', 'references',
            # TODO: lang file support
            '<DungeonNameLoc>k__BackingField', '<DungeonDescriptionLoc>k__BackingField',
            '_dungeonThumbnailSprite', '_soundGroupCreator', '_reverbZonePrefab',
        }, keys)

        data_taken = {k: data.get(k) for k in keys}

        data_taken['GenerationConfig'] = cls.get_m_Name(data_taken.get('GenerationConfig'))  ## ?

        data_taken['_cameraVolumeProfile'] = cls.get_m_Name(data_taken.get('_cameraVolumeProfile'))
        data_taken['_skyboxMaterial'] = cls.get_m_Name(data_taken.get('_skyboxMaterial'))
        data_taken['_traversalBGM'] = cls.get_m_Name(data_taken.get('_traversalBGM'))
        data_taken['_battleBGM'] = cls.get_m_Name(data_taken.get('_battleBGM'))

        data_taken['_relicsInLevel'] = [cls.get_m_Name(d) for d in data_taken.get('_relicsInLevel', [])]
        data_taken['_coffinsInLevel'] = [cls.get_m_Name(d) for d in data_taken.get('_coffinsInLevel', [])]

        return cls.get_m_Name(dungeon_config), data_taken

    @classmethod
    def dump_data(cls):
        udoc = cls.get_udoc(2)

        full_data: dict[str, dict] = {}

        for dungeon_config in udoc.entry.data['_assetList']:
            name, data_taken = cls.format_data(dungeon_config)
            full_data[name] = data_taken

        cls.save_data(full_data)


class TownBuildingDataDumper(BaseDataDumper):
    _type = DataTypeVC.TOWN_BUILDING

    @classmethod
    def format_data(cls, dungeon_config: UnityDoc) -> tuple[str, dict]:
        data: dict = dungeon_config.entry.data

        keys = data.keys()
        keys = filter(lambda k: not k.startswith("m_"), keys)
        keys = filter(lambda k: k not in {
            'serializationData', 'references',
            # TODO: lang file support
            '_townBuildingName', '_menuName', '_unlockedBuildingDesc', '_lockedBuildingDesc',

        }, keys)

        data_taken = {k: data.get(k) for k in keys}

        data_taken['_musicOverride'] = cls.get_m_Name(data_taken.get('_musicOverride'))

        return cls.get_m_Name(dungeon_config), data_taken

    @classmethod
    def dump_data(cls):
        udoc = cls.get_udoc(2)

        full_data: dict[str, dict] = {}

        for dungeon_config in udoc.entry.data['_assetList']:
            name, data_taken = cls.format_data(dungeon_config)
            full_data[name] = data_taken

        cls.save_data(full_data)


if __name__ == "__main__":
    MetaDataHandler.load(Game.VC)
    TownBuildingDataDumper.dump_data()
