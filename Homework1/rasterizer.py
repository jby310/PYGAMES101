import numpy as np
from typing import Dict, List, Tuple
from Triangle import Triangle

class Rasterizer:
    """
    对应 C++ rst::rasterizer，当前只实现 Triangle + 线框模式。
    """

    def __init__(self, w: int, h: int) -> None:
        self.width = w
        self.height = h
        self.model = np.eye(4, dtype=np.float32)
        self.view = np.eye(4, dtype=np.float32)
        self.projection = np.eye(4, dtype=np.float32)

        self.pos_buf: Dict[int, List[np.ndarray]] = {}
        self.ind_buf: Dict[int, List[np.ndarray]] = {}
        self.frame_buf = np.zeros((h * w, 3), dtype=np.float32)
        self.depth_buf = np.full((h * w,), np.inf, dtype=np.float32)

        self._next_id = 0

    def _get_next_id(self) -> int:
        nid = self._next_id
        self._next_id += 1
        return nid

    def load_positions(self, positions: List[Tuple[float, float, float]]) -> int:
        """
        positions: list of 3D points
        返回 id（类似 pos_buf_id.pos_id）
        """
        pts = [np.array(p, dtype=np.float32) for p in positions]
        pid = self._get_next_id()
        self.pos_buf[pid] = pts
        return pid

    def load_indices(self, indices: List[Tuple[int, int, int]]) -> int:
        """
        indices: list of (i0, i1, i2)
        """
        inds = [np.array(idx, dtype=np.int32) for idx in indices]
        iid = self._get_next_id()
        self.ind_buf[iid] = inds
        return iid

    def set_model(self, m: np.ndarray) -> None:
        self.model = m.astype(np.float32)

    def set_view(self, v: np.ndarray) -> None:
        self.view = v.astype(np.float32)

    def set_projection(self, p: np.ndarray) -> None:
        self.projection = p.astype(np.float32)

    def clear(self, color: bool = True, depth: bool = True) -> None:
        if color:
            self.frame_buf[...] = 0.0
        if depth:
            self.depth_buf[...] = np.inf

    def _set_pixel(self, point: np.ndarray, color: np.ndarray) -> None:
        x = int(point[0])
        y = int(point[1])
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        ind = (self.height - 1 - y) * self.width + x
        self.frame_buf[ind, :] = color

    def _draw_line(self, begin: np.ndarray, end: np.ndarray) -> None:
        """
        Bresenham 线段绘制，对应 C++ draw_line。
        begin, end: 3D，但这里只用 xy。
        """
        x1, y1 = int(begin[0]), int(begin[1])
        x2, y2 = int(end[0]), int(end[1])

        line_color = np.array([255.0, 255.0, 255.0], dtype=np.float32)

        dx = x2 - x1
        dy = y2 - y1
        dx1 = abs(dx)
        dy1 = abs(dy)
        px = 2 * dy1 - dx1
        py = 2 * dx1 - dy1

        if dy1 <= dx1:
            if dx >= 0:
                x, y, xe = x1, y1, x2
            else:
                x, y, xe = x2, y2, x1

            self._set_pixel(np.array([x, y, 1.0], dtype=np.float32), line_color)

            while x < xe:
                x += 1
                if px < 0:
                    px += 2 * dy1
                else:
                    if (dx < 0 and dy < 0) or (dx > 0 and dy > 0):
                        y += 1
                    else:
                        y -= 1
                    px += 2 * (dy1 - dx1)
                self._set_pixel(np.array([x, y, 1.0], dtype=np.float32), line_color)
        else:
            if dy >= 0:
                x, y, ye = x1, y1, y2
            else:
                x, y, ye = x2, y2, y1

            self._set_pixel(np.array([x, y, 1.0], dtype=np.float32), line_color)

            while y < ye:
                y += 1
                if py <= 0:
                    py += 2 * dx1
                else:
                    if (dx < 0 and dy < 0) or (dx > 0 and dy > 0):
                        x += 1
                    else:
                        x -= 1
                    py += 2 * (dx1 - dy1)
                self._set_pixel(np.array([x, y, 1.0], dtype=np.float32), line_color)

    def _rasterize_wireframe(self, t: Triangle) -> None:
        self._draw_line(t.c(), t.a())
        self._draw_line(t.c(), t.b())
        self._draw_line(t.b(), t.a())

    def draw(self, pos_id: int, ind_id: int) -> None:
        """
        只支持三角形 + 线框模式，对应 C++ draw 中 Primitive::Triangle 分支。
        """
        buf = self.pos_buf[pos_id]
        ind = self.ind_buf[ind_id]

        # 深度映射常数，对应 C++ 里的 f1, f2
        f1 = (100.0 - 0.1) / 2.0
        f2 = (100.0 + 0.1) / 2.0

        mvp = self.projection @ self.view @ self.model

        for idx in ind:
            t = Triangle()

            # 取出顶点并做 MVP 变换
            v = []
            for i in range(3):
                p = buf[idx[i]]
                v4 = np.array([p[0], p[1], p[2], 1.0], dtype=np.float32)
                v4 = mvp @ v4
                # 透视除法
                v4 /= v4[3]
                # 视口变换：[-1,1] -> [0,width/height]
                v4[0] = 0.5 * self.width * (v4[0] + 1.0)
                v4[1] = 0.5 * self.height * (v4[1] + 1.0)
                v4[2] = v4[2] * f1 + f2
                v.append(v4)

            for i in range(3):
                t.set_vertex(i, v[i][:3])

            # 设置三个顶点不同颜色（和 C++ 中一样）
            t.set_color(0, 255.0, 0.0, 0.0)
            t.set_color(1, 0.0, 255.0, 0.0)
            t.set_color(2, 0.0, 0.0, 255.0)

            self._rasterize_wireframe(t)

    def frame_buffer(self) -> np.ndarray:
        return self.frame_buf

