# 标靶检测本地服务调用 API 文档

version: 1.1

author: 史祺

---

## HTTP API 说明

- 所有请求均为 `POST` 或 `GET` 请求
- 所有请求均为 `JSON` 格式
- 所有请求均需要 `Content-Type` 头部, 值为 `application/json`
- 所有请求均需要 `Accept` 头部, 值为 `application/json`

####  Request 格式

```json
// 请求为 JSON 对象
// 根据不同请求，内容格式不同
```

#### Response 格式

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": {},         // 回复数据, 根据不同请求，格式不同. 当没有回复数据时，data 为 null.
}
```


## 获取相机列表

获取可见相机列表

```http
GET /api/v1/camera/list
```

#### Request

```json
// 无需请求体
```

#### Response

```json
// 相机列表
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": {
        "cameras": [
            {
                "id": 1,                // 相机ID
                "name": "camera_1",     // 相机名称
                "ip": "192.168.0.11"    // 相机IP
            },
            {
                "id": 2,
                "name": "camera_2",
                "ip": "192.168.0.12"
            },
            ...
        ]
    }
}
```


## 获取相机画面

通过ID获取相机画面

```http
GET /api/v1/camera/{ID}/get-frame
```

#### Request

```json
// 无需请求体
```

#### Response

返回 MIME Type 为 image/jpeg 格式的图像数据

```json
// JPEG图片数据
```


## 获取相机详细信息

获取当前相机参数/属性。

```http
GET /api/v1/camera/{ID}/get-info
```

#### Request

```json
// 无需请求体
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": {
        "id": 1,                // 相机ID
        "name": "camera_1",     // 相机名称
        "ip": "192.168.0.11",   // 相机IP
        "settings": {
            "yaw": 0.0,             // 相机偏航角 (rad)
            "pitch": 0.0,           // 相机俯仰角 (rad)
            "roll": 0.0,            // 相机滚转角 (rad)
            "exposure": 1000.0,     // 曝光时间 (ms)
            "gain": 100,            // 增益
        },
        "intrinsics": [             // 内参数 (Intrinsics)
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0
        ],
        "distortion": [             // 畸变参数 (Distortion)
            1.0, 0.0, 0.0, 0.0, 0.0
        ],
    }
}
```

## 设置相机参数

设置相机参数: 名字, 曝光时间, 增益。可选，一个或多个属性

```http
POST /api/v1/camera/set
```

#### Request

```json
{
    "id": "camera_id",                // 相机ID
    "set": {
        "name": "camera_1",     // 相机名称
        "yaw": 0.0,             // 相机偏航角 (rad)
        "pitch": 0.0,           // 相机俯仰角 (rad)
        "roll": 0.0,            // 相机滚转角 (rad)
        "x": 0.0,               // 相机位置 x (m)
        "y": 0.0,               // 相机位置 y (m)
        "z": 0.0,               // 相机位置 z (m)
        "standard": 0.0,        // 是否为基准相机 (0:否, 1:是)
        "exposure": 1000.0,     // 曝光时间 (ms)
        "gain": 0               // 增益
    }
}
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": null
}
```

## 相机标定

相机标定，内参数和畸变参数（计算相机内参数和畸变参数可能时间会比较长，为了防止UI阻塞可使用异步调用）

```http
POST /api/v1/camera/calibrate
```

#### Request

```json
{
    "id": "abcde",              // 相机ID
    "checkerboard": {
        "width": 9,             // 棋盘格宽度
        "height": 6,            // 棋盘格高度
        "size": 0.025           // 棋盘格尺寸 (m)
    },
    "images": "/path/to/imgs"   // 图像路径列表
}
```

#### Response

```json
{
    "status": 1,                // 返回状态 1 为成功, 0 为失败
    "data": null
}
```


## 获取指定相机的标靶列表

获取指定相机 (ID) 的标靶列表

```http
GET /api/v1/camera/{ID}/list-markers
```

#### Request

```json
// 无需请求体
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": {
        "markers": [
            {
                "id": 1,                // 标靶ID
                "name": "marker_1",     // 标靶名称
                "type": "circle",       // 标靶类型
                "size": 100,            // 标靶尺寸 (mm)
                "roi": [                // 标靶ROI (归一化): [left, top, width, height]
                    0.52, 0.75, 0.052, 0.052
                ],
                "position": [           // 标靶位置 (m)
                    0.0, 0.0, 0.0
                ],
                "rotation": [           // 标靶旋转 (rad)
                    0.0, 0.0, 0.0
                ]
            },
            {
                "id": 2,
                "name": "marker_2",
                "type": "circle",
                "size": 0.10,
                "roi": [
                    0, 0, 0, 0
                ],
                "position": [
                    0.0, 0.0, 0.0
                ],
                "rotation": [
                    0.0, 0.0, 0.0
                ]
            },
            ...
        ]
    }
}
```


## 设置指定相机的标靶

指定相机（ID），设置其下所有标靶的信息

```http
POST /api/v1/camera/{ID}/set-markers
```

#### Request

```json
{
    "markers": [
        {
            "id": "marker111",      // 标靶ID
            "name": "marker_1",     // 标靶名称
            "type": "circle",       // 标靶类型
            "size": 100,            // 标靶尺寸 (mm)
            "roi": [                // 标靶ROI (归一化): [left, top, width, height]
                0.52, 0.75, 0.052, 0.052
            ],
            "position": [           // 标靶位置 (m)
                0.0, 0.0, 0.0
            ],
            "rotation": [           // 标靶旋转 (rad)
                0.0, 0.0, 0.0
            ]
        },
        {
            "id": "marker222",
            "name": "marker_2",
            "type": "circle",
            "size": 100,
            "roi": [
                0, 0, 0, 0
            ],
            "position": [
                0.0, 0.0, 0.0
            ],
            "rotation": [
                0.0, 0.0, 0.0
            ]
        },
        ...
    ]
}
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": null
}
```


## 初始化标靶检测

设置检测参数，抓拍基准图像

```http
POST /api/v1/camera/capture-reference-image
```

#### Request

```json
{
    "algorithm": "optical-flow",    // 对比算法: elliptic, optical-flow
    "capture": "自动",              // 抓拍方式: 自动, 手动
    "frequency": 30,               // 检测间隔 (分钟)
    "sampleNumber": 5              // 采样数
}
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
}
```



## 开始自动对比

开始自动对比 (自动对比会在后台运行，不会阻塞UI)

```http
POST /api/v1/camera/set-timed-check
```

#### Request

```json
// 无需请求体
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
}
```

## 取消定时对比

取消定时对比

```http
POST /api/v1/camera/cancel-timed-check
```

#### Request

```json
// 无需请求体
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
}
```


## 获取定时对比结果

获取定时对比结果

```http
GET /api/v1/camera/{ID}/get-timed-check-result
```

#### Request

```json
// 无需请求体
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": {
        /* 当定时对比未设置时，data 字段为 null */
        "camera": "abcdefg",                    // 相机ID
        "algorithm": "optical-flow",            // 对比算法: elliptic, optical-flow
        "sample": 10,                           // 采样数
        "interval": 24,                         // 对比间隔 (小时)
        "start_time": "2019-01-01 12:00:00",    // 开始时间, ISO-8601 格式
        "results": [
            "/offset_plots/{camera_id1}/{marker_id1}", // 对比结果图像路径
            "/offset_plots/{camera_id1}/{marker_id2}", // 对比结果图像路径
            // ...
        ]
    }
}
```


## 设置远程服务器信息

设置远程服务器信息

```http
POST /api/v1/remote-server/set
```

#### Request

```json
{
    "server1": "http://xxx.xxx.xxx.xxx/api/call",   // 服务器1地址
    "server2": "http://xxx.xxx.xxx.xxx/api/call",   // 服务器2地址
}
```

#### Response

```json
{
    "status": 1        // 返回状态 1 为成功, 0 为失败
}
```


## 获取远程服务器信息

获取远程服务器信息

```http
GET /api/v1/remote-server/get
```

#### Request

```json
// 无需请求体
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": {
        "server1": "http://xxx.xxx.xxx.xxx/api/call",
        "server2": "http://xxx.xxx.xxx.xxx/api/call"
    }
}
```


