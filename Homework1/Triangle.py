import numpy as np
from typing import List
from dataclasses import dataclass

@dataclass
class Triangle:
    """
    对应 C++ 的 Triangle 类，只用到 v 和 color。
    """
    v: List[np.ndarray]
    color: List[np.ndarray]

    def __init__(self) -> None:
        self.v = [np.zeros(3, dtype=np.float32) for _ in range(3)]
        self.color = [np.zeros(3, dtype=np.float32) for _ in range(3)]

    def a(self) -> np.ndarray:
        return self.v[0]

    def b(self) -> np.ndarray:
        return self.v[1]

    def c(self) -> np.ndarray:
        return self.v[2]

    def set_vertex(self, ind: int, ver: np.ndarray) -> None:
        self.v[ind] = ver.astype(np.float32)

    def set_color(self, ind: int, r: float, g: float, b: float) -> None:
        if not (0.0 <= r <= 255.0 and 0.0 <= g <= 255.0 and 0.0 <= b <= 255.0):
            raise ValueError("Invalid color values")
        self.color[ind] = np.array([r / 255.0, g / 255.0, b / 255.0], dtype=np.float32)

