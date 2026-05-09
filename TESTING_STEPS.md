# 项目本地测试步骤

本文档用于在本地验收班级考勤系统的数据库、后端 API 与前端页面。命令默认在项目根目录 `ClassTask_ContentSecurity` 下执行，Windows、macOS、Linux 路径不同，请按自己的安装位置替换。

## 1. 测试前检查

确认本地已准备好：

- MySQL 8.0+，推荐 8.0.19 及以上。
- Python 3.10+。
- Node.js 18+ 与 npm。
- 项目模型文件位于 `models/`。
- 真实人脸图片如需测试，应放在 `backend/uploads/face_data/`。

不要提交以下本地隐私或大文件：

- `backend/uploads/`
- `models/`
- `scripts/seed_face_data_basic.py`
- `sql/seed_face_data_basic.sql`

## 2. 数据库初始化

### 2.1 使用真实人脸基础数据

当前网页端实际测试优先使用这条路线。它会导入真实学生基础信息、账号和人脸特征，但不会预置考勤记录，后续考勤记录由你在网页端测试产生。

确认真实图片已在：

```text
backend/uploads/face_data/
```

Windows PowerShell 推荐使用 `cmd /c` 执行 SQL 重定向，避免中文转码问题：

```powershell
cmd /c 'mysql -u root -p --default-character-set=utf8mb4 < "sql/database_schema.sql"'
cmd /c 'mysql -u root -p --default-character-set=utf8mb4 attendance_db < "sql/seed_face_data_basic.sql"'
```

如果 `mysql` 没有加入 PATH，请把 `mysql` 替换为本机完整路径，例如：

```powershell
cmd /c '"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p --default-character-set=utf8mb4 < "sql/database_schema.sql"'
```

macOS / Linux 可使用：

```bash
mysql -u root -p --default-character-set=utf8mb4 < sql/database_schema.sql
mysql -u root -p --default-character-set=utf8mb4 attendance_db < sql/seed_face_data_basic.sql
```

如需重新生成真实数据 SQL：

```powershell
python scripts/seed_face_data_basic.py --output sql/seed_face_data_basic.sql
```

注意：`seed_face_data_basic.py` 与 `seed_face_data_basic.sql` 属于本地隐私数据辅助文件，不要提交到云端。

### 2.2 使用演示统计数据

`sql/seed_basic.sql` 和 `sql/seed_demo_records.sql` 主要用于早期图表、报表、分页和统计 SQL 验收。当前网页端真实测试暂时不推荐依赖它们。

如果确实需要恢复演示统计数据，可导入：

```powershell
cmd /c 'mysql -u root -p --default-character-set=utf8mb4 < "sql/database_schema.sql"'
cmd /c 'mysql -u root -p --default-character-set=utf8mb4 attendance_db < "sql/seed_basic.sql"'
cmd /c 'mysql -u root -p --default-character-set=utf8mb4 attendance_db < "sql/seed_demo_records.sql"'
```

注意：当前仓库中的 `seed_basic.sql` 可能仍含旧占位密码 `demo_hash_123456`。如果用它做后端登录测试，可能触发 `Invalid salt`，需要额外重置账号密码或改用真实人脸基础数据路线。

## 3. 数据库验收

登录 MySQL：

```powershell
mysql -u root -p attendance_db
```

执行基础检查：

```sql
SHOW TABLES;

SELECT COUNT(*) AS student_count FROM student_info;
SELECT COUNT(*) AS user_count FROM user_info;
SELECT COUNT(*) AS attendance_count FROM attendance_record;
SELECT COUNT(*) AS emotion_count FROM emotion_record;

SELECT username, role, status
FROM user_info
ORDER BY role, username
LIMIT 10;
```

演示数据导入后，重点确认：

- `student_info` 有学生数据。
- `user_info` 有 admin、teacher、student 账号。
- `attendance_record` 有考勤流水。
- `emotion_record` 有情绪统计数据。

