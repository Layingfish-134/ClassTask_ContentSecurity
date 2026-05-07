# 班级考勤系统 API 交互协议

版本：v1.0  
适用阶段：阶段一接口联调前置协议  

## 1. 通用约定

### 1.1 基础信息

| 项目 | 约定 |
|------|------|
| Base URL | `/api` |
| 请求格式 | `application/json` |
| 图片传输 | Base64 字符串，字段名统一使用 `*_base64` |
| 认证方式 | `Authorization: Bearer <access_token>` |
| 字段命名 | `snake_case` |
| 时间格式 | ISO8601，示例：`2026-05-06T09:30:00+08:00` |
| 分页方式 | 流水型列表统一使用游标分页，不使用深度 `OFFSET` 分页 |

### 1.2 统一成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "request_id": "req_202605060930000001"
}
```

### 1.3 统一错误响应

```json
{
  "code": 40101,
  "message": "JWT令牌已过期",
  "data": null,
  "request_id": "req_202605060930000001"
}
```

### 1.4 分页响应格式

```json
{
  "records": [],
  "size": 20,
  "next_cursor": "eyJ0aW1lIjoiMjAyNi0wNS0wNlQwOTozMDowNSswODowMCIsImlkIjoxMDAwMX0=",
  "has_more": true
}
```

游标规则：

- `size` 默认 `20`，最大 `100`。
- `cursor` 为空表示第一页。
- `next_cursor` 由后端生成并编码，前端不得自行拼接。
- 流水型数据按稳定排序字段做 Keyset Pagination，例如考勤记录按 `attendance_time DESC, record_id DESC`。
- 禁止使用大页码深度分页，避免 `LIMIT offset, size` 在大数据量下造成慢查询。

### 1.5 枚举值

| 枚举 | 可选值 | 说明 |
|------|--------|------|
| `role` | `teacher`, `student`, `admin` | 用户角色 |
| `attendance_status` | `0`, `1` | `0` 失败，`1` 成功 |
| `emotion` | `happy`, `neutral`, `sad`, `angry`, `tired`, `surprised`, `unknown` | 情绪类型 |
| `image_format` | `jpg`, `jpeg`, `png` | 图片格式 |
| `source_type` | `attendance`, `group_photo` | 情绪来源 |
| `spoof_type` | `photo_attack`, `video_replay`, `screen_replay`, `unknown` | 活体攻击类型 |
| `failure_reason` | `no_face`, `multiple_faces`, `liveness_failed`, `face_not_matched`, `recognition_timeout`, `invalid_image`, `unknown` | 识别失败原因 |

### 1.6 业务错误码

| HTTP 状态 | 业务码 | message 示例 | 场景 |
|-----------|--------|--------------|------|
| 400 | `40000` | 请求参数错误 | 通用参数错误 |
| 400 | `40001` | 缺少必要字段 | 必填字段为空 |
| 400 | `40002` | 图片格式不支持 | 非 jpg/png 图片 |
| 413 | `40003` | 文件大小超过限制 | 超过 10MB |
| 400 | `40004` | Excel模板格式错误 | 批量导入模板列缺失或格式不符 |
| 400 | `40005` | 人脸图片压缩包格式错误 | ZIP缺失、损坏或图片命名不匹配 |
| 401 | `40100` | 未登录或令牌无效 | 缺少 token |
| 401 | `40101` | JWT令牌已过期 | token 过期 |
| 401 | `40102` | 账号已停用或令牌已失效 | `user_info.status=0` 或 `token_version` 不一致 |
| 403 | `40300` | 无权限访问该资源 | 学生访问教师接口 |
| 403 | `40301` | 无权限访问该文件 | 访问不属于自己的考勤图片或合照 |
| 404 | `40400` | 资源不存在 | 学生或记录不存在 |
| 409 | `40900` | 数据已存在 | 学号或用户名重复 |
| 422 | `42201` | 未检测到人脸 | 活体/识别前置失败 |
| 422 | `42202` | 检测到多张人脸 | 单人考勤图片包含多人 |
| 422 | `42203` | 活体检测未通过 | 通用活体失败 |
| 422 | `42204` | 疑似照片攻击 | 活体检测照片攻击 |
| 422 | `42205` | 疑似视频重放攻击 | 活体检测视频攻击 |
| 422 | `42206` | 人脸匹配失败 | 未匹配到学生 |
| 504 | `42207` | 识别服务超时 | 算法服务超时 |
| 422 | `42208` | 人脸库导入部分失败 | 批量导入时部分学生人脸特征提取失败 |
| 500 | `50000` | 服务器内部错误 | 未知异常 |
| 503 | `50300` | 数据库连接不可用 | MySQL 或 Redis 异常 |

### 1.7 安全与性能约束

**JWT 状态校验**

- JWT 必须携带 `user_id`、`role`、`student_id` 和 `token_version`。
- 每次访问受保护接口时，后端不能只校验 JWT 签名，还必须检查 `user_info.status=1`。
- 后端必须校验 JWT 中的 `token_version` 与 `user_info.token_version` 一致。
- 删除/停用用户、重置密码、强制下线时，必须递增 `user_info.token_version`，使旧 JWT 立即失效。

**人脸向量检索**

- MySQL 中的 `student_info.face_feature` 只用于持久化备份和缓存重建，不用于每次考勤时全表扫描。
- 考勤识别时，算法服务必须按班级或活跃学生范围加载人脸特征到内存、Redis 或 FAISS 等向量索引中。
- 新增学生、更新人脸、批量导入后，后端必须刷新对应班级的人脸特征缓存或递增缓存版本。
- 禁止在高频考勤接口中执行“读取全班 JSON 特征到 Python 后逐条解析”的 O(N) 数据库查询流程。

**图片访问**

- `image_path`、`photo_path` 仅为服务器内部存储键，不得直接返回给前端作为公开 URL。
- 前端只能通过受鉴权保护的文件接口访问图片，例如 `GET /api/files/{file_id}`。
- 文件接口必须做权限校验、路径归一化和目录边界检查，禁止暴露 `/uploads` 静态目录。
- 文件下载/预览 URL 应短时有效，禁止可枚举的永久公开链接。

## 2. 权限矩阵

| 接口模块 | teacher | student | admin |
|----------|---------|---------|-------|
| 登录/刷新令牌 | 允许 | 允许 | 允许 |
| 发起本人考勤 | 允许 | 允许 | 允许 |
| 查询本人考勤 | 允许 | 允许 | 允许 |
| 查询全班考勤 | 允许 | 禁止 | 允许 |
| 学生新增/修改/删除 | 允许 | 禁止 | 允许 |
| 学生与人脸库批量导入 | 允许 | 禁止 | 允许 |
| 合照上传识别 | 允许 | 禁止 | 允许 |
| 情绪统计 | 允许 | 仅本人 | 允许 |
| Excel 报表导出 | 允许 | 禁止 | 允许 |

## 3. 认证接口

### 3.1 登录

`POST /api/auth/login`

请求：

```json
{
  "username": "teacher01",
  "password": "123456"
}
```

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "expires_in": 7200,
    "user": {
      "user_id": "u_teacher_001",
      "username": "teacher01",
      "role": "teacher",
      "student_id": null,
      "token_version": 1
    }
  },
  "request_id": "req_202605060930000001"
}
```

