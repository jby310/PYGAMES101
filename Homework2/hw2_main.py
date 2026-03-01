import math

import numpy as np
import cv2
from rasterizer import Rasterizer
from Triangle import Triangle

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
    model = np.eye(4, dtype=np.float32)
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
    # 注意：如果 zNear / zFar 传入的是正数，但相机朝 -z，看向负 z 方向。
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


if __name__ == "__main__":
    r = Rasterizer(700, 700)
    eye_pos = [0, 0, 5]
    
    # 定义两个三角形（对应 main.cpp 里的数据）
    tri1 = Triangle()
    tri1.set_vertex(0, [2, 0, -2]); tri1.set_vertex(1, [0, 2, -2]); tri1.set_vertex(2, [-2, 0, -2])
    tri1.set_color(0, 217, 238, 185); tri1.set_color(1, 217, 238, 185); tri1.set_color(2, 217, 238, 185)

    tri2 = Triangle()
    tri2.set_vertex(0, [3.5, -1, -5]); tri2.set_vertex(1, [2.5, 1.5, -5]); tri2.set_vertex(2, [-1, 0.5, -5])
    tri2.set_color(0, 185, 217, 238); tri2.set_color(1, 185, 217, 238); tri2.set_color(2, 185, 217, 238)

    r.set_view(get_view_matrix(eye_pos))
    r.set_projection(get_projection_matrix(45, 1, 0.1, 50)) # 注意Near/Far符号习惯

    while True:
        r.clear()
        r.rasterize_triangle(tri1)
        r.rasterize_triangle(tri2)
        
        # 转换为 OpenCV 格式 (RGB -> BGR, 0-255 uint8)
        img = (r.frame_buf).astype(np.uint8)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        cv2.imshow('GAMES101 HW2 Python', img)
        if cv2.waitKey(10) == 27: # ESC 退出
            break
    cv2.destroyAllWindows()