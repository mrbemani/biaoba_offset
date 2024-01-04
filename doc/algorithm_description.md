
### 获取基准图像

1. 获取标靶的 N 张连续拍摄图像，计算 N 张图像的平均灰度图像。
2. [定位标靶]图像的位置，获取标靶的矩形包围框。
3. 从矩形包围框中截取标靶的图像，作为基准图像。


### 获取目标图像

1. 获取标靶的 N 张连续拍摄图像，计算 N 张图像的平均灰度图像。
2. 使用基准图像获取到的标靶坐标，从当前图像中截取标靶的图像，作为目标图像。

### 定位标靶

1. 对拍摄到的灰度图像做二值化处理，转换为只有 0 与 255 的二值化图像。
2. 在边缘图像上搜索轮廓，找到最大的轮廓，即为标靶的轮廓。
3. 对轮廓进行椭圆拟合，得到标靶的椭圆区域。其中 $(h,k)$ 为椭圆的中心坐标，$a$ 与 $b$ 分别为椭圆的长轴与短轴，$\theta$ 为椭圆的旋转角度。

$$
\frac{((x - h) \cos \theta + (y - k) \sin \theta)^2}{a^2} + \frac{((x - h) \sin \theta - (y - k) \cos \theta)^2}{b^2} = 1
$$

$$
拟合椭圆的方法为最小二乘法，即最小化下式：
$$

$$
\sum_{i=1}^n \left( \frac{((x_i - h) \cos \theta + (y_i - k) \sin \theta)^2}{a^2} + \frac{((x_i - h) \sin \theta - (y_i - k) \cos \theta)^2}{b^2} - 1 \right)^2
$$

4. 获取标靶椭圆区域的矩形包围框，即为标靶的位置。

### 对比目标图像与基准图像的差异

1. 使用 goodFeaturesToTrack 函数对图像的每个像素点，计算其周围窗口内的像素点的梯度，然后计算窗口内所有像素点的梯度的平均值，如果该平均值大于阈值，则认为该像素点是角点。利用通过这种方式获得的角点来作为下一步光流算法的特征点。其中 $I_x$ 与 $I_y$ 分别为图像在 $x$ 与 $y$ 方向上的梯度。

$$
\sum_{x,y \in W} \left| I_x(x,y) \right| + \left| I_y(x,y) \right|
$$


1. 这里由于拍摄的环境是可控的，且标靶为刚体移动，所以我们使用了金字塔 Lucas-Kanade 光流法来计算图像的位移。该算法假设光流是均匀的。其中 $I_x$ 与 $I_y$ 分别为图像在 $x$ 与 $y$ 方向上的梯度，$I_t$ 为图像在时间上的梯度，$v_x$ 与 $v_y$ 分别为图像在 $x$ 与 $y$ 方向上的位移。

$$
\begin{aligned}
& I_x(x,y) v_x + I_y(x,y) v_y + I_t(x,y) = 0 \\
\\
& \begin{bmatrix}
I_x(x_1,y_1) & I_y(x_1,y_1) \\
I_x(x_2,y_2) & I_y(x_2,y_2) \\
\vdots & \vdots \\
I_x(x_n,y_n) & I_y(x_n,y_n) \\
\end{bmatrix}
\begin{bmatrix}
v_x \\
v_y \\
\end{bmatrix}
=
\begin{bmatrix}
-I_t(x_1,y_1) \\
-I_t(x_2,y_2) \\
\vdots \\
-I_t(x_n,y_n) \\
\end{bmatrix}
\end{aligned}
$$

这里我们通过调用 OpenCV 中的 calcOpticalFlowPyrLK 函数来实现:

$$
\begin{aligned}
& calcOpticalFlowPyrLK(prevImg, nextImg, prevPts, nextPts, status, err, winSize, maxLevel, criteria, flags, minEigThreshold) \\
\\
& prevImg: 前一帧图像 \\
& nextImg: 后一帧图像 \\
& prevPts: 前一帧图像中的特征点 \\
& nextPts: 后一帧图像中的特征点 \\
& status: 输出的状态向量，如果特征点在后一帧图像中被找到，则对应的状态为 1，否则为 0 \\
& err: 输出的误差向量，表示前一帧图像中的特征点与后一帧图像中的特征点之间的误差 \\
& winSize: 搜索窗口的大小 \\
& maxLevel: 金字塔的层数 \\
& criteria: 终止条件 \\
& flags: 用于指定计算光流的方法 \\
\end{aligned}
$$

1. 我们将光流得到的 (X,Y) 方向上的位移量做平均，得到图像的 (X,Y) 分量位移。

2. 因为正圆形标靶的透视变换后的椭圆最长边始终会等于标靶的直径，所以我们通过对椭圆拟合的结果获得的椭圆的最长边长来计算图像的实际尺寸与像素尺寸的比例，从而得到图像的实际位移。


