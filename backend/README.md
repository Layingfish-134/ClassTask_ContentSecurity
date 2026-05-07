# 班级考勤系统 - 后端服务

基于 Flask + Python 的人脸识别考勤系统后端，集成活体检测、人脸比对、合照识别、情绪分析等核心算法。

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 编程语言 |
| Flask | 2.3.x | Web框架 |
| Flask-RESTful | 0.3.10 | RESTful API |
| Flask-JWT-Extended | 4.7.x | JWT认证 |
| Flask-SQLAlchemy | 3.1.x | ORM |
| MySQL | 8.0+ | 关系型数据库 |
| OpenCV | 4.x | 图像处理 |
| MTCNN | 0.1.x | 人脸检测 |
| Facenet-PyTorch | 2.5.x | 人脸特征提取 |
| PyTorch | 2.x | 深度学习框架 |
| Pandas + OpenPyXL | - | Excel导出 |

---

## 项目目录结构

```
backend/
├── .env                          # 环境变量配置文件
├── requirements.txt              # Python依赖清单
├── run.py                        # 应用启动入口
├── init_db.sql                   # 数据库初始化SQL脚本
├── uploads/                      # 用户上传文件存储目录（运行后自动产生）
├── models/                       # 深度学习模型文件目录
│   ├── mtcnn/                    # MTCNN人脸检测模型
│   ├── facenet/                  # FaceNet特征提取模型
│   └── resnet/                   # ResNet情绪分类模型
└── app/                          # 应用主包
    ├── __init__.py               # 应用工厂：创建Flask实例、注册路由、初始化组件
    ├── config/                   # 配置模块
    │   ├── __init__.py
    │   ├── database_config.py    # 数据库连接配置与初始化
    │   └── file_storage_config.py# 文件上传存储配置
    ├── models/                   # 数据模型模块（ORM映射）
    │   ├── __init__.py           # 导入所有模型，确保SQLAlchemy识别
    │   ├── student.py            # 学生信息模型（student_info表）
    │   ├── attendance_record.py  # 考勤记录模型（attendance_record表）
    │   ├── group_photo_record.py # 合照识别记录模型（group_photo_record表）
    │   └── user.py               # 用户模型（user_info表，权限控制）
    ├── dto/                      # 数据传输对象（DTO）
    │   ├── __init__.py
    │   ├── request/              # 请求DTO
    │   │   ├── __init__.py
    │   │   └── parsers.py        # 所有API请求参数解析器
    │   └── response/             # 响应DTO
    │       ├── __init__.py
    │       ├── common.py         # 通用响应格式（success/error/paginated）
    │       ├── face_match_result.py  # 人脸比对结果数据结构
    │       └── emotion_result.py     # 情绪分析结果数据结构
    ├── repositories/             # 数据访问层（封装数据库操作）
    │   ├── __init__.py
    │   ├── student_repository.py           # 学生数据CRUD
    │   ├── attendance_record_repository.py # 考勤记录查询与统计
    │   └── group_photo_record_repository.py# 合照记录查询与活动频次统计
    ├── services/                 # 业务与算法服务层
    │   ├── __init__.py
    │   ├── liveness_detector.py       # 活体检测算法（纹理+颜色+傅里叶多模态融合）
    │   ├── face_feature_extractor.py  # 人脸特征提取（MTCNN检测+FaceNet提取）
    │   ├── face_matcher.py            # 人脸比对（余弦相似度匹配）
    │   ├── multi_face_detector.py     # 多人脸检测（合照场景）
    │   ├── emotion_classifier.py      # 情绪分类（ResNet50/简易规则降级）
    │   ├── face_recognition_service.py# 人脸识别服务（整合以上算法的完整流程）
    │   ├── attendance_service.py      # 考勤业务逻辑
    │   ├── student_service.py         # 学生管理业务逻辑
    │   └── report_service.py          # 报表生成与合照识别业务逻辑
    ├── controllers/              # 控制器层（API接口）
    │   ├── __init__.py
    │   ├── auth_controller.py         # 认证接口（登录/刷新令牌/当前用户）
    │   ├── attendance_controller.py   # 考勤接口（签到/记录查询）
    │   ├── student_controller.py      # 学生管理接口（CRUD）
    │   ├── group_photo_controller.py  # 合照识别接口（上传识别/记录查询）
    │   ├── emotion_controller.py      # 情绪统计接口
    │   └── report_controller.py       # 报表导出接口（Excel）
    ├── exception/                # 异常处理模块
    │   ├── __init__.py
    │   └── global_exception_handler.py# 全局异常处理器与自定义异常类
    └── utils/                    # 工具模块
        ├── __init__.py
        └── image_utils.py        # 图像处理工具（Base64编解码、保存、缩放）
```

---

