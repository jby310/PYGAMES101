import numpy as np

class Triangle:
    def __init__(self):
        self.v = np.zeros((3, 3))  # 顶点坐标
        self.color = np.zeros((3, 3)) # 顶点颜色
        
    def set_vertex(self, ind, ver):
        self.v[ind] = ver
        
    def set_color(self, ind, r, g, b):
        self.color[ind] = np.array([r, g, b]) / 255.0

    def get_color(self):
        return self.color[0] * 255.0