### 3.2 刷新令牌

`POST /api/auth/refresh`

请求头：

```http
Authorization: Bearer <refresh_token>
```

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOi...",
    "expires_in": 7200
  },
  "request_id": "req_202605060930000002"
}
```

## 4. 考勤接口

### 4.1 发起考勤

`POST /api/attendance/checkin`

请求：

```json
{
  "image_base64": "/9j/4AAQSkZJRgABAQ...",
  "image_format": "jpg",
  "capture_time": "2026-05-06T09:30:00+08:00",
  "device_id": "web_camera_001",
  "idempotency_key": "checkin_2024001_20260506093000_web_camera_001"
}
```

安全备注：

- `capture_time` 仅作前端采集耗时和问题排查参考，不作为最终考勤时间。
- 实际 `attendance_time` 必须以服务端接收到请求并完成识别记录落库的时间为准，防止学生修改本地设备时间进行代签或补签。
- `idempotency_key` 由前端在点击打卡时生成，同一次打卡重试必须复用同一个值。
- 后端必须对 `idempotency_key` 做唯一性保护：如果收到重复键，直接返回第一次处理结果或“重复提交”提示，不得再次调用活体检测和人脸识别模型。
- 前端提交按钮在请求完成前必须禁用，并显示 Loading 状态，避免用户连续点击触发高成本 CV 推理。

成功响应：

```json
{
  "code": 200,
  "message": "考勤成功",
  "data": {
    "record_id": 10001,
    "student_id": "2024001",
    "name": "张三",
    "class_name": "计科2401班",
    "status": 1,
    "confidence": 98.52,
    "liveness_passed": true,
    "liveness_score": 97.30,
    "spoof_type": null,
    "failure_reason": null,
    "emotion": "happy",
    "emotion_confidence": 91.20,
    "attendance_time": "2026-05-06T09:30:05+08:00",
    "image_file_id": "file_attendance_10001",
    "image_preview_url": "/api/files/file_attendance_10001?purpose=preview",
    "idempotency_key": "checkin_2024001_20260506093000_web_camera_001"
  },
  "request_id": "req_202605060930000003"
}
```

活体失败响应：

```json
{
  "code": 42204,
  "message": "疑似照片攻击",
  "data": {
    "status": 0,
    "liveness_passed": false,
    "liveness_score": 36.20,
    "spoof_type": "photo_attack",
    "failure_reason": "liveness_failed"
  },
  "request_id": "req_202605060930000004"
}
```

### 4.2 查询考勤记录

`GET /api/attendance/records`

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `student_id` | string | 否 | 学号筛选 |
| `class_name` | string | 否 | 班级筛选，学生角色不可用 |
| `start_time` | string | 否 | 开始时间 |
| `end_time` | string | 否 | 结束时间 |
| `status` | int | 否 | `0` 失败，`1` 成功 |
| `cursor` | string | 否 | 上一页返回的 `next_cursor`，第一页不传 |
| `size` | int | 否 | 默认 `20`，最大 `100` |

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "records": [
      {
        "record_id": 10001,
        "student_id": "2024001",
        "name": "张三",
        "class_name": "计科2401班",
        "status": 1,
        "confidence": 98.52,
        "liveness_passed": true,
        "liveness_score": 97.30,
        "emotion": "happy",
        "emotion_confidence": 91.20,
        "attendance_time": "2026-05-06T09:30:05+08:00"
      }
    ],
    "size": 20,
    "next_cursor": "eyJ0aW1lIjoiMjAyNi0wNS0wNlQwOTozMDowNSswODowMCIsImlkIjoxMDAwMX0=",
    "has_more": false
  },
  "request_id": "req_202605060930000005"
}
```

