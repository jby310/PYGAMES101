import math
import numpy as np
from typing import Dict, List, Tuple
from Triangle import Triangle

class Rasterizer:
    def __init__(self, w, h):
        self.width = w
        self.height = h
        self.frame_buf = np.zeros((h, w, 3))
        self.depth_buf = np.full((h, w), -float('inf'))
        
        self.model = np.eye(4)
        self.view = np.eye(4)
        self.projection = np.eye(4)

    def set_model(self, m): self.model = m
    def set_view(self, v): self.view = v
    def set_projection(self, p): self.projection = p

    def clear(self):
        self.frame_buf.fill(0)
        self.depth_buf.fill(-float('inf'))

    def get_index(self, x, y):
        # 翻转 y 轴匹配课程习惯
        return (self.height - 1 - y), x

    def inside_triangle(self, x, y, v):
        # 使用叉积判断点是否在三角形内
        v0, v1, v2 = v[:, :2]
        p = np.array([x, y])
        
        def cross_product_2d(a, b):
            return a[0]*b[1] - a[1]*b[0]
        
        c1 = cross_product_2d(v1 - v0, p - v0)
        c2 = cross_product_2d(v2 - v1, p - v1)
        c3 = cross_product_2d(v0 - v2, p - v2)
        
        return (c1 > 0 and c2 > 0 and c3 > 0) or (c1 < 0 and c2 < 0 and c3 < 0)

    def compute_barycentric_2d(self, x, y, v):
        v0, v1, v2 = v[:, :2]
        c1 = (x*(v1[1] - v2[1]) + (v2[0] - v1[0])*y + v1[0]*v2[1] - v2[0]*v1[1]) / (v0[0]*(v1[1] - v2[1]) + (v2[0] - v1[0])*v0[1] + v1[0]*v2[1] - v2[0]*v1[1])
        c2 = (x*(v2[1] - v0[1]) + (v0[0] - v2[0])*y + v2[0]*v0[1] - v0[0]*v2[1]) / (v1[0]*(v2[1] - v0[1]) + (v0[0] - v2[0])*v1[1] + v2[0]*v0[1] - v0[0]*v2[1])
        c3 = 1 - c1 - c2
        return c1, c2, c3

    def rasterize_triangle(self, t):
        # 获取 4x4 齐次坐标顶点
        v_orig = np.ones((3, 4))
        v_orig[:, :3] = t.v
        
        # 应用 MVP 变换
        mvp = self.projection @ self.view @ self.model
        v = (mvp @ v_orig.T).T
        
        # 透视除法
        w = v[:, 3].copy()
        v /= v[:, 3][:, np.newaxis]
        
        # 视口变换
        v[:, 0] = 0.5 * self.width * (v[:, 0] + 1.0)
        v[:, 1] = 0.5 * self.height * (v[:, 1] + 1.0)
        # 深度缩放 (zNear=0.1, zFar=50)
        f1 = (50 - 0.1) / 2.0
        f2 = (50 + 0.1) / 2.0
        v[:, 2] = v[:, 2] * f1 + f2

        # 1. 确定包围盒
        min_x = math.floor(np.min(v[:, 0]))
        max_x = math.ceil(np.max(v[:, 0]))
        min_y = math.floor(np.min(v[:, 1]))
        max_y = math.ceil(np.max(v[:, 1]))

        # 2. 遍历像素
        for x in range(max(0, min_x), min(self.width, max_x)):
            for y in range(max(0, min_y), min(self.height, max_y)):
                if self.inside_triangle(x + 0.5, y + 0.5, v):
                    # 3. 计算插值深度
                    alpha, beta, gamma = self.compute_barycentric_2d(x + 0.5, y + 0.5, v)
                    
                    # 透视修正插值 (z_interpolated)
                    w_reciprocal = 1.0 / (alpha/w[0] + beta/w[1] + gamma/w[2])
                    z_interpolated = (alpha*v[0, 2]/w[0] + beta*v[1, 2]/w[1] + gamma*v[2, 2]/w[2]) * w_reciprocal

                    # 4. Z-Buffer 测试
                    iy, ix = self.get_index(x, y)
                    if z_interpolated > self.depth_buf[iy, ix]:
                        self.depth_buf[iy, ix] = z_interpolated
                        self.frame_buf[iy, ix] = t.get_color()