真实数据导入后，重点确认：

- `student_info.face_feature` 不为空。
- `student_info.face_feature_hash` 不为空。
- `user_info` 中学生账号已同步创建。

## 4. 后端启动

进入后端目录：

```powershell
cd backend
```

首次运行安装依赖：

```powershell
python -m pip install -r requirements.txt
```

检查 `.env` 中数据库配置，至少需要：

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=attendance_db
DB_USER=你的数据库用户名
DB_PASSWORD=你的数据库密码
HOST=0.0.0.0
PORT=5000
```

启动后端：

```powershell
python run.py
```

看到 Flask 服务监听 `http://127.0.0.1:5000` 或 `http://localhost:5000` 即可继续。

## 5. API 快速验收

新开一个终端，登录并保存 token：

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:5000/api/auth/login" `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"123456"}'

$token = $login.data.access_token
```

验证当前用户：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/api/auth/me" `
  -Headers @{ Authorization = "Bearer $token" }
```

验证学生列表：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/api/students?size=3" `
  -Headers @{ Authorization = "Bearer $token" }
```

验证考勤记录：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/api/attendance/records?size=3" `
  -Headers @{ Authorization = "Bearer $token" }
```

验证情绪统计。该接口需要时间范围：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/api/emotion/statistics?start_time=2026-04-07%2000:00:00&end_time=2026-05-06%2023:59:59" `
  -Headers @{ Authorization = "Bearer $token" }
```

## 6. 前端启动

新开终端，进入前端目录：

```powershell
cd frontend
```

首次运行安装依赖：

```powershell
npm install
```

启动开发服务器：

```powershell
npm run dev
```

浏览器打开：

```text
http://localhost:5173
```

默认前端会把 `/api` 请求代理到：

```text
http://localhost:5000
```

如果后端端口不同，可临时指定：

```powershell
$env:VITE_API_PROXY_TARGET="http://localhost:5001"
npm run dev
```

## 7. 前端页面验收

按顺序检查：

1. 打开登录页。
2. 使用 `admin / 123456` 登录。
3. 进入学生管理页，确认能看到学生列表。
4. 进入考勤记录页，确认列表能加载。
5. 进入情绪统计页，确认图表接口不会报 401、422 或 500。
6. 使用学生账号登录，确认学生只能查看自己的相关数据。
7. 若使用真实人脸数据，进入签到页测试拍照或上传识别。

## 8. 常见问题

### Access denied for user

说明 `.env` 中 `DB_USER` 或 `DB_PASSWORD` 与 MySQL 实际账号不一致。修改后重启后端。

### Request failed with status code 422

常见原因：

- JWT token 失效或格式错误，重新登录。
- 接口缺少必填参数，例如情绪统计缺少 `start_time`。
- 人脸识别接口未检测到有效人脸或活体检测失败。

### 前端能打开但接口失败

检查：

- 后端是否已启动。
- 后端端口是否为 5000。
- `frontend/vite.config.js` 的代理目标是否正确。
- 浏览器开发者工具 Network 中 `/api/...` 请求返回码。

### Invalid salt

说明数据库里的 `password_hash` 不是后端当前 bcrypt 校验逻辑可识别的哈希。重新导入当前匹配的账号数据，或使用真实数据 seed 中生成的账号。

### 中文导入乱码

使用 `--default-character-set=utf8mb4`，Windows 下优先使用 `cmd /c` 文件重定向导入 SQL。

## 9. 提交前检查

提交前执行：

```powershell
git status --short
```

确认不要提交：

- `backend/uploads/`
- `models/`
- `scripts/seed_face_data_basic.py`
- `sql/seed_face_data_basic.sql`
- `.env`
- `__pycache__/`
- `dist/`

前端改动提交前建议执行：

```powershell
cd frontend
npm run build
```

后端改动提交前建议至少执行一次 API 快速验收。
