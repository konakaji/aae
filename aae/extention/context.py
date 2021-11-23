from aae.extention.base import LoadingMethod, DefaultLoadingMethod
from aae.extention.aae import AAE_KEY, AAELoadingMethod


class Context:
    loader_map = {}

    @classmethod
    def register(cls, key, l_method: LoadingMethod):
        cls.loader_map[key] = l_method

    @classmethod
    def get(cls, key):
        if key in cls.loader_map:
            return cls.loader_map[key]
        return DefaultLoadingMethod()


Context.register(AAE_KEY, AAELoadingMethod())
