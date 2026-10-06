from generated.base_struct import BaseStruct
from generated.formats.landscape.structs.Pair import Pair


class Repeat2(BaseStruct):
    ind: int
    pair: Pair

    def __init__(self, context: object, arg: int = 0, template: object = None, set_default: bool = True) -> None: ...
