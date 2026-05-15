from enum import Enum

from Source.Utility.constants import SHARED_DATA


class Lang(Enum):
    EN = "en"  # s c
    FR = "fr"  # s c
    IT = "it"  # s c
    DE = "de"  # s c
    ES = "es"  # s c
    PT_BR = "pt-BR"  # s c
    PL = "pl"  # s c
    RU = "ru"  # s c
    JA = "ja"  # s c
    KO = "ko"  # s c
    TR = "tr"  # s
    UK = "uk"  # s

    ## Traditional (both)
    ZH_CN = "zh-CN"  # s
    ZH_HANT = "zh-Hant"  # c

    ## Simplified (both)
    ZH_TW = "zh-TW"  # s
    ZH_HANS = "zh-Hans"  # c

    SHARED_DATA = SHARED_DATA  # c

    @classmethod
    def get_vs(cls) -> list["Lang"]:
        # return {*cls}.difference({cls.ZH_HANT, cls.ZH_HANS, cls.SHARED_DATA})
        return [cls.EN, cls.FR, cls.IT, cls.DE, cls.ES,
                cls.PT_BR, cls.PL, cls.RU, cls.JA, cls.KO,
                cls.TR, cls.UK, cls.ZH_CN, cls.ZH_TW]

    @classmethod
    def get_vc(cls) -> list["Lang"]:
        # return {*cls}.difference({cls.TR, cls.UK, cls.ZH_CN, cls.ZH_TW, cls.SHARED_DATA})
        return [cls.EN, cls.FR, cls.IT, cls.DE, cls.ES,
                cls.PT_BR, cls.PL, cls.RU, cls.JA, cls.KO,
                cls.ZH_HANT, cls.ZH_HANS]
