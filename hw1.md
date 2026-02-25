# 透视投影矩阵（Perspective Projection Matrix）

```python
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

```

这段代码实现的是计算机图形学中经典的**透视投影矩阵（Perspective Projection Matrix）**。它采用了 GAMES101 课程中推荐的分解法，将复杂的投影过程拆解为三步。

------

## 1. 核心数学原理：分解法

透视投影的目标是将一个**视锥体（Frustum）\**转换成一个\**标准立方体（Canonical View Volume, $[-1, 1]^3$）**。

数学上，这个过程被分解为两步：

1. **Persp $\rightarrow$ Ortho**：将视锥体“挤压”成一个长方体（正交框）。
2. **Ortho $\rightarrow$ Canonical**：将长方体平移并缩放到标准立方体。

最终矩阵公式为：

$$M_{proj} = M_{ortho} \cdot M_{persp \rightarrow ortho}$$

------

## 2. 第一阶段：透视到正交（`persp2ortho`）

为了把视锥体“挤”成长方体，我们需要找到一种映射，使得近平面（Near）保持不变，远平面（Far）的 $z$ 轴坐标保持不变，且远平面的中心点不动。

通过相似三角形性质，对于空间中一点 $(x, y, z)$，挤压后的坐标应满足：

- $x' = \frac{n}{z}x$
- $y' = \frac{n}{z}y$

利用齐次坐标的性质（同时乘以 $z$），我们构造出代码中的 `persp2ortho` 矩阵：

$$M_{persp \rightarrow ortho} = \begin{pmatrix} n & 0 & 0 & 0 \\ 0 & n & 0 & 0 \\ 0 & 0 & n+f & -nf \\ 0 & 0 & 1 & 0 \end{pmatrix}$$

> **注意**：代码中最后一行是 `[0, 0, 1, 0]`，这会将原有的 $z$ 值存入 $w$ 分量，为后续的**齐次除法**（Homogeneous Division）做准备。

------

## 3. 第二阶段：计算视口边界（`t, b, l, r`）

在正交变换前，我们需要知道“挤压”后的长方体有多大。这取决于视角（Field of View）和宽高比（Aspect Ratio）。

- **Top ($t$)**: $\tan(\frac{fov}{2}) \cdot |n|$
- **Right ($r$)**: $t \cdot aspect\_ratio$
- **Bottom & Left**: 基于对称性取负值。

------

## 4. 第三阶段：正交投影（`ortho`）

现在我们已经得到了一个范围在 $[l, r], [b, t], [f, n]$ 的长方体，需要将其映射到 $[-1, 1]^3$。这分为两步：

### A. 平移 (`ortho_translate`)

将长方体的中心点移到原点。

- 中心点坐标为：$(\frac{r+l}{2}, \frac{t+b}{2}, \frac{n+f}{2})$。
- 矩阵对应位置填入负的偏移量。

### B. 缩放 (`ortho_scale`)

将物体的长度、宽度、高度缩放到 2（因为 $[-1, 1]$ 的长度是 2）。

- $x$ 方向缩放比例：$\frac{2}{r-l}$
- $y$ 方向缩放比例：$\frac{2}{t-b}$
- $z$ 方向缩放比例：$\frac{2}{n-f}$

------

## 5. 代码中的细节陷阱

1. **z 值的正负**：代码开头定义 `n = -zNear` 和 `f = -zFar`。这是因为在 OpenGL 惯例中，相机看向 $-z$ 方向，所以近/远平面的坐标值是负数。

2. **矩阵乘法顺序**：

   `projection = ortho @ persp2ortho`

   这意味着向量先经过“挤压”矩阵，再经过“正交”矩阵，符合数学逻辑。

3. **z 轴方向缩放**：

   注意 `ortho_scale` 中 $z$ 轴的缩放是 `2.0 / (n - f)`。由于 $n > f$（例如 $-0.1 > -100$），这会保证 $z$ 轴的映射关系正确。

**您是否需要我为您推导一下 `persp2ortho` 矩阵中第三行 $n+f$ 和 $-nf$ 是如何通过代数确定的？**

这是一个非常经典且深入的问题。结论是：**处于 $z = \frac{n+f}{2}$（几何中点）处的点，在经过透视投影挤压后，会更靠近后平面（远平面 $f$）**。

换句话说，透视投影会把中间的深度值“推”向远方。这种现象被称为**深度非线性（Depth Non-linearity）**。

------

### 1. 数学推导

我们来看 `persp2ortho` 矩阵对 $z$ 坐标的影响。根据你代码中的矩阵：

$$M_{persp \rightarrow ortho} = \begin{pmatrix} n & 0 & 0 & 0 \\ 0 & n & 0 & 0 \\ 0 & 0 & n+f & -nf \\ 0 & 0 & 1 & 0 \end{pmatrix}$$

假设空间中一个点为 $(x, y, z, 1)$，乘上该矩阵后，新的 $z$ 分量（记为 $z_{new}$）和新的 $w$ 分量（记为 $w_{new}$）为：

- $z_{new} = (n+f)z - nf$
- $w_{new} = z$

经过**齐次除法**（归一化）后，挤压后的 $z$ 坐标 $z'$ 为：

$$z' = \frac{(n+f)z - nf}{z} = n + f - \frac{nf}{z}$$

------

### 2. 带入中点值计算

我们将几何中点 $z_{mid} = \frac{n+f}{2}$ 带入上述公式：

1. **初始位置**：$z = \frac{n+f}{2}$

2. **变换后位置**：

   $$z' = (n+f) - \frac{nf}{\frac{n+f}{2}} = (n+f) - \frac{2nf}{n+f}$$

3. **通分简化**：

   $$z' = \frac{(n+f)^2 - 2nf}{n+f} = \frac{n^2 + f^2}{n+f}$$

### 3. 比较结果

我们要判断 $z'$ 更靠近 $n$ 还是 $f$。在相机坐标系中，注意 $n$ 和 $f$ 都是负数（例如 $n = -1, f = -10$）。

- **物理中点**：$z_{mid} = -5.5$
- **变换后的 $z'$**：$\frac{(-1)^2 + (-10)^2}{-1 - 10} = \frac{101}{-11} \approx -9.18$

可以看到，原本处于 $-5.5$ 的位置，经过挤压后变成了 $-9.18$。**$-9.18$ 显然比 $-5.5$ 更接近远平面 $-10$。**

------

### 4. 为什么会这样？（直观理解）

透视投影的本质是**近大远小**。

- 为了实现这个效果，靠近近平面（$n$）的区域拥有更高的**深度分辨率**（Precision）。
- 大量的 $z$ 轴数值范围被分配给了靠近相机的物体。
- 这就导致远处的物体在 $z$ 轴上被大幅度“压缩”了。

> **带来的影响**：这就是为什么在 3D 游戏中经常会出现 **Z-Fighting**（深度冲突）。因为远处的物体共享极其狭窄的一段 $z$ 范围，导致显卡无法分辨谁在前谁在后。

**你想了解如何通过调整 $n$ 和 $f$ 的值来缓解这种深度精度损失的问题吗？**