## 各模块详细说明

### 1. config/ — 配置模块

| 文件 | 功能 |
|------|------|
| `database_config.py` | 读取环境变量配置MySQL连接，初始化SQLAlchemy，启动时自动建表 |
| `file_storage_config.py` | 配置上传目录、文件大小限制、允许的文件格式 |

### 2. models/ — 数据模型模块

| 文件 | 对应数据表 | 功能 |
|------|-----------|------|
| `student.py` | `student_info` | 学生基本信息+人脸特征向量（JSON存储） |
| `attendance_record.py` | `attendance_record` | 考勤记录（状态、置信度、情绪、时间、图片路径） |
| `group_photo_record.py` | `group_photo_record` | 合照识别记录（照片信息、活动名称、识别学生列表JSON） |
| `user.py` | `user_info` | 用户账号（用户名、密码哈希、角色teacher/student） |

### 3. dto/ — 数据传输对象

| 文件 | 功能 |
|------|------|
| `request/parsers.py` | 定义所有API的请求参数解析规则（必填校验、类型校验、默认值） |
| `response/common.py` | 统一响应格式：`success_response()`、`error_response()`、`paginated_response()` |
| `response/face_match_result.py` | 人脸比对结果：学号、姓名、置信度、是否匹配 |
| `response/emotion_result.py` | 情绪分析结果：情绪类型、置信度 |

### 4. repositories/ — 数据访问层

| 文件 | 功能 |
|------|------|
| `student_repository.py` | 学生CRUD、按班级/关键词分页查询、查询有人脸特征的学生 |
| `attendance_record_repository.py` | 考勤记录多条件分页查询、情绪统计聚合查询、按日期范围查询 |
| `group_photo_record_repository.py` | 合照记录分页查询、活动参与频次统计 |

### 5. services/ — 核心算法与业务服务层

#### 算法服务

| 文件 | 算法 | 说明 |
|------|------|------|
| `liveness_detector.py` | 多模态活体检测 | 纹理分析（Laplacian方差）+ 颜色分析（HSV肤色检测）+ 傅里叶分析（高频分量比），三维度加权融合评分 |
| `face_feature_extractor.py` | 人脸检测+特征提取 | 优先使用MTCNN检测+FaceNet提取512维特征；降级使用OpenCV Haar检测+像素特征 |
| `face_matcher.py` | 人脸比对 | 余弦相似度计算，阈值0.8（可配置），支持单人与多人批量匹配 |
| `multi_face_detector.py` | 多人脸检测 | 优先MTCNN批量检测，降级OpenCV Haar级联，返回所有人脸区域和图像 |
| `emotion_classifier.py` | 情绪分类 | 优先ResNet50深度学习模型（5类：happy/sad/surprised/angry/neutral）；降级使用灰度统计规则 |
| `face_recognition_service.py` | 人脸识别整合服务 | 编排完整流程：活体检测→人脸检测→特征提取→库比对→情绪分析 |

#### 业务服务

| 文件 | 功能 |
|------|------|
| `attendance_service.py` | 考勤签到（调用人脸识别服务+保存记录+保存图片）、考勤记录分页查询 |
| `student_service.py` | 学生CRUD（创建时自动提取人脸特征、更新时可重新录入人脸） |
| `report_service.py` | 合照识别（多人脸检测+批量比对+情绪分析+保存记录）、情绪统计、Excel报表导出 |

### 6. controllers/ — API控制器

| 文件 | 接口 | 说明 |
|------|------|------|
| `auth_controller.py` | `/api/auth/login`、`/api/auth/refresh`、`/api/auth/me` | 登录获取JWT、刷新令牌、获取当前用户；启动时自动创建默认账号 |
| `attendance_controller.py` | `/api/attendance/checkin`、`/api/attendance/records` | 人脸考勤签到、考勤记录多条件查询 |
| `student_controller.py` | `/api/students`、`/api/students/{id}` | 学生列表/新增、学生详情/更新/删除 |
| `group_photo_controller.py` | `/api/group-photo/recognize`、`/api/group-photo/records` | 合照上传识别、合照记录查询 |
| `emotion_controller.py` | `/api/emotion/statistics` | 情绪分布统计 |
| `report_controller.py` | `/api/reports/attendance/export`、`/api/reports/activity-frequency/export` | 考勤报表Excel导出、活动频次Excel导出 |

### 7. exception/ — 异常处理

| 文件 | 功能 |
|------|------|
| `global_exception_handler.py` | 定义自定义异常类（活体检测失败、人脸未找到、权限不足等）+ 注册Flask全局错误处理器（400/401/403/404/500） |

### 8. utils/ — 工具模块

| 文件 | 功能 |
|------|------|
| `image_utils.py` | Base64↔图像互转、图像保存到磁盘、图像缩放、字节数组解码 |

