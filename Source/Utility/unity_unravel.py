from itertools import cycle

from Source.Data.unity_data import UnityDataHandler
from Source.Utility.unity_parser import UnityEntry, UnityDoc, UnityReference
from Source.Data.meta_data import MetaDataHandler, MetaData
from Source.Utility.constants import SPRITE_FILE_IDS
from Source.Utility.multirun import run_multiprocess, run_concurrent_async, run_concurrent_sync, run_multiprocess_single


def _get_data(_data) -> set[UnityReference]:
    if isinstance(_data, UnityReference):
        if _data.is_valid():
            return {_data}
    elif isinstance(_data, UnityEntry):
        return _get_data(_data.data)
    elif isinstance(_data, UnityDoc):
        return {obj for entry in _data.entries for obj in _get_data(entry)}
    elif isinstance(_data, dict):
        return {obj for k, v in _data.items() for obj in _get_data(v)}
    elif isinstance(_data, list):
        return {obj for v in _data for obj in _get_data(v)}

    return set()


def _make_data(_data, guid_docs: dict[str, UnityDoc]):
    if isinstance(_data, UnityReference):
        if _data.is_valid():
            return guid_docs.get(_data.guid) or _data
    elif isinstance(_data, UnityEntry):
        return _data.with_data(_make_data(_data.data, guid_docs))
    elif isinstance(_data, UnityDoc):
        return UnityDoc([_make_data(entry, guid_docs) for entry in _data.entries], guid=_data.guid)
    elif isinstance(_data, dict):
        return {
            k: _make_data(v, guid_docs)
            for k, v in _data.items()
        }
    elif isinstance(_data, list):
        return [_make_data(v, guid_docs) for v in _data]

    return _data


def _unity_unravel_entry(entry: UnityEntry, guid_docs: dict[str, UnityDoc]) -> UnityEntry:
    return entry.with_data(_make_data(entry.data, guid_docs))


def unity_unravel_doc(unity_doc: UnityDoc, depth: int = 1) -> UnityDoc:
    _unity_doc = unity_doc

    guid_docs: dict[str, UnityDoc | MetaData] = {}

    for d in range(depth):
        unity_refs = {guid for g_list in run_multiprocess_single(_get_data, [e.data for e in _unity_doc.entries]) for guid in
                 g_list}

        assets = {ref.guid for ref in unity_refs if ref.fileID not in SPRITE_FILE_IDS}
        sprites = {ref.guid for ref in unity_refs if ref.fileID in SPRITE_FILE_IDS}

        print(f"Unraveling UnityDoc. Depth: {d} (Assets to parse: {len(assets)}, Sprites to parse: {len(sprites)})")

        docs = UnityDataHandler.get_data_dict_by_guid_set(assets)
        guid_docs.update(docs)
        metas = MetaDataHandler.get_meta_dict_by_guid_set(sprites)
        guid_docs.update(metas)

        args = zip(_unity_doc.entries, cycle((guid_docs,)))

        _unity_doc.entries = run_multiprocess(_unity_unravel_entry, args)

    return _unity_doc


if __name__ == "__main__":
    from Source.Config.config import Game

    MetaDataHandler.load(Game.VC)

    db_name = "EnemyDatabase"
    # db_name = "AllDecks"

    path = MetaDataHandler.get_path_by_name_no_meta(db_name)


    doc = UnityDoc.yaml_parse_file_smart(path)
    # print(doc)

    udoc = unity_unravel_doc(doc, depth=3)

    print(udoc)
