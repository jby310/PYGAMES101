## L03-04 Transformation

### Scale Matrix

![image-20260301162303170](Notes.assets/image-20260301162303170.png)

![image-20260301162250606](Notes.assets/image-20260301162250606.png)

### Reflection Matrix 反射矩阵

![image-20260301162224416](Notes.assets/image-20260301162224416.png)

### Shear Matrix 切变矩阵

![image-20260301154039740](Notes.assets/image-20260301154039740.png)

### Rotate Matrix

![image-20260301154424993](Notes.assets/image-20260301154424993.png)

- 默认绕原点，逆时针（CCW）

![image-20260301162531640](Notes.assets/image-20260301162531640.png)

- 性质：**旋转矩阵的逆就是旋转矩阵的转置，即旋转矩阵也是正交矩阵。**

### Linear Transforms

![image-20260301154829119](Notes.assets/image-20260301154829119.png)

### Homogeneous Coordinates

![image-20260301154935005](Notes.assets/image-20260301154935005.png)

**平移变换不是线性变换**。

![image-20260301155259690](Notes.assets/image-20260301155259690.png)

**向量具有平移不变性**，且满足下面的运算：

![image-20260301155526121](Notes.assets/image-20260301155526121.png)

- 一个点加另一个点的齐次坐标 = 这两个点的中点。

### Affine Transformation

![image-20260301155922890](Notes.assets/image-20260301155922890.png)

- 仿射变换 = 线性变换 + 平移
- 引入齐次坐标的目的就是为了把所有的变换写成一个矩阵乘以一个向量的简单形式。

### 小结：2D Transform

![image-20260301160218077](Notes.assets/image-20260301160218077.png)

---

### Inverse Transform

![image-20260301160435377](Notes.assets/image-20260301160435377.png)

### Composite Transform 合成变换

![image-20260301160733227](Notes.assets/image-20260301160733227.png)

![image-20260301160811057](Notes.assets/image-20260301160811057.png)

![image-20260301160929128](Notes.assets/image-20260301160929128.png)

矩阵相乘不满足交换律，**但满足结合律**：

![image-20260301161120194](Notes.assets/image-20260301161120194.png)

### Decomposing Complex Transforms

![image-20260301161258520](Notes.assets/image-20260301161258520.png)

### 3D Transformations

![image-20260301161537767](Notes.assets/image-20260301161537767.png)

![image-20260301161624342](Notes.assets/image-20260301161624342.png)

先应用线性变换，再平移。

![image-20260301163738130](Notes.assets/image-20260301163738130.png)

![image-20260301163520164](Notes.assets/image-20260301163520164.png)

- 按照右手定则，以及xyz循环对称规律，z叉乘x得到y，所以Ry里面的顺序跟Rx和Rz是反的。

### 3D Rotations

![image-20260301164005141](Notes.assets/image-20260301164005141.png)

俯仰（pitch）、航向（yaw）和横滚（roll）

### Rodrigues' Rotation Formula

![image-20260301164448097](Notes.assets/image-20260301164448097.png)

- 推导见补充材料。
- 四元数主要是为了插值方便。

### View / Camera Transformation

![image-20260301164736740](Notes.assets/image-20260301164736740.png)

![image-20260301164834949](Notes.assets/image-20260301164834949.png)

![image-20260301165014580](Notes.assets/image-20260301165014580.png)

- 提到一个相对运动的概念。

- 注意到仍然是右手系。

![image-20260301165227464](Notes.assets/image-20260301165227464.png)

  ![image-20260301165609929](Notes.assets/image-20260301165609929.png)

- why：旋转矩阵是正交矩阵，转置就是它的逆。

![image-20260301170038861](Notes.assets/image-20260301170038861.png)

模型变换通常跟视图变换放在一起叫ModelView。

### Projection transformation

![image-20260301170336604](Notes.assets/image-20260301170336604.png)

![image-20260301171037811](Notes.assets/image-20260301171037811.png)

- 正交投影假设相机离得无限远。

#### Orthographic projection

![image-20260301171158933](Notes.assets/image-20260301171158933.png)

下面这种做法更通用： 

![image-20260301171308149](Notes.assets/image-20260301171308149.png)

- 因为没有丢弃z轴所以，规范化维度为立方
- 注意：因为是沿着-z看，所以离得远的物体z值更小，远小于近。

![image-20260301172243124](Notes.assets/image-20260301172243124.png)

![image-20260301172334744](Notes.assets/image-20260301172334744.png)

#### Perspective projection

![image-20260301172601754](Notes.assets/image-20260301172601754.png)

![image-20260301172645915](Notes.assets/image-20260301172645915.png)

![image-20260301172748745](Notes.assets/image-20260301172748745.png)