## 5. 合照识别接口

### 5.1 上传合照并识别

`POST /api/group-photos/recognize`

请求：

```json
{
  "photo_base64": "/9j/4AAQSkZJRgABAQ...",
  "image_format": "jpg",
  "photo_name": "班会合照.jpg",
  "activity_name": "主题班会",
  "activity_time": "2026-05-06T15:00:00+08:00"
}
```

时序规则：

- `activity_time` 表示照片对应活动实际发生时间，可以早于上传时间。
- 合照识别明细中的 `class_name` 必须按 `activity_time` 查询 `class_enrollment_history` 得到历史班级快照，不能使用上传/识别当天的当前班级。
- `emotion_record.detected_at` 对合照来源建议使用 `activity_time`，保证情绪统计按活动发生时间归档。
- 如果 `activity_time` 为空，后端才允许退化使用服务端上传时间。

成功响应：

```json
{
  "code": 200,
  "message": "识别完成",
  "data": {
    "photo_id": 501,
    "activity_name": "主题班会",
    "total_faces": 5,
    "recognized_count": 4,
    "unrecognized_count": 1,
    "details": [
      {
        "detail_id": 9001,
        "student_id": "2024001",
        "name": "张三",
        "class_name": "计科2401班",
        "status": 1,
        "confidence": 96.40,
        "face_box": {
          "x": 120,
          "y": 80,
          "width": 96,
          "height": 96
        },
        "emotion": "neutral",
        "emotion_confidence": 88.10
      }
    ]
  },
  "request_id": "req_202605060930000006"
}
```

### 5.2 查询合照识别记录

`GET /api/group-photos/records`

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `activity_name` | string | 否 | 活动名称 |
| `class_name` | string | 否 | 班级 |
| `start_time` | string | 否 | 开始时间 |
| `end_time` | string | 否 | 结束时间 |
| `cursor` | string | 否 | 上一页返回的 `next_cursor`，第一页不传 |
| `size` | int | 否 | 默认 `20`，最大 `100` |

