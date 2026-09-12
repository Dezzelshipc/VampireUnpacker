from typing import Callable


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        key = cls.__name__
        if key not in cls._instances:
            cls._instances[key] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[key]


class Objectless:
    def __new__(cls, *args, **kwargs):
        raise RuntimeError(f'{cls} should not be instantiated')


class Emitter[**P](Objectless):
    _callbacks: dict[str, set[Callable[[P], None]]] = {}

    @classmethod
    def register(cls, name: str, c: Callable[[P], None]) -> None:
        if name not in cls._callbacks:
            cls._callbacks[name] = set()

        cls._callbacks[name].add(c)

    @classmethod
    def unregister(cls, name: str, c: Callable[[P], None]) -> None:
        if name not in cls._callbacks:
            return

        cls._callbacks[name].discard(c)

    @classmethod
    def emit(cls, name: str, *args, **kwargs) -> None:
        for c in cls._callbacks.get(name, {}):
            c(*args, **kwargs)
