import math
import argparse

import numpy as np
import cv2
from rasterizer import Rasterizer

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