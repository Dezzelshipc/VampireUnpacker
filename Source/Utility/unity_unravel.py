from Source.Utility.unity_parser import UnityEntry, UnityDoc, UnityReference
from Source.Data.meta_data import MetaDataHandler


def _make_data(_data, depth: int):
    if isinstance(_data, UnityReference):
        if _data.is_valid():
            _path = MetaDataHandler.get_path_by_guid_no_meta(_data.guid)
            if _path:
                _doc = UnityDoc.yaml_parse_file_smart(_path)
                return unity_unravel_doc(_doc, depth - 1)
    elif isinstance(_data, dict):
        return {
            k: _make_data(v, depth)
            for k, v in _data.items()
        }
    elif isinstance(_data, list):
        return [_make_data(v, depth) for v in _data]

    return _data


def unity_unravel_entry(entry: UnityEntry, depth: int = 1) -> UnityEntry:
    if depth <= 0:
        return entry

    data = _make_data(entry.data, depth)
    return entry.with_data(data)


def unity_unravel_doc(unity_doc: UnityDoc, depth: int = 1) -> UnityDoc:
    return UnityDoc([unity_unravel_entry(e, depth) for e in unity_doc.entries])


if __name__ == "__main__":
    from Source.Config.config import Game

    MetaDataHandler.load(Game.VC)

    # db_name = "EnemyDatabase"
    db_name = "AllDecks"

    name, path = list(MetaDataHandler.filter_paths(lambda name_path: db_name.lower() in name_path[0].lower()))[0]

    doc = UnityDoc.yaml_parse_file_smart(path.with_suffix(""))
    print(doc)

    udoc = unity_unravel_doc(doc, depth=2)
    print(udoc)