成功响应中的 `data` 使用统一分页格式，`records` 单项字段如下：

```json
{
  "photo_id": 501,
  "photo_name": "班会合照.jpg",
  "activity_name": "主题班会",
  "activity_time": "2026-05-06T15:00:00+08:00",
  "total_faces": 5,
  "recognized_count": 4,
  "unrecognized_count": 1,
  "created_at": "2026-05-06T15:01:20+08:00"
}
```

### 5.3 查询合照识别明细

`GET /api/group-photos/{photo_id}/details`

成功响应中的 `data.records` 单项字段与 `5.1` 的 `details` 一致。

## 6. 情绪统计接口

### 6.1 获取情绪统计数据

`GET /api/emotions/statistics`

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `class_name` | string | 否 | 班级筛选 |
| `student_id` | string | 否 | 学号筛选 |
| `source_type` | string | 否 | `attendance` 或 `group_photo` |
| `start_time` | string | 是 | 开始时间 |
| `end_time` | string | 是 | 结束时间 |

响应固定返回两类数据：

- `distribution`：所选时间段内的情绪占比分布，用于饼图。
- `trend`：按日期汇总的情绪变化趋势，用于折线图或柱状图。
- `distribution.ratio` 使用百分比数值，`60.00` 表示 60%。

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "distribution": [
      {
        "emotion": "neutral",
        "count": 60,
        "ratio": 60.00
      },
      {
        "emotion": "happy",
        "count": 30,
        "ratio": 30.00
      },
      {
        "emotion": "tired",
        "count": 10,
        "ratio": 10.00
      }
    ],
    "trend": [
      {
        "date": "2026-05-06",
        "happy": 12,
        "neutral": 24,
        "sad": 2,
        "angry": 0,
        "tired": 4,
        "surprised": 1,
        "unknown": 0
      }
    ]
  },
  "request_id": "req_202605060930000007"
}
```

## 7. 学生管理接口

### 7.1 新增学生

`POST /api/students`

请求：

```json
{
  "student_id": "2024001",
  "name": "张三",
  "class_name": "计科2401班",
  "face_image_base64": "/9j/4AAQSkZJRgABAQ...",
  "image_format": "jpg",
  "username": "2024001",
  "password": "123456"
}
```

字段规则：

| 字段 | 必填 | 说明 |
|------|------|------|
| `student_id` | 是 | 学号，需唯一 |
| `name` | 是 | 姓名 |
| `class_name` | 是 | 班级 |
| `face_image_base64` | 是 | 人脸图片 Base64 |
| `image_format` | 是 | `jpg`、`jpeg` 或 `png` |
| `username` | 否 | 学生账号用户名，默认使用学号 |
| `password` | 否 | 初始密码；后端只能保存密码哈希，不能明文入库 |

成功响应：

```json
{
  "code": 201,
  "message": "创建成功",
  "data": {
    "student_id": "2024001",
    "name": "张三",
    "class_name": "计科2401班",
    "account": {
      "user_id": "u_2024001",
      "username": "2024001",
      "role": "student",
      "created": true
    },
    "created_at": "2026-05-06T09:30:00+08:00"
  },
  "request_id": "req_202605060930000008"
}
```

处理规则：

- 新增学生时，后端必须在同一个数据库事务中同时写入 `student_info` 和 `user_info`。
- `user_info.role` 必须为 `student`，`user_info.student_id` 必须关联本次新增的 `student_info.student_id`。
- 同一事务中还必须写入 `class_enrollment_history`，记录学生进入当前班级的 `enrolled_at`。
- 如果学生信息、人脸特征、账号或班级归属历史任一步写入失败，整个事务必须回滚，避免出现“有学生无账号”或历史班级分母缺失的脏数据。
- `username` 为空时默认使用 `student_id`；`password` 为空时使用后端配置的默认初始密码或一次性重置密码。
- 数据库层约束要求：`role='student'` 的账号必须绑定 `student_id`；`teacher` / `admin` 账号不得绑定 `student_id`。
- 账号唯一性只约束活跃账号：软删除账号不会继续占用 `username`，但如果 `student_id` 已存在于 `student_info`，后端应走恢复/更新流程，而不是盲目插入重复学生主键。

### 7.2 批量导入学生与人脸库

`POST /api/students/batch-import`

请求格式：

| 项目 | 值 |
|------|----|
| Content-Type | `multipart/form-data` |
| 权限 | `teacher`, `admin` |
| 文件大小限制 | 单次建议不超过 50MB |

表单参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `student_excel` | file | 是 | 学生基础信息 Excel，建议 `.xlsx` |
| `face_zip` | file | 是 | 学生人脸图片 ZIP 包 |
| `class_name` | string | 否 | 批量指定班级；如果 Excel 已包含班级列，可不传 |
| `match_rule` | string | 否 | 图片匹配规则，默认 `student_id_filename` |
| `overwrite_existing` | boolean | 否 | 是否覆盖已存在学生和人脸特征，默认 `false` |

Excel 模板字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `student_id` | 是 | 学号，需唯一 |
| `name` | 是 | 姓名 |
| `class_name` | 是 | 班级 |
| `username` | 否 | 学生账号用户名，默认使用学号 |
| `password` | 否 | 初始密码，后端需加密存储 |

ZIP 图片命名约定：

| 规则 | 示例 | 说明 |
|------|------|------|
| `student_id_filename` | `2024001.jpg` | 文件名与学号一致 |
| `student_id_folder` | `2024001/face1.jpg` | 每个学生一个文件夹，可放多张人脸图 |

成功响应：

```json
{
  "code": 200,
  "message": "批量导入完成",
  "data": {
    "import_batch_id": "batch_202605061630000001",
    "total_rows": 50,
    "success_count": 48,
    "failed_count": 2,
    "created_count": 45,
    "updated_count": 3,
    "face_feature_extracted_count": 48,
    "failures": [
      {
        "row": 12,
        "student_id": "2024012",
        "reason": "未找到匹配的人脸图片"
      },
      {
        "row": 27,
        "student_id": "2024027",
        "reason": "人脸特征提取失败"
      }
    ]
  },
  "request_id": "req_202605061630000001"
}
```

处理规则：

- 后端必须先校验 Excel 模板字段，再校验 ZIP 文件完整性。
- 学号是学生唯一标识，重复学号按 `overwrite_existing` 决定拒绝或覆盖。
- 人脸特征提取失败时，允许部分成功导入，并在 `failures` 中返回失败明细。
- 每个成功导入的学生都必须同步写入 `student_info` 和 `user_info`，并创建 `role='student'` 的学生账号。
- 批量导入建议以“单个学生”为事务边界：同一名学生的基本信息、人脸特征、学生账号和班级归属历史必须同一事务提交；该学生失败则回滚该学生，不影响其他学生继续导入。
- 该接口用于“班级人脸库可批量导入”评分点，报告中可归入系统易用性和数据初始化能力。
- 批量导入会连续调用人脸检测和特征提取模型，纯 CPU 环境可能耗时 10-20 秒甚至更久。
- 前端调用该接口时，Axios `timeout` 建议至少设置为 `60000ms`，并务必显示全局 Loading 遮罩层，避免用户重复提交。

### 7.3 查询学生列表

`GET /api/students`

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `class_name` | string | 否 | 班级 |
| `keyword` | string | 否 | 学号或姓名关键字 |
| `cursor` | string | 否 | 上一页返回的 `next_cursor`，第一页不传 |
| `size` | int | 否 | 默认 `20`，最大 `100` |

### 7.4 更新学生

`PUT /api/students/{student_id}`

请求：

```json
{
  "name": "张三",
  "class_name": "计科2401班",
  "face_image_base64": "/9j/4AAQSkZJRgABAQ...",
  "image_format": "jpg"
}
```

处理规则：

- 如果只更新姓名或人脸图片，不需要变更班级归属历史。
- 如果 `class_name` 发生变化，后端必须在同一个事务中：
  - 更新 `student_info.class_name`。
  - 将旧的 `class_enrollment_history` 当前记录写入 `left_at`。
  - 新增一条新班级的 `class_enrollment_history` 记录。
- 班级变更历史用于保证历史出勤率分母不会被当前班级状态污染。

### 7.5 删除学生

`DELETE /api/students/{student_id}`

删除策略：

- 该接口默认执行逻辑删除，不直接物理删除学生历史数据。
- 后端必须在同一个事务中：
  - 将 `student_info.status` 更新为 `0`。
  - 将对应 `user_info.status` 更新为 `0`，禁止该学生继续登录。
  - 将对应 `user_info.token_version` 递增，使该学生已签发 JWT 立即失效。
  - 将该学生当前 `class_enrollment_history.left_at` 更新为服务端当前时间。
- 历史考勤、合照识别和情绪记录保留，用于历史报表查询。

成功响应：

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null,
  "request_id": "req_202605060930000009"
}
```