**对于中间的任何一个点，经过挤压变换之后，z值会如何变化？**
$$
z'=n+f-\frac{nf}{z}
$$
这个公式表明，z 值的变化是一个关于 `1/z` 的线性函数，这导致了深度值的非线性分布，使得近处的深度精度更高，即快速被拉向了远处。**所以中间的点会更靠近远平面**。

![image-20260301172922736](Notes.assets/image-20260301172922736.png)

![image-20260301172957127](Notes.assets/image-20260301172957127.png)

![image-20260301173048303](Notes.assets/image-20260301173048303.png)

![image-20260301173125439](Notes.assets/image-20260301173125439.png)

![image-20260301173456708](Notes.assets/image-20260301173456708.png)

![image-20260301173655149](Notes.assets/image-20260301173655149.png)

![image-20260301173701931](Notes.assets/image-20260301173701931.png)

### Homework1

这份代码通常源自 **GAMES101**（现代计算机图形学入门）的作业 1。你需要补全的是 `get_model_matrix`（模型变换）和 `get_projection_matrix`（投影变换）这两个核心函数。

以下是基于 Eigen 库的详细实现方案：

------

#### 1. 补全 `get_model_matrix`

此函数要求创建一个绕 **Z 轴**旋转的矩阵。

绕 Z 轴旋转 $\alpha$ 度的旋转矩阵公式为：

$$R_z(\alpha) = \begin{pmatrix} \cos\alpha & -\sin\alpha & 0 & 0 \\ \sin\alpha & \cos\alpha & 0 & 0 \\ 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & 1 \end{pmatrix}$$



```C++
Eigen::Matrix4f get_model_matrix(float rotation_angle)
{
    Eigen::Matrix4f model = Eigen::Matrix4f::Identity();

    // 将角度转换为弧度
    float radian = rotation_angle * MY_PI / 180.0;
    
    // 填充旋转矩阵内容
    model << cos(radian), -sin(radian), 0, 0,
             sin(radian),  cos(radian), 0, 0,
             0,            0,           1, 0,
             0,            0,           0, 1;

    return model;
}
```

------

#### 2. 补全 `get_projection_matrix`

投影变换通常分为两步：

1. **透视投影转正交投影** (Perspective to Orthographic)。
2. **正交投影变换** (Orthographic Projection)，即将视角立方体缩放并平移至 $[-1, 1]^3$。

```C++
Eigen::Matrix4f get_projection_matrix(float eye_fov, float aspect_ratio,
                                      float zNear, float zFar)
{
    Eigen::Matrix4f projection = Eigen::Matrix4f::Identity();

    // 1. Perspective -> Orthographic 矩阵
    Eigen::Matrix4f persp_to_ortho;
    persp_to_ortho << zNear, 0, 0, 0,
                      0, zNear, 0, 0,
                      0, 0, zNear + zFar, -zNear * zFar,
                      0, 0, 1, 0;

    // 2. 计算视锥体边界 (Top, Bottom, Left, Right)
    float angle = eye_fov * MY_PI / 180.0;
    float t = zNear * tan(angle / 2.0); // top
    float b = -t;                       // bottom
    float r = t * aspect_ratio;         // right
    float l = -r;                       // left

    // 3. 正交投影矩阵 (Scale * Translate)
    Eigen::Matrix4f ortho_scale = Eigen::Matrix4f::Identity();
    ortho_scale << 2.0/(r-l), 0, 0, 0,
                   0, 2.0/(t-b), 0, 0,
                   0, 0, 2.0/(zNear-zFar), 0, // 注意：zNear > zFar 在某些约定下需处理符号
                   0, 0, 0, 1;

    Eigen::Matrix4f ortho_trans = Eigen::Matrix4f::Identity();
    ortho_trans << 1, 0, 0, -(r+l)/2.0,
                   0, 1, 0, -(t+b)/2.0,
                   0, 0, 1, -(zNear+zFar)/2.0,
                   0, 0, 0, 1;

    // 最终组合矩阵：M_proj = M_ortho_scale * M_ortho_trans * M_persp_to_ortho
    projection = ortho_scale * ortho_trans * persp_to_ortho;

    return projection;
}
```

------

**关键点说明**

- **弧度制转换**：C++ 的 `sin()` 和 `cos()` 函数接收的是弧度（Radian），而非角度（Degree），所以必须乘以 $\frac{\pi}{180}$。
- **Z 轴正负号**：在 GAMES101 的环境中，相机看向的是 $Z$ 轴负方向。在处理 `zNear` 和 `zFar` 时，代码通常传入的是绝对数值（正数），但在矩阵运算中，它们位于负半轴。上面的代码采用了标准的透视推导方式。
- **矩阵乘法顺序**：Eigen 中的矩阵乘法是左乘。