---

## API接口一览

### 认证接口

| 方法 | 路径 | 说明 | 是否需要Token |
|------|------|------|-------------|
| POST | `/api/auth/login` | 用户登录，返回JWT | 否 |
| POST | `/api/auth/refresh` | 刷新JWT令牌 | 否 |
| GET | `/api/auth/me` | 获取当前用户信息 | 是 |

### 考勤接口

| 方法 | 路径 | 说明 | 是否需要Token |
|------|------|------|-------------|
| POST | `/api/attendance/checkin` | 人脸考勤签到 | 是 |
| GET | `/api/attendance/records` | 查询考勤记录 | 是 |

### 学生管理接口

| 方法 | 路径 | 说明 | 是否需要Token |
|------|------|------|-------------|
| GET | `/api/students` | 查询学生列表 | 是 |
| POST | `/api/students` | 新增学生（含人脸录入） | 是 |
| GET | `/api/students/{student_id}` | 查询学生详情 | 是 |
| PUT | `/api/students/{student_id}` | 更新学生信息 | 是 |
| DELETE | `/api/students/{student_id}` | 删除学生 | 是 |

### 合照识别接口

| 方法 | 路径 | 说明 | 是否需要Token |
|------|------|------|-------------|
| POST | `/api/group-photo/recognize` | 上传合照并识别 | 是 |
| GET | `/api/group-photo/records` | 查询合照识别记录 | 是 |

### 情绪分析接口

| 方法 | 路径 | 说明 | 是否需要Token |
|------|------|------|-------------|
| GET | `/api/emotion/statistics` | 获取情绪分布统计 | 是 |

### 报表导出接口

| 方法 | 路径 | 说明 | 是否需要Token |
|------|------|------|-------------|
| GET | `/api/reports/attendance/export` | 导出考勤报表（Excel） | 是 |
| GET | `/api/reports/activity-frequency/export` | 导出活动频次报表（Excel） | 是 |

---

## 数据库设计

### student_info（学生信息表）

| 字段 | 类型 | 说明 |
|------|------|------|
| student_id | VARCHAR(20) PK | 学号 |
| name | VARCHAR(50) | 姓名 |
| class_name | VARCHAR(50) | 班级 |
| face_feature | TEXT | 人脸特征向量（JSON格式） |
| created_at | DATETIME | 创建时间 |

### attendance_record（考勤记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| record_id | BIGINT PK AUTO | 记录ID |
| student_id | VARCHAR(20) FK | 学号 |
| status | INT | 考勤状态（0失败/1成功） |
| confidence | DECIMAL(5,2) | 匹配置信度 |
| emotion | VARCHAR(20) | 情绪类型 |
| emotion_confidence | DECIMAL(5,2) | 情绪置信度 |
| attendance_time | DATETIME | 考勤时间 |
| image_path | VARCHAR(255) | 考勤图片路径 |

### group_photo_record（合照识别记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| photo_id | BIGINT PK AUTO | 照片ID |
| photo_name | VARCHAR(255) | 照片名称 |
| photo_path | VARCHAR(255) | 照片路径 |
| activity_name | VARCHAR(100) | 活动名称 |
| recognized_students | TEXT | 识别学生列表（JSON） |
| created_at | DATETIME | 创建时间 |

### user_info（用户信息表）

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | VARCHAR(20) PK | 用户ID |
| username | VARCHAR(50) UNIQUE | 用户名 |
| password_hash | VARCHAR(255) | 密码哈希（bcrypt） |
| role | VARCHAR(20) | 角色（teacher/student） |
| student_id | VARCHAR(20) FK | 关联学号（学生用户） |
| created_at | DATETIME | 创建时间 |

---

## 算法流程

### 考勤签到流程

```
前端上传人脸图片(Base64)
    ↓
活体检测（纹理+颜色+傅里叶三维度融合）
    ↓ 失败 → 返回"活体检测失败，疑似照片攻击"
    ↓ 通过
人脸检测（MTCNN / OpenCV Haar）
    ↓ 未检测到 → 返回"未检测到人脸"
    ↓ 检测到
人脸特征提取（FaceNet 512维向量 / OpenCV像素特征）
    ↓
人脸库比对（余弦相似度，阈值0.8）
    ↓
情绪分类（ResNet50 / 简易规则）
    ↓
保存考勤记录到数据库
    ↓
返回考勤结果（学生信息+置信度+情绪）
```

### 合照识别流程

```
前端上传合照(Base64)
    ↓
多人脸检测（MTCNN / OpenCV Haar）
    ↓ 对每个人脸
特征提取 → 人脸库比对 → 情绪分类
    ↓
汇总识别结果，保存合照记录
    ↓
返回识别学生名单（学号+姓名+置信度+情绪）
```