## 8. 文件访问接口

### 8.1 受控预览或下载文件

`GET /api/files/{file_id}`

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `purpose` | string | 否 | `preview` 或 `download`，默认 `preview` |

处理规则：

- 该接口必须要求登录，不允许匿名访问。
- 后端必须根据 `file_id` 查找内部 `image_path` 或 `photo_path`，不得把客户端传入内容拼接为磁盘路径。
- 后端必须做路径归一化，确保最终路径仍位于允许的上传根目录内，防止 `../` 目录遍历。
- 学生只能访问本人考勤图片或授权可见的合照；教师和管理员按权限访问班级或活动文件。
- 不得开放 `/uploads/**` 这类公开静态目录。

成功响应：

| 项目 | 值 |
|------|----|
| HTTP 状态 | `200` |
| Content-Type | 图片实际 MIME 类型 |
| Body | 图片二进制流 |

错误响应仍使用统一 JSON 错误响应，例如无权访问返回 `40301`。

## 9. 报表导出接口

### 9.1 导出考勤报表

`GET /api/reports/attendance/export`

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `class_name` | string | 否 | 班级 |
| `start_time` | string | 是 | 开始时间 |
| `end_time` | string | 是 | 结束时间 |

成功响应：

| 项目 | 值 |
|------|----|
| HTTP 状态 | `200` |
| Content-Type | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| Content-Disposition | `attachment; filename="attendance_report.xlsx"` |
| Body | Excel 二进制流 |

