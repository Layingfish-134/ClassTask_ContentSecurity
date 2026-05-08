# 班级考勤系统 - 后端API接口文档

## 1. 基础信息

### 1.1 服务地址
- **开发环境**: `http://localhost:5000/api`
- **认证方式**: JWT Token（Bearer Token）

### 1.2 响应格式

**成功响应**:
```json
{
    "code": 200,
    "message": "操作成功",
    "data": { ... }
}
```

**分页响应**:
```json
{
    "code": 200,
    "message": "查询成功",
    "data": {
        "records": [...],
        "total": 100,
        "page": 1,
        "size": 20
    }
}
```

**错误响应**:
```json
{
    "code": 400,
    "message": "错误信息",
    "data": null
}
```

### 1.3 默认用户
| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | teacher |
| teacher001 | 123456 | teacher |

---

## 2. 认证接口

### 2.1 用户登录

**接口地址**: `POST /api/login`

**功能描述**: 用户登录获取JWT令牌

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | String | 是 | 用户名 |
| password | String | 是 | 密码 |

**请求示例**:
```json
{
    "username": "admin",
    "password": "admin123"
}
```

**成功响应**:
```json
{
    "code": 200,
    "message": "登录成功",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user_id": "admin",
        "role": "teacher"
    }
}
```

---

### 2.2 刷新令牌

**接口地址**: `POST /api/refresh`

**功能描述**: 使用refresh_token获取新的access_token

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| refresh_token | String | 是 | 刷新令牌 |

**请求示例**:
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**成功响应**:
```json
{
    "code": 200,
    "message": "令牌刷新成功",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}
```

---

### 2.3 获取当前用户信息

**接口地址**: `GET /api/user/current`

**功能描述**: 获取当前登录用户信息（需要JWT认证）

**请求头**:
```
Authorization: Bearer <access_token>
```

**成功响应**:
```json
{
    "code": 200,
    "message": "操作成功",
    "data": {
        "user_id": "admin",
        "username": "admin",
        "role": "teacher"
    }
}
```

---

## 3. 考勤接口

### 3.1 发起考勤

**接口地址**: `POST /api/attendance/checkin`

**功能描述**: 上传人脸图像，执行活体检测和人脸比对，完成考勤

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| image_base64 | String | 是 | 人脸图像Base64编码 |
| image_format | String | 是 | 图像格式（jpg/png） |

**请求示例**:
```json
{
    "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "image_format": "jpg"
}
```

**成功响应**:
```json
{
    "code": 200,
    "message": "考勤成功",
    "data": {
        "status": 1,
        "student_id": "2024001",
        "name": "张三",
        "class_name": "计算机2401班",
        "attendance_time": "2024-01-15T08:30:45",
        "confidence": 98.5,
        "emotion": "happy",
        "emotion_confidence": 92.3
    }
}
```

**失败响应**:
```json
{
    "code": 400,
    "message": "考勤失败，未匹配到学生信息",
    "data": {
        "status": 0
    }
}
```

---

### 3.2 查询考勤记录

**接口地址**: `GET /api/attendance/records`

**功能描述**: 查询考勤记录列表，支持多条件筛选

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| student_id | String | 否 | 学号筛选 |
| class_name | String | 否 | 班级筛选 |
| start_time | String | 否 | 开始时间（ISO8601格式） |
| end_time | String | 否 | 结束时间（ISO8601格式） |
| status | Integer | 否 | 状态筛选（0失败/1成功） |
| page | Integer | 否 | 页码，默认1 |
| size | Integer | 否 | 每页数量，默认20 |

**请求示例**:
```
GET /api/attendance/records?class_name=计算机2401班&status=1&page=1&size=20
```

**成功响应**:
```json
{
    "code": 200,
    "message": "查询成功",
    "data": {
        "records": [
            {
                "record_id": 1,
                "student_id": "2024001",
                "name": "张三",
                "class_name": "计算机2401班",
                "status": 1,
                "confidence": 98.5,
                "emotion": "happy",
                "emotion_confidence": 92.3,
                "attendance_time": "2024-01-15T08:30:45"
            }
        ],
        "total": 100,
        "page": 1,
        "size": 20
    }
}
```

---

## 4. 学生管理接口

### 4.1 查询学生列表

**接口地址**: `GET /api/students`

