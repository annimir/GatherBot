import configparser

language_path = configparser.ConfigParser(allow_no_value=True, delimiters=('=',))

default_language = "RU"
path_language = {
    "RU": "messages/messages_ru.properties",
    "EN": "messages/messages_en.properties",
}


def getLanguagePath(language: str):
    return path_language[language]


def message(language: str, text: str, key) -> str:
    language_path.read(getLanguagePath(language), encoding='utf-8')
    return str(language_path[key][text])


def message(language: str, text: str, key, *args) -> str:
    language_path.read(getLanguagePath(language), encoding='utf-8')
    return str(language_path[key][text]).format(*args)