---

## 环境准备与运行

### 前置条件

- Python 3.10+
- MySQL 8.0+（需提前安装并启动）
- pip 包管理器

### 第一步：安装Python依赖

```bash
cd backend
pip install -r requirements.txt
```

如需GPU加速（可选）：

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 第二步：配置环境变量

编辑 `backend/.env` 文件，修改数据库连接信息：

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=attendance_db
DB_USER=root
DB_PASSWORD=你的MySQL密码
```

### 第三步：初始化数据库

方式一：使用SQL脚本（推荐）

```bash
mysql -u root -p < init_db.sql
```

方式二：启动应用时自动建表

Flask-SQLAlchemy 配置了 `db.create_all()`，首次启动时会自动创建数据表（需确保数据库 `attendance_db` 已存在）。

```sql
CREATE DATABASE IF NOT EXISTS attendance_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 第四步：启动后端服务

```bash
cd backend
python run.py
```

启动成功后输出：

```
 * Running on http://0.0.0.0:5000
 * Restarting with stat
 * Debugger is active!
```

### 第五步：验证服务

```bash
# 测试登录接口
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

成功返回JWT令牌即表示服务正常运行。

---

## 默认账号

系统首次启动时自动创建以下账号：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | teacher |
| teacher001 | 123456 | teacher |

---

## 算法模型说明

### 模型自动下载

以下模型在首次使用时会自动下载：

- **MTCNN**：通过 `mtcnn` 库自动下载
- **FaceNet**：通过 `facenet-pytorch` 的 `pretrained='vggface2'` 自动下载

### 模型手动放置

如需离线使用，将模型文件放入 `models/` 对应目录：

```
models/
├── mtcnn/          # MTCNN模型文件（通常自动下载）
├── facenet/        # FaceNet模型文件（通常自动下载）
└── resnet/
    └── emotion_resnet.pth   # 需自行训练或下载的情绪分类模型
```

### 降级策略

当模型文件不可用时，系统自动降级：

| 算法 | 优先方案 | 降级方案 |
|------|---------|---------|
| 人脸检测 | MTCNN（高精度） | OpenCV Haar级联（基础精度） |
| 特征提取 | FaceNet 512维向量 | OpenCV 像素特征（低精度） |
| 情绪分类 | ResNet50 深度学习 | 灰度统计规则（基础分类） |
| 活体检测 | 无降级，始终使用多模态融合 | - |

---

## 请求示例

### 登录获取Token

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 新增学生（含人脸录入）

```bash
curl -X POST http://localhost:5000/api/students \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "student_id": "2024001",
    "name": "张三",
    "class_name": "计算机2401班",
    "face_image_base64": "data:image/jpeg;base64,/9j/4AAQ..."
  }'
```

### 人脸考勤签到

```bash
curl -X POST http://localhost:5000/api/attendance/checkin \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "image_base64": "data:image/jpeg;base64,/9j/4AAQ...",
    "image_format": "jpg"
  }'
```

### 合照识别

```bash
curl -X POST http://localhost:5000/api/group-photo/recognize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "image_base64": "data:image/jpeg;base64,/9j/4AAQ...",
    "image_format": "jpg",
    "activity_name": "元旦晚会"
  }'
```

### 查询考勤记录

```bash
curl -X GET "http://localhost:5000/api/attendance/records?class_name=计算机2401班&page=1&size=20" \
  -H "Authorization: Bearer <your_token>"
```

### 导出考勤报表

```bash
curl -X GET "http://localhost:5000/api/reports/attendance/export?start_time=2024-01-01T00:00:00&end_time=2024-12-31T23:59:59" \
  -H "Authorization: Bearer <your_token>" \
  -o attendance_report.xlsx
```

---

## 常见问题

### Q: 启动时数据库连接失败？

检查 `.env` 中的数据库配置是否正确，确保MySQL已启动，且数据库 `attendance_db` 已创建。

### Q: MTCNN/FaceNet下载慢或失败？

这两个库的模型文件托管在海外服务器，如下载困难可配置国内镜像源，或使用降级方案（系统会自动降级到OpenCV）。

### Q: 情绪分类精度不高？

需要自行训练ResNet50情绪分类模型。推荐使用FER-2013数据集进行训练，训练后将模型保存为 `models/resnet/emotion_resnet.pth`。

### Q: 如何修改活体检测阈值？

编辑 `.env` 文件中的 `LIVENESS_THRESHOLD` 值（默认0.95，降低阈值更容易通过，提高阈值更严格）。

### Q: 如何修改人脸比对阈值？

编辑 `.env` 文件中的 `FACE_MATCH_THRESHOLD` 值（默认0.8，降低阈值更宽松，提高阈值更严格）。