**功能描述**: 查询学生列表，支持分页和筛选

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| class_name | String | 否 | 班级筛选 |
| keyword | String | 否 | 学号或姓名关键词 |
| page | Integer | 否 | 页码，默认1 |
| size | Integer | 否 | 每页数量，默认20 |

**请求示例**:
```
GET /api/students?class_name=计算机2401班&keyword=张&page=1&size=20
```

**成功响应**:
```json
{
    "code": 200,
    "message": "查询成功",
    "data": {
        "records": [
            {
                "student_id": "2024001",
                "name": "张三",
                "class_name": "计算机2401班",
                "created_at": "2024-01-01T00:00:00"
            }
        ],
        "total": 50,
        "page": 1,
        "size": 20
    }
}
```

---

### 4.2 创建学生

**接口地址**: `POST /api/students`

**功能描述**: 创建新学生并录入人脸特征

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| student_id | String | 是 | 学号 |
| name | String | 是 | 姓名 |
| class_name | String | 是 | 班级 |
| face_image_base64 | String | 是 | 人脸图像Base64编码 |

**请求示例**:
```json
{
    "student_id": "2024001",
    "name": "张三",
    "class_name": "计算机2401班",
    "face_image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**成功响应**:
```json
{
    "code": 201,
    "message": "学生创建成功",
    "data": {
        "student_id": "2024001",
        "name": "张三",
        "class_name": "计算机2401班",
        "created_at": "2024-01-15T10:00:00"
    }
}
```

---

### 4.3 查询单个学生

**接口地址**: `GET /api/students/{student_id}`

**功能描述**: 根据学号查询单个学生信息

**请求头**:
```
Authorization: Bearer <access_token>
```

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| student_id | String | 学号 |

**请求示例**:
```
GET /api/students/2024001
```

**成功响应**:
```json
{
    "code": 200,
    "message": "操作成功",
    "data": {
        "student_id": "2024001",
        "name": "张三",
        "class_name": "计算机2401班",
        "created_at": "2024-01-01T00:00:00"
    }
}
```

**失败响应**:
```json
{
    "code": 404,
    "message": "学号 2024001 不存在",
    "data": null
}
```

---

### 4.4 更新学生信息

**接口地址**: `PUT /api/students/{student_id}`

**功能描述**: 更新学生信息

**请求头**:
```
Authorization: Bearer <access_token>
```

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| student_id | String | 学号 |

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | String | 否 | 姓名 |
| class_name | String | 否 | 班级 |
| face_image_base64 | String | 否 | 人脸图像（更新人脸特征时传） |

**请求示例**:
```json
{
    "name": "张三（已修改）",
    "class_name": "计算机2402班"
}
```

**成功响应**:
```json
{
    "code": 200,
    "message": "学生信息更新成功",
    "data": {
        "student_id": "2024001",
        "name": "张三（已修改）",
        "class_name": "计算机2402班",
        "created_at": "2024-01-01T00:00:00"
    }
}
```

---

### 4.5 删除学生

**接口地址**: `DELETE /api/students/{student_id}`

**功能描述**: 删除学生信息

**请求头**:
```
Authorization: Bearer <access_token>
```

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| student_id | String | 学号 |

**请求示例**:
```
DELETE /api/students/2024001
```

**成功响应**:
```json
{
    "code": 200,
    "message": "学生删除成功",
    "data": null
}
```

---

## 5. 合照识别接口

### 5.1 上传合照并识别

**接口地址**: `POST /api/group-photo/recognize`

**功能描述**: 上传合照图片，检测并识别图片中的所有学生

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| image_base64 | String | 是 | 合照图像Base64编码 |
| image_format | String | 是 | 图像格式（jpg/png） |
| activity_name | String | 否 | 活动名称 |

**请求示例**:
```json
{
    "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "image_format": "jpg",
    "activity_name": "元旦晚会"
}
```

**成功响应**:
```json
{
    "code": 200,
    "message": "识别完成",
    "data": {
        "photo_id": 1,
        "photo_name": "group_photo_20240115.jpg",
        "activity_name": "元旦晚会",
        "recognized_count": 30,
        "total_faces": 32,
        "students": [
            {
                "student_id": "2024001",
                "name": "张三",
                "class_name": "计算机2401班",
                "confidence": 95.2,
                "emotion": "happy",
                "emotion_confidence": 88.5
            }
        ]
    }
}
```

---

### 5.2 查询合照识别记录

**接口地址**: `GET /api/group-photo/records`

**功能描述**: 查询合照识别记录列表

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| activity_name | String | 否 | 活动名称筛选 |
| start_time | String | 否 | 开始时间（ISO8601格式） |
| end_time | String | 否 | 结束时间（ISO8601格式） |
| page | Integer | 否 | 页码，默认1 |
| size | Integer | 否 | 每页数量，默认20 |

**请求示例**:
```
GET /api/group-photo/records?activity_name=元旦晚会&page=1&size=20
```

**成功响应**:
```json
{
    "code": 200,
    "message": "查询成功",
    "data": {
        "records": [
            {
                "photo_id": 1,
                "photo_name": "group_photo_20240115.jpg",
                "activity_name": "元旦晚会",
                "recognized_count": 30,
                "total_faces": 32,
                "created_at": "2024-01-15T14:00:00"
            }
        ],
        "total": 10,
        "page": 1,
        "size": 20
    }
}
```

---

## 6. 情绪分析接口

### 6.1 获取情绪统计数据

**接口地址**: `GET /api/emotion/statistics`

**功能描述**: 获取情绪分布统计数据，支持多维度筛选

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| class_name | String | 否 | 班级筛选 |
| activity_type | String | 否 | 活动类型筛选 |
| start_time | String | 否 | 开始时间（ISO8601格式） |
| end_time | String | 否 | 结束时间（ISO8601格式） |

**请求示例**:
```
GET /api/emotion/statistics?class_name=计算机2401班&start_time=2024-01-01T00:00:00&end_time=2024-01-31T23:59:59
```

**成功响应**:
```json
{
    "code": 200,
    "message": "操作成功",
    "data": {
        "total_count": 150,
        "distribution": {
            "happy": 65,
            "sad": 15,
            "surprised": 20,
            "angry": 8,
            "neutral": 42
        }
    }
}
```

---

## 7. 报表导出接口

### 7.1 导出考勤报表

**接口地址**: `GET /api/reports/attendance/export`

**功能描述**: 导出考勤统计报表（Excel格式）

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| class_name | String | 否 | 班级筛选 |
| start_time | String | 是 | 开始时间（ISO8601格式） |
| end_time | String | 是 | 结束时间（ISO8601格式） |

**请求示例**:
```
GET /api/reports/attendance/export?class_name=计算机2401班&start_time=2024-01-01T00:00:00&end_time=2024-01-31T23:59:59
```

**成功响应**:
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- 返回Excel文件二进制流

---

### 7.2 导出活动参与频次报表

**接口地址**: `GET /api/reports/activity-frequency/export`

**功能描述**: 导出学生活动参与频次统计报表（Excel格式）

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| class_name | String | 否 | 班级筛选 |

**请求示例**:
```
GET /api/reports/activity-frequency/export?class_name=计算机2401班
```

**成功响应**:
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- 返回Excel文件二进制流

---

## 8. API使用流程示例

### 8.1 完整考勤流程

1. **登录获取令牌**:
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

2. **发起考勤**:
```bash
curl -X POST http://localhost:5000/api/attendance/checkin \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "image_base64": "data:image/jpeg;base64,...",
    "image_format": "jpg"
  }'
```

3. **查询考勤记录**:
```bash
curl -X GET "http://localhost:5000/api/attendance/records?page=1&size=20" \
  -H "Authorization: Bearer <access_token>"
```

---

### 8.2 完整学生管理流程

1. **创建学生**:
```bash
curl -X POST http://localhost:5000/api/students \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "student_id": "2024001",
    "name": "张三",
    "class_name": "计算机2401班",
    "face_image_base64": "data:image/jpeg;base64,..."
  }'
```

2. **查询学生列表**:
```bash
curl -X GET "http://localhost:5000/api/students?class_name=计算机2401班" \
  -H "Authorization: Bearer <access_token>"
```

3. **更新学生信息**:
```bash
curl -X PUT http://localhost:5000/api/students/2024001 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"name": "张三（已修改）"}'
```

4. **删除学生**:
```bash
curl -X DELETE http://localhost:5000/api/students/2024001 \
  -H "Authorization: Bearer <access_token>"
```

---

## 9. 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 操作成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（登录失败/令牌无效） |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

**文档版本**: v1.0  
**创建时间**: 2026-05-06  
**适用项目**: 班级考勤系统 - 后端模块