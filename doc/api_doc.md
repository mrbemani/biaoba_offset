# Marker Offset-Check - API Document

version: 1.0

author: David Shi

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
        "exposure": 1000.0,     // 曝光时间 (ms)
        "gain": 100            // 增益
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
    "id": 1,                // 相机ID
    "checkerboard": {
        "width": 9,         // 棋盘格宽度
        "height": 6,        // 棋盘格高度
        "size": 0.025       // 棋盘格尺寸 (m)
    },
    "images": [
        "d:/temp/1.bmp",      // 图片路径, 本地路径或URL
        "d:/temp/2.bmp",
        "d:/temp/3.bmp",
        ...
    ]
}
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": {
        "id": 1,                    // 相机ID
        "name": "camera_1",         // 相机名称
        "ip": "192.168.0.11",       // 相机IP
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
                "size": 0.10,           // 标靶尺寸 (m)
                "roi": [                // 标靶ROI: [left, top, width, height]
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
            "id": 1,                // 标靶ID
            "name": "marker_1",     // 标靶名称
            "type": "circle",       // 标靶类型
            "size": 0.10,           // 标靶尺寸 (m)
            "roi": [                // 标靶ROI: [left, top, width, height]
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
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": null
}
```


## 抓拍标靶基准图像

指定相机 (ID) 抓拍基准图像

```http
POST /api/v1/camera/capture-reference-image
```

#### Request

```json
{
    "camera": 1,            // 相机ID
    "sample": 10,           // 连续抓拍样本数
    "save_path": "d:/temp"  // 保存路径 (可选)
}
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": {
        "reference_images": [
            {
                "camera": 1,                            // 标靶ID
                "marker": 1,                            // 标靶ID
                "reference": "d:/temp/ref_1_1.bmp"      // 图片路径
            },
            {
                "camera": 1,
                "marker": 2,
                "reference": "d:/temp/ref_1_2.bmp"
            },
            ...
        ]
    }
}
```


## 执行对比

指定相机 (ID) 计算标靶偏移

```http
POST /api/v1/camera/check-offset
```

#### Request

```json
{
    "camera": 1,                    // 相机ID
    "sample": 10,                   // 连续抓拍样本数
    "algorithm": "optical-flow"     // 对比算法: elliptic, optical-flow
}
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": {
        "datetime": "2019-01-01 12:00:00",              // 对比时间, ISO-8601 格式
        "camera": 1,                                    // 相机ID
        "marker_offset": [
            {
                "marker": 1,                            // 标靶ID
                "offset": [0.0, 0.0]                    // 偏移量 (m)
            },
            {
                "marker": 2,
                "offset": [0.0, 0.0]
            },
            ...
        ]
    }
}
```

## 设置定时对比

设置定时对比

```http
POST /api/v1/camera/set-timed-check
```

#### Request

```json
{
    "camera": 1,                    // 相机ID
    "algorithm": "optical-flow",    // 对比算法: elliptic, optical-flow
    "sample": 10,                   // 连续抓拍样本数
    "interval": 3600                // 对比间隔 (s)
}
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": {
        "camera": 1,                            // 相机ID
        "algorithm": "optical-flow",            // 对比算法: elliptic, optical-flow
        "sample": 10,                           // 连续抓拍样本数
        "interval": 3600,                       // 对比间隔 (s)
        "start_time": "2019-01-01 12:00:00",    // 开始时间, ISO-8601 格式
    }
}
```

## 取消定时对比

取消定时对比

```http
POST /api/v1/camera/cancel-timed-check
```

#### Request

```json
{
    "camera": 1,        // 相机ID
}
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": null
}
```



## 获取定时对比状态

获取定时对比状态

```http
GET /api/v1/camera/{ID}/get-timed-check
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
        "camera": 1,                            // 相机ID
        "algorithm": "optical-flow",            // 对比算法: elliptic, optical-flow
        "sample": 10,                           // 连续抓拍样本数
        "interval": 3600,                       // 对比间隔 (s)
        "start_time": "2019-01-01 12:00:00",    // 开始时间, ISO-8601 格式
    }
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
        "camera": 1,                            // 相机ID
        "algorithm": "optical-flow",            // 对比算法: elliptic, optical-flow
        "sample": 10,                           // 连续抓拍样本数
        "interval": 24,                         // 对比间隔 (小时)
        "start_time": "2019-01-01 12:00:00",    // 开始时间, ISO-8601 格式
        "results": [
            {
                "datetime": "2019-01-01 12:00:00",              // 对比时间, ISO-8601 格式
                "marker_offset": [
                    {
                        "marker": 1,                            // 标靶ID
                        "offset": [0.0, 0.0]                    // 偏移量 (m)
                    },
                    {
                        "marker": 2,
                        "offset": [0.0, 0.0]
                    },
                    ...
                ]
            },
            ...
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
    "address": "192.168.0.1",   // 服务器地址
    "port": 8080,               // 服务器端口
    "protocol": "http"          // 服务器协议: http, https
}
```

#### Response

```json
{
    "status": 1,        // 返回状态 1 为成功, 0 为失败
    "data": null
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
        "address": "xxx.xxx.xxx.xxx",
        "port": 8080,
        "protocol": "http"
    }
}
```


