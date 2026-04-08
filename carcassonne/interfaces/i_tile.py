from abc import ABC


class ITile(ABC):
    code: str
    tiles_lands: dict
    connect_to: dict
    direction_matrix: list[list[list[str]]]