错误响应仍使用统一 JSON 错误响应。

### 9.2 导出活动参与频次报表

`GET /api/reports/activity-frequency/export`

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `class_name` | string | 否 | 班级 |
| `activity_name` | string | 否 | 活动名称 |
| `start_time` | string | 否 | 开始时间 |
| `end_time` | string | 否 | 结束时间 |

成功响应与 `9.1` 一致，文件名建议为 `activity_frequency_report.xlsx`。

## 10. 接口验收清单

| 编号 | 验收项 | 预期结果 |
|------|--------|----------|
| A-01 | 登录成功 | 返回 access_token、refresh_token 和用户角色 |
| A-02 | 令牌过期 | 返回 `40101` |
| A-03 | 缺少必填字段 | 返回 `40001` |
| A-04 | 非图片上传 | 返回 `40002` |
| A-05 | 图片超过 10MB | 返回 `40003` |
| A-06 | 批量导入 Excel 模板错误 | 返回 `40004` |
| A-07 | 批量导入 ZIP 损坏或命名不匹配 | 返回 `40005` |
| A-08 | 批量导入部分人脸失败 | 返回 `42208` 和失败明细 |
| A-09 | 单个新增学生 | 同一事务写入 `student_info` 和 `user_info(role='student')` |
| A-10 | 批量导入学生 | 每个成功学生都有对应 `user_info(role='student')` |
| A-11 | 考勤图片无人脸 | 返回 `42201` |
| A-12 | 单人考勤图片多张脸 | 返回 `42202` |
| A-13 | 疑似照片攻击 | 返回 `42204` |
| A-14 | 疑似视频攻击 | 返回 `42205` |
| A-15 | 人脸匹配失败 | 返回 `42206` |
| A-16 | 识别服务超时 | 返回 `42207` 或 HTTP `504` |
| A-17 | 学生访问教师接口 | 返回 `40300` |
| A-18 | 教师查询全班数据 | 返回分页数据 |
| A-19 | 学生查询本人数据 | 只返回本人记录 |
| A-20 | 客户端伪造 `capture_time` | `attendance_time` 仍以服务端时间为准 |
| A-21 | 连续点击重复考勤 | 相同 `idempotency_key` 不重复触发识别模型 |
| A-22 | 上传历史合照 | 明细 `class_name` 按 `activity_time` 对应历史班级归属计算 |
| A-23 | 软删除后复用用户名 | 已停用账号不阻塞新活跃账号使用同名 `username` |
| A-24 | 数据库连接异常 | 返回 `50300`，后端进程不崩溃 |
