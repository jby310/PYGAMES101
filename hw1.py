import sys
import math
import argparse
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import cv2


MY_PI = 3.1415926


def get_view_matrix(eye_pos: np.ndarray) -> np.ndarray:
    """
    完全对应 C++ 里的 get_view_matrix。
    eye_pos: shape (3,)
    """
    view = np.eye(4, dtype=np.float32)
    translate = np.array(
        [
            [1, 0, 0, -eye_pos[0]],
            [0, 1, 0, -eye_pos[1]],
            [0, 0, 1, -eye_pos[2]],
            [0, 0, 0, 1],
        ],
        dtype=np.float32,
    )
    view = translate @ view
    return view


def get_model_matrix(rotation_angle: float) -> np.ndarray:
    """
    对应作业 TODO：绕 Z 轴旋转的模型矩阵。
    rotation_angle: 角度（度）
    """
    rad = rotation_angle / 180.0 * MY_PI
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    model = np.array(
        [
            [cos_a, -sin_a, 0, 0],
            [sin_a, cos_a, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ],
        dtype=np.float32,
    )
    return model


def get_projection_matrix(
    eye_fov: float, aspect_ratio: float, zNear: float, zFar: float
) -> np.ndarray:
    """
    对应作业 TODO：透视投影矩阵。

    这里采用 GAMES101 官方推荐的“透视到正交”的分解实现方式：
    1. 先构造透视到正交的矩阵（persp2ortho）
    2. 再对正交盒子做平移 + 缩放到标准立方体 [-1,1]^3
    """
    # 注意：作业里 zNear / zFar 传入的是正数，但相机朝 -z，看向负 z 方向。
    # 常见做法是把 n, f 取为负值。
    n = -zNear
    f = -zFar

    # 由 fov 计算上下（top/bottom）以及左右（left/right）平面
    half_rad = (eye_fov / 180.0 * MY_PI) / 2.0
    t = math.tan(half_rad) * abs(n)  # top
    b = -t                           # bottom
    r = t * aspect_ratio             # right
    l = -r                           # left

    # 透视 -> 正交
    persp2ortho = np.array(
        [
            [n, 0, 0, 0],
            [0, n, 0, 0],
            [0, 0, n + f, -n * f],
            [0, 0, 1, 0],
        ],
        dtype=np.float32,
    )

    # 正交投影：先平移到原点，再缩放到 [-1,1]^3
    ortho_translate = np.array(
        [
            [1, 0, 0, -(r + l) / 2.0],
            [0, 1, 0, -(t + b) / 2.0],
            [0, 0, 1, -(n + f) / 2.0],
            [0, 0, 0, 1],
        ],
        dtype=np.float32,
    )

    ortho_scale = np.array(
        [
            [2.0 / (r - l), 0, 0, 0],
            [0, 2.0 / (t - b), 0, 0],
            [0, 0, 2.0 / (n - f), 0],
            [0, 0, 0, 1],
        ],
        dtype=np.float32,
    )

    ortho = ortho_scale @ ortho_translate
    projection = ortho @ persp2ortho
    return projection


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


def run_once(angle: float, filename: str) -> None:
    """
    命令行模式：只渲染一帧并保存到文件。
    """
    r = Rasterizer(700, 700)
    eye_pos = np.array([0.0, 0.0, 5.0], dtype=np.float32)

    pos = [(2.0, 0.0, -2.0), (0.0, 2.0, -2.0), (-2.0, 0.0, -2.0)]
    ind = [(0, 1, 2)]

    pos_id = r.load_positions(pos)
    ind_id = r.load_indices(ind)

    r.clear(color=True, depth=True)
    r.set_model(get_model_matrix(angle))
    r.set_view(get_view_matrix(eye_pos))
    r.set_projection(get_projection_matrix(45.0, 1.0, 0.1, 50.0))

    r.draw(pos_id, ind_id)

    img_data = r.frame_buffer().reshape((700, 700, 3))
    # 与 C++ 一样：CV_32FC3 -> CV_8UC3
    image = img_data.astype(np.float32)
    image = np.clip(image, 0.0, 255.0)
    image = image.astype(np.uint8)

    cv2.imwrite(filename, image)
    print(f"Saved image to {filename}")


def run_interactive() -> None:
    """
    交互模式：按 'a' / 'd' 旋转三角形，ESC 退出。
    """
    angle = 0.0
    r = Rasterizer(700, 700)
    eye_pos = np.array([0.0, 0.0, 5.0], dtype=np.float32)

    pos = [(2.0, 0.0, -2.0), (0.0, 2.0, -2.0), (-2.0, 0.0, -2.0)]
    ind = [(0, 1, 2)]

    pos_id = r.load_positions(pos)
    ind_id = r.load_indices(ind)

    frame_count = 0
    key = -1

    while key != 27:  # ESC
        r.clear(color=True, depth=True)
        r.set_model(get_model_matrix(angle))
        r.set_view(get_view_matrix(eye_pos))
        r.set_projection(get_projection_matrix(45.0, 1.0, 0.1, 50.0))

        r.draw(pos_id, ind_id)

        img_data = r.frame_buffer().reshape((700, 700, 3))
        image = img_data.astype(np.float32)
        image = np.clip(image, 0.0, 255.0)
        image = image.astype(np.uint8)

        cv2.imshow("image", image)
        key = cv2.waitKey(10) & 0xFF

        print(f"frame count: {frame_count}")
        frame_count += 1

        if key == ord("a"):
            angle += 10.0
        elif key == ord("d"):
            angle -= 10.0

    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(
        description="Python reimplementation of GAMES101 Homework1 rasterizer."
    )
    parser.add_argument(
        "-r",
        "--angle",
        type=float,
        default=None,
        help="Rotation angle in degrees; if provided, run once and save image.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="output.png",
        help="Output image filename in one-shot mode.",
    )
    args = parser.parse_args()

    if args.angle is not None:
        run_once(args.angle, args.output)
    else:
        # 与 C++ 程序无参数时类似，进入交互模式
        run_interactive()


if __name__ == "__main__":
    main()