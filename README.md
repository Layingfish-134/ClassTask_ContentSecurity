# 专业考勤系统

一个基于人脸识别的课堂考勤与活动管理系统，包含实时考勤、合照识别、学生管理、情绪统计、Excel 报表导出等功能。项目采用前后端分离结构：前端使用 Vue 3 + Element Plus，后端使用 Flask + MySQL，并集成 MTCNN、FaceNet、OpenCV、PyTorch 等图像识别能力。

## 功能特性

- 用户登录与权限控制：支持管理员、教师、学生三类角色。
- 实时考勤：通过摄像头拍照完成活体检测、人脸识别、情绪识别和考勤记录保存。
- 合照识别：上传合照后自动检测多张人脸，匹配学生库并生成活动参与记录。
- 学生管理：支持学生增删改查、单个学生人脸录入、批量导入。
- 情绪分析：统计考勤和合照识别中产生的情绪分布与趋势。
- 报表导出：支持考勤明细、考勤汇总、活动频次、学生活动参与、活动记录等 Excel 报表。
- 登录会话控制：前端使用会话级 token，后端重启后旧 token 自动失效。

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 前端 | Vue 3, Vite, Element Plus, Axios, Chart.js |
| 后端 | Python, Flask, Flask-RESTful, Flask-JWT-Extended, Flask-SQLAlchemy |
| 数据库 | MySQL |
| 人脸检测 | facenet-pytorch MTCNN, OpenCV Haar fallback |
| 特征提取 | InceptionResnetV1 pretrained on VGGFace2 |
| 情绪分析 | Transformers/PyTorch 模型，失败时使用简易规则降级 |
| 报表 | Pandas, OpenPyXL |

## 项目结构

```text
Task-6/
├── backend/               # Flask 后端服务
├── frontend/              # Vue 前端应用
├── docs/                  # 项目说明文档
├── scripts/               # 数据导入和演示数据脚本
├── sql/                   # 数据库相关 SQL
├── uploads/               # 顶层上传目录预留
├── .gitignore             # Git 忽略规则
└── README.md              # 项目总览文档
```

更详细的结构说明见 [docs/项目架构文档.md](docs/项目架构文档.md)。

## 快速开始

### 1. 安装后端依赖

```powershell
cd backend
pip install -r requirements.txt
```

启动前请确认 MySQL 已创建数据库，并在 `backend/.env` 中配置 `DB_HOST`、`DB_PORT`、`DB_NAME`、`DB_USER`、`DB_PASSWORD`。

如使用项目自带虚拟环境，可在根目录使用：

```powershell
venv\Scripts\python.exe backend\run.py
```

### 2. 启动后端

```powershell
cd backend
python run.py
```

默认后端地址：

```text
http://localhost:5000
```

### 3. 安装并启动前端

```powershell
cd frontend
npm install
npm run dev
```

默认前端地址以 Vite 输出为准，一般为：

```text
http://localhost:5173
```

### 4. 导入本地人脸库

如果数据库为空，需要导入 `backend/uploads/face_data` 中的学生照片：

```powershell
venv\Scripts\python.exe scripts\import_face_data.py
```

导入脚本会解析图片文件名，提取人脸特征并写入学生表，同时创建学生账号。

## 默认账号

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | admin | demo_hash_123456 |
| 教师 | teacher01 | demo_hash_123456 |
| 学生 | 20240001 | demo_hash_123456 |

部分批量导入学生账号的默认密码可能为 `123456` 或导入脚本指定值。

## 常用接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/auth/me` | 获取当前用户 |
| POST | `/api/attendance/checkin` | 实时考勤签到 |
| GET | `/api/attendance/records` | 查询考勤记录 |
| GET/POST | `/api/students` | 查询/新增学生 |
| POST | `/api/group-photo/recognize` | 合照识别 |
| GET | `/api/group-photo/records` | 合照识别记录 |
| GET | `/api/emotion/statistics` | 情绪分布统计 |
| GET | `/api/emotion/trend` | 情绪趋势统计 |
| GET | `/api/reports/attendance-summary/export` | 考勤汇总报表 |
| GET | `/api/reports/activity/export` | 学生活动参与报表 |
| GET | `/api/reports/activity-record/export` | 活动记录报表 |

完整业务逻辑见 [docs/功能说明文档.md](docs/功能说明文档.md)。

## 数据与文件说明

- MySQL 数据库：默认数据库名为 `attendance_db`，连接信息在 `backend/.env` 中配置。
- `backend/uploads/face_data`：学生人脸库原始照片。
- `backend/uploads`：考勤照片、合照上传文件保存目录。
- `backend/models`：本地模型文件目录。
- `frontend/dist`：前端构建产物。

其中数据库、上传文件、模型文件和构建产物通常不应提交到 Git。

## 构建

前端生产构建：

```powershell
cd frontend
npm run build
```

后端语法检查示例：

```powershell
venv\Scripts\python.exe -m py_compile backend\run.py backend\app\__init__.py
```

## 文档

- [功能说明文档](docs/功能说明文档.md)
- [项目架构文档](docs/项目架构文档.md)

## 备注

本项目用于课程设计和实验演示。人脸识别、活体检测和情绪识别结果会受到摄像头质量、光照、人脸角度、样本库质量等因素影响。正式部署前应补充更严格的安全策略、模型评估、日志审计和隐私合规处理。
