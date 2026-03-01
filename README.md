[TOC]
# PYGAMES101

用python重构一遍Games101作业




## Homework2
### 栅格化一个三角形——在屏幕上画出一个实心三角形

上一次作业中，在视口变化之后，我们调用了函数`rasterize_wireframe(const Triangle& t)`。

```c++
void rst::rasterizer::rasterize_wireframe(const Triangle& t)
{
    draw_line(t.c(), t.a());
    draw_line(t.c(), t.b());
    draw_line(t.b(), t.a());
}
```
但这一次，你需要自己填写并调用函数`rasterize_triangle(const Triangle& t)`
```c++
//Screen space rasterization
void rst::rasterizer::rasterize_triangle(const Triangle& t) {
    auto v = t.toVector4();
    
    // TODO : Find out the bounding box of current triangle.
    // iterate through the pixel and find if the current pixel is inside the triangle

    // If so, use the following code to get the interpolated z value.
    //auto[alpha, beta, gamma] = computeBarycentric2D(x, y, t.v);
    //float w_reciprocal = 1.0/(alpha / v[0].w() + beta / v[1].w() + gamma / v[2].w());
    //float z_interpolated = alpha * v[0].z() / v[0].w() + beta * v[1].z() / v[1].w() + gamma * v[2].z() / v[2].w();
    //z_interpolated *= w_reciprocal;

    // TODO : set the current pixel (use the set_pixel function) to the color of the triangle (use getColor function) if it should be painted.
}
```

要完成 `rasterize_triangle` 函数，我们需要遵循以下步骤：

1. **确定包围盒 (Bounding Box)**：找到三角形三个顶点在 $x$ 和 $y$ 方向上的最小值和最大值。
2. **遍历像素**：在包围盒范围内，检查每个像素中心点 $(x+0.5, y+0.5)$ 是否在三角形内。
3. **深度测试 (Z-buffer)**：如果点在三角形内，计算插值后的 $z$ 值，并与 `depth_buf` 中的值比较。如果当前点更近，则更新深度缓冲并着色。

还需要配合实现 `insideTriangle` 函数来完成判定。

---

### 1. 实现 insideTriangle

这个函数通常使用 **叉积 (Cross Product)** 法。对于三角形 $ABC$ 和点 $P$，如果 $\vec{AB} \times \vec{AP}$、$\vec{BC} \times \vec{BP}$、$\vec{CA} \times \vec{CP}$ 的方向一致（同正或同负），则点在三角形内。

```cpp
static bool insideTriangle(float x, float y, const Vector3f* _v)
{   
    // 向量 AB, BC, CA
    Eigen::Vector2f v01 = _v[1].head<2>() - _v[0].head<2>();
    Eigen::Vector2f v12 = _v[2].head<2>() - _v[1].head<2>();
    Eigen::Vector2f v20 = _v[0].head<2>() - _v[2].head<2>();

    // 向量 AP, BP, CP (P 为像素中心点)
    Eigen::Vector2f v0p = Eigen::Vector2f(x, y) - _v[0].head<2>();
    Eigen::Vector2f v1p = Eigen::Vector2f(x, y) - _v[1].head<2>();
    Eigen::Vector2f v2p = Eigen::Vector2f(x, y) - _v[2].head<2>();

    // 计算 2D 叉积 (z分量)
    float z1 = v01.x() * v0p.y() - v01.y() * v0p.x();
    float z2 = v12.x() * v1p.y() - v12.y() * v1p.x();
    float z3 = v20.x() * v2p.y() - v20.y() * v2p.x();

    // 判断符号是否一致
    return (z1 > 0 && z2 > 0 && z3 > 0) || (z1 < 0 && z2 < 0 && z3 < 0);
}

```

---

### 2. 实现 rasterize_triangle

```cpp
void rst::rasterizer::rasterize_triangle(const Triangle& t) {
    auto v = t.toVector4(); // 这里的 v 是四个 Vector4f，包含了变换后的坐标
    
    // 1. 找到包围盒 (Bounding Box)
    float min_x = std::min({v[0].x(), v[1].x(), v[2].x()});
    float max_x = std::max({v[0].x(), v[1].x(), v[2].x()});
    float min_y = std::min({v[0].y(), v[1].y(), v[2].y()});
    float max_y = std::max({v[0].y(), v[1].y(), v[2].y()});

    // 整数化边界并进行屏幕范围裁剪
    int min_x_idx = std::max(0, (int)std::floor(min_x));
    int max_x_idx = std::min(width - 1, (int)std::ceil(max_x));
    int min_y_idx = std::max(0, (int)std::floor(min_y));
    int max_y_idx = std::min(height - 1, (int)std::ceil(max_y));

    // 2. 遍历包围盒内的所有像素
    for (int x = min_x_idx; x <= max_x_idx; x++) {
        for (int y = min_y_idx; y <= max_y_idx; y++) {
            
            // 检查像素中心点 (x+0.5, y+0.5) 是否在三角形内
            if (insideTriangle(x + 0.5f, y + 0.5f, t.v)) {
                
                // 3. 计算插值的深度值 z
                auto[alpha, beta, gamma] = computeBarycentric2D(x + 0.5f, y + 0.5f, t.v);
                
                // 这里是透视修正插值 (Homework 2 提供的公式)
                float w_reciprocal = 1.0 / (alpha / v[0].w() + beta / v[1].w() + gamma / v[2].w());
                float z_interpolated = alpha * v[0].z() / v[0].w() + beta * v[1].z() / v[1].w() + gamma * v[2].z() / v[2].w();
                z_interpolated *= w_reciprocal;

                // 4. 深度测试
                int index = get_index(x, y);
                // 注意：在 OpenCV 的坐标系中，z 值通常为正且越小越近，
                // 但根据 clear 函数的 infinity 初始化，这里判断 z_interpolated < depth_buf[index]
                if (z_interpolated < depth_buf[index]) {
                    // 更新深度缓冲
                    depth_buf[index] = z_interpolated;
                    
                    // 设置颜色
                    Eigen::Vector3f point(x, y, z_interpolated);
                    set_pixel(point, t.getColor());
                }
            }
        }
    }
}

```

### 关键点说明：

* **像素中心**：我们在判断 `insideTriangle` 时使用 `x + 0.5f` 和 `y + 0.5f`，这是为了确保采样点的准确性。
* **Bounding Box 优化**：直接遍历全屏效率极低，使用 `min/max` 确定的矩形区域可以极大减少计算量。
* **Z-buffer**：`depth_buf` 存储的是当前像素看到的最靠近摄像机的物体的深度。只有当新的插值深度比存的小，才更新。

你想继续了解如何在这个基础上实现 **MSAA (多重采样抗锯齿)** 吗？