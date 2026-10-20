class DictionariesFeatureError(Exception):
    pass


class DuplicateDictionaryNameError(DictionariesFeatureError):
    pass


class CategoryNotFoundError(DictionariesFeatureError):
    pass
