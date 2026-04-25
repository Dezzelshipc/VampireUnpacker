import json

from Source.Utility.constants import TRANSLATIONS_FOLDER, VAMPIRE_CRAWLERS, GENERATED
from Source.Utility.unity_parser import UnityDoc

SHARED_DATA = "Shared Data"


def gen_main_langs():
    folder = TRANSLATIONS_FOLDER / VAMPIRE_CRAWLERS

    files = list(folder.glob("*.asset"))

    types = [file for file in files if file.stem.endswith(SHARED_DATA)]
    # .stem.replace(SHARED_DATA, "").strip()

    types_dict = {
        t: [file for file in files if
            t.stem.replace(SHARED_DATA, "").strip() in file.stem and SHARED_DATA not in file.stem]
        for t in types
    }

    save_folder = folder / GENERATED

    for keys_data_path, langs_data_paths in types_dict.items():
        t = keys_data_path.stem.replace(SHARED_DATA, "").strip()
        keys_data = UnityDoc.yaml_parse_file_smart(keys_data_path).entry.data['m_Entries']
        keys_data = {data['m_Id']: data['m_Key'] for data in keys_data}

        langs_data = {"en": [{}]}
        langs_data.update({
            p.stem.replace(f"{t}_", ""): UnityDoc.yaml_parse_file_smart(p).entry.data['m_TableData']
            for p in langs_data_paths
        })
        langs_data = {
            lang: {data['m_Id']: data['m_Localized'] for data in lang_data}
            for lang, lang_data in langs_data.items()
        }

        full_data = {
            key: {
                lang: data.get(_id)
                for lang, data in langs_data.items()
            }
            for _id, key in keys_data.items()
        }

        sf = save_folder / "LangDictionary"
        sf.mkdir(parents=True, exist_ok=True)

        with open(sf / f"{t}.json", mode="w", encoding="UTF-8") as f:
            f.write(json.dumps(full_data, ensure_ascii=False, indent=2))

        1

    pass


if __name__ == "__main__":
    gen_main_langs()
