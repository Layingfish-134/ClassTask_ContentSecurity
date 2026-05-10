# 专业考勤系统 - 前端代码架构设计

## 1. 技术栈

| 分类 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | Vue.js | 3.x | 响应式前端框架 |
| UI组件 | Element Plus | 2.x | 企业级UI组件库 |
| 图表 | Chart.js | 4.x | 图表可视化库 |
| HTTP客户端 | Axios | 1.x | 网络请求库 |
| 构建工具 | Vite | 5.x | 快速构建工具 |
| 语言 | JavaScript | ES6+ | 编程语言 |

## 2. 项目目录结构

```
frontend/                              # 前端项目根目录
├── public/                            # 静态资源目录
│   ├── index.html                     # HTML入口文件
│   └── favicon.ico                    # 网站图标
├── src/                               # 源代码目录
│   ├── components/                    # 组件目录
│   │   ├── Attendance/               # 考勤相关组件
│   │   │   ├── AttendanceCamera.vue   # 摄像头实时预览组件
│   │   │   ├── AttendanceResult.vue   # 考勤结果展示组件
│   │   │   └── AttendanceRecord.vue   # 考勤记录列表组件
│   │   ├── GroupPhoto/               # 合照相关组件
│   │   │   ├── PhotoUpload.vue        # 合照上传组件
│   │   │   └── PhotoResult.vue        # 合照识别结果组件
│   │   ├── Emotion/                  # 情绪分析组件
│   │   │   ├── EmotionPieChart.vue    # 情绪分布饼图
│   │   │   └── EmotionBarChart.vue    # 情绪分布柱状图
│   │   ├── Report/                   # 报表组件
│   │   │   └── ReportExport.vue       # 报表导出组件
│   │   └── Common/                   # 公共组件
│   │       ├── PageHeader.vue         # 页面头部组件
│   │       ├── PageFooter.vue         # 页面底部组件
│   │       ├── Loading.vue            # 加载动画组件
│   │       └── ErrorAlert.vue         # 错误提示组件
│   ├── views/                         # 页面视图目录
│   │   ├── AttendancePage.vue         # 考勤页面
│   │   ├── GroupPhotoPage.vue         # 合照识别页面
│   │   ├── AnalysisPage.vue           # 数据分析页面
│   │   └── StudentPage.vue            # 学生管理页面
│   ├── api/                           # API接口封装目录
│   │   ├── attendance.js              # 考勤相关API
│   │   ├── groupPhoto.js              # 合照识别API
│   │   ├── emotion.js                 # 情绪分析API
│   │   ├── student.js                 # 学生管理API
│   │   └── report.js                  # 报表导出API
│   ├── utils/                         # 工具函数目录
│   │   ├── camera.js                  # 摄像头操作工具
│   │   ├── file.js                    # 文件处理工具
│   │   ├── format.js                  # 数据格式化工具
│   │   └── request.js                 # 请求封装工具
│   ├── config/                        # 配置目录
│   │   └── index.js                   # 全局配置
│   ├── stores/                        # 状态管理目录
│   │   ├── attendanceStore.js         # 考勤状态管理
│   │   ├── emotionStore.js            # 情绪分析状态管理
│   │   └── studentStore.js            # 学生状态管理
│   ├── App.vue                        # 根组件
│   ├── main.js                        # 应用入口
│   └── style.css                      # 全局样式
├── .env.development                   # 开发环境变量
├── .env.production                    # 生产环境变量
├── vite.config.js                     # Vite配置文件
├── package.json                       # 项目依赖配置
└── README.md                          # 项目说明文档
```

## 3. 组件架构设计

### 3.1 考勤模块组件

#### AttendanceCamera.vue
**功能**: 摄像头实时预览、人脸采集、拍摄控制

| 功能模块 | 职责说明 |
|----------|----------|
| 摄像头初始化 | 请求摄像头权限，获取视频流 |
| 实时预览 | 显示摄像头画面 |
| 人脸检测 | 实时检测人脸位置 |
| 拍照控制 | 点击拍摄人脸照片 |
| 错误处理 | 摄像头调用失败提示 |

**Props**:
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| width | Number | 640 | 预览宽度 |
| height | Number | 480 | 预览高度 |
| enableDetection | Boolean | true | 是否启用人脸检测 |

**Events**:
| 事件 | 说明 | 参数 |
|------|------|------|
| photo-captured | 照片拍摄完成 | `imageBase64`: String |
| error | 摄像头调用失败 | `error`: Error |

---

#### AttendanceResult.vue
**功能**: 展示考勤结果

| 功能模块 | 职责说明 |
|----------|----------|
| 结果展示 | 显示考勤状态、学生信息 |
| 情绪展示 | 显示识别到的情绪 |
| 状态图标 | 根据状态显示成功/失败图标 |
| 重试按钮 | 考勤失败时提供重试入口 |

**Props**:
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| result | Object | null | 考勤结果数据 |
| visible | Boolean | false | 是否显示 |

**Events**:
| 事件 | 说明 | 参数 |
|------|------|------|
| retry | 用户点击重试 | 无 |

---

#### AttendanceRecord.vue
**功能**: 考勤记录列表展示

| 功能模块 | 职责说明 |
|----------|----------|
| 列表展示 | 分页展示考勤记录 |
| 筛选功能 | 按学号、专业、时间筛选 |
| 状态过滤 | 按考勤状态过滤 |
| 详情查看 | 点击查看详细信息 |

**Props**:
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| records | Array | [] | 考勤记录列表 |
| total | Number | 0 | 总记录数 |
| page | Number | 1 | 当前页码 |
| size | Number | 20 | 每页数量 |

**Events**:
| 事件 | 说明 | 参数 |
|------|------|------|
| page-change | 页码变更 | `page`: Number |
| view-detail | 查看详情 | `record`: Object |

---

### 3.2 合照模块组件

#### PhotoUpload.vue
**功能**: 合照上传与格式校验

| 功能模块 | 职责说明 |
|----------|----------|
| 文件选择 | 支持点击选择或拖拽上传 |
| 格式校验 | 校验JPG/PNG格式 |
| 大小限制 | 限制文件大小≤10MB |
| 图片预览 | 上传前预览图片 |
| 压缩处理 | 自动压缩过大图片 |

**Props**:
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| maxSize | Number | 10 | 最大文件大小(MB) |
| supportedTypes | Array | ['image/jpeg', 'image/png'] | 支持的文件类型 |

**Events**:
| 事件 | 说明 | 参数 |
|------|------|------|
| file-selected | 文件选择完成 | `file`: File |
| file-error | 文件校验失败 | `error`: Object |

---

#### PhotoResult.vue
**功能**: 合照识别结果展示

| 功能模块 | 职责说明 |
|----------|----------|
| 识别统计 | 显示识别人数、总人脸数 |
| 学生列表 | 展示识别成功的学生信息 |
| 置信度显示 | 显示每位学生的匹配置信度 |
| 情绪标签 | 显示学生情绪 |

**Props**:
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| result | Object | null | 识别结果数据 |
| photoUrl | String | '' | 合照预览地址 |

---

### 3.3 情绪分析组件

#### EmotionPieChart.vue
**功能**: 情绪分布饼图

| 功能模块 | 职责说明 |
|----------|----------|
| 饼图渲染 | 使用Chart.js渲染饼图 |
| 数据绑定 | 绑定情绪分布数据 |
| 图例展示 | 显示情绪图例 |
| 交互提示 | 悬停显示详细信息 |

**Props**:
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| data | Object | {} | 情绪分布数据 |
| title | String | '情绪分布' | 图表标题 |

---

#### EmotionBarChart.vue
**功能**: 情绪分布柱状图（按时间/专业维度）

| 功能模块 | 职责说明 |
|----------|----------|
| 柱状图渲染 | 使用Chart.js渲染 |
| 多维度数据 | 支持按时间段/专业分组 |
| 数据对比 | 展示不同维度的情绪对比 |
| 动态更新 | 支持数据动态刷新 |

**Props**:
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| data | Array | [] | 多维度情绪数据 |
| groupBy | String | 'time' | 分组方式(time/class) |

---

### 3.4 报表组件

#### ReportExport.vue
**功能**: 报表导出功能

| 功能模块 | 职责说明 |
|----------|----------|
| 筛选条件 | 时间范围、专业选择 |
| 导出类型 | 支持考勤报表、活动频次报表 |
| 导出按钮 | 触发导出请求 |
| 进度提示 | 显示导出进度 |

**Props**:
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| reportType | String | 'attendance' | 报表类型 |

**Events**:
| 事件 | 说明 | 参数 |
|------|------|------|
| export | 触发导出 | `params`: Object |

---

### 3.5 公共组件

#### PageHeader.vue
**功能**: 页面头部导航

| 功能模块 | 职责说明 |
|----------|----------|
| Logo展示 | 显示系统Logo |
| 导航菜单 | 页面导航链接 |
| 用户信息 | 登录用户信息展示 |

#### PageFooter.vue
**功能**: 页面底部

| 功能模块 | 职责说明 |
|----------|----------|
| 版权信息 | 显示版权声明 |
| 版本号 | 显示系统版本 |

#### Loading.vue
**功能**: 加载动画

**Props**:
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| text | String | '加载中...' | 加载提示文字 |
| visible | Boolean | false | 是否显示 |

#### ErrorAlert.vue
**功能**: 错误提示组件

**Props**:
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| message | String | '' | 错误信息 |
| type | String | 'error' | 提示类型(error/warning/info) |
| visible | Boolean | false | 是否显示 |

**Events**:
| 事件 | 说明 | 参数 |
|------|------|------|
| close | 关闭提示 | 无 |

## 4. 页面视图架构

### 4.1 AttendancePage.vue
**考勤页面**

| 区域 | 组件 | 说明 |
|------|------|------|
| 头部 | PageHeader | 页面导航 |
| 主体 | AttendanceCamera | 摄像头预览区 |
| 结果区 | AttendanceResult | 考勤结果展示 |
| 记录区 | AttendanceRecord | 历史记录列表 |
| 底部 | PageFooter | 页面底部 |

**页面状态**:
| 状态 | 说明 |
|------|------|
| idle | 初始状态，等待用户操作 |
| previewing | 摄像头预览中 |
| processing | 正在处理考勤请求 |
| success | 考勤成功 |
| failed | 考勤失败 |

---

### 4.2 GroupPhotoPage.vue
**合照识别页面**

| 区域 | 组件 | 说明 |
|------|------|------|
| 头部 | PageHeader | 页面导航 |
| 上传区 | PhotoUpload | 合照上传组件 |
| 预览区 | - | 照片预览 |
| 结果区 | PhotoResult | 识别结果展示 |
| 底部 | PageFooter | 页面底部 |

---

### 4.3 AnalysisPage.vue
**数据分析页面**

| 区域 | 组件 | 说明 |
|------|------|------|
| 头部 | PageHeader | 页面导航 |
| 筛选区 | - | 时间/专业/活动筛选 |
| 图表区 | EmotionPieChart | 情绪饼图 |
| 图表区 | EmotionBarChart | 情绪柱状图 |
| 报表区 | ReportExport | 报表导出 |
| 底部 | PageFooter | 页面底部 |

---

### 4.4 StudentPage.vue
**学生管理页面**

| 区域 | 组件 | 说明 |
|------|------|------|
| 头部 | PageHeader | 页面导航 |
| 查询区 | - | 学生查询表单 |
| 列表区 | - | 学生列表展示 |
| 操作区 | - | 添加/编辑/删除按钮 |
| 底部 | PageFooter | 页面底部 |

## 5. API 封装架构

### 5.1 request.js - 请求封装
**功能**: 统一HTTP请求封装

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `get(url, params)` | GET请求 | `url`: String, `params`: Object | Promise |
| `post(url, data)` | POST请求 | `url`: String, `data`: Object | Promise |
| `put(url, data)` | PUT请求 | `url`: String, `data`: Object | Promise |
| `delete(url)` | DELETE请求 | `url`: String | Promise |

**特性**:
- 请求超时处理（30秒）
- 统一错误处理
- 请求/响应拦截器
- 自动添加认证token

---

### 5.2 attendance.js - 考勤API

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `checkin(imageBase64, format)` | 发起考勤 | `imageBase64`: String, `format`: String | Promise |
| `getRecords(params)` | 查询考勤记录 | `params`: Object | Promise |
| `getRecordById(id)` | 查询单条记录 | `id`: Number | Promise |

---

### 5.3 groupPhoto.js - 合照API

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `recognize(imageBase64, format, activityName)` | 上传并识别合照 | `imageBase64`: String, `format`: String, `activityName`: String | Promise |
| `getRecords(params)` | 查询合照记录 | `params`: Object | Promise |
| `getRecordById(id)` | 查询单条记录 | `id`: Number | Promise |

---

### 5.4 emotion.js - 情绪分析API

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `getStatistics(params)` | 获取情绪统计 | `params`: Object | Promise |
| `getTrend(params)` | 获取情绪趋势 | `params`: Object | Promise |

---

### 5.5 student.js - 学生管理API

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `create(studentData)` | 创建学生 | `studentData`: Object | Promise |
| `list(params)` | 查询学生列表 | `params`: Object | Promise |
| `getById(id)` | 查询单个学生 | `id`: String | Promise |
| `update(id, studentData)` | 更新学生信息 | `id`: String, `studentData`: Object | Promise |
| `delete(id)` | 删除学生 | `id`: String | Promise |

---

### 5.6 report.js - 报表API

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `exportAttendance(params)` | 导出考勤报表 | `params`: Object | Promise (Blob) |
| `exportActivityFrequency(params)` | 导出活动频次报表 | `params`: Object | Promise (Blob) |

## 6. 工具函数架构

### 6.1 camera.js - 摄像头工具

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `initCamera(constraints)` | 初始化摄像头 | `constraints`: MediaStreamConstraints | Promise(MediaStream) |
| `startPreview(videoElement)` | 开始预览 | `videoElement`: HTMLVideoElement | void |
| `capturePhoto(videoElement)` | 拍摄照片 | `videoElement`: HTMLVideoElement | String (base64) |
| `stopCamera(stream)` | 停止摄像头 | `stream`: MediaStream | void |
| `detectFace(videoElement)` | 人脸检测 | `videoElement`: HTMLVideoElement | Object (人脸位置) |

---

### 6.2 file.js - 文件处理工具

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `validateFile(file, maxSize, types)` | 校验文件 | `file`: File, `maxSize`: Number, `types`: Array | Object (valid, message) |
| `compressImage(file, maxSize)` | 压缩图片 | `file`: File, `maxSize`: Number | Promise(Blob) |
| `fileToBase64(file)` | 文件转Base64 | `file`: File | Promise(String) |
| `downloadFile(blob, filename)` | 下载文件 | `blob`: Blob, `filename`: String | void |

---

### 6.3 format.js - 格式化工具

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `formatTime(date)` | 格式化时间 | `date`: Date/String | String |
| `formatDate(date)` | 格式化日期 | `date`: Date/String | String |
| `formatDateTime(date)` | 格式化日期时间 | `date`: Date/String | String |
| `formatConfidence(value)` | 格式化置信度 | `value`: Number | String |
| `getEmotionLabel(emotion)` | 获取情绪标签 | `emotion`: String | String |
| `getStatusLabel(status)` | 获取状态标签 | `status`: Number | String |

## 7. 状态管理架构

### 7.1 attendanceStore.js - 考勤状态

| 状态 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| isProcessing | Boolean | false | 是否正在处理 |
| currentResult | Object | null | 当前考勤结果 |
| records | Array | [] | 考勤记录列表 |
| total | Number | 0 | 记录总数 |
| page | Number | 1 | 当前页码 |

| 方法 | 功能 | 参数 |
|------|------|------|
| `setProcessing(processing)` | 设置处理状态 | `processing`: Boolean |
| `setResult(result)` | 设置考勤结果 | `result`: Object |
| `setRecords(records)` | 设置记录列表 | `records`: Array |
| `setTotal(total)` | 设置总数 | `total`: Number |
| `setPage(page)` | 设置页码 | `page`: Number |

---

### 7.2 emotionStore.js - 情绪分析状态

| 状态 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| statistics | Object | {} | 情绪统计数据 |
| trend | Array | [] | 情绪趋势数据 |
| filters | Object | {} | 筛选条件 |

| 方法 | 功能 | 参数 |
|------|------|------|
| `setStatistics(data)` | 设置统计数据 | `data`: Object |
| `setTrend(data)` | 设置趋势数据 | `data`: Array |
| `setFilters(filters)` | 设置筛选条件 | `filters`: Object |

---

### 7.3 studentStore.js - 学生状态

| 状态 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| students | Array | [] | 学生列表 |
| total | Number | 0 | 学生总数 |
| currentStudent | Object | null | 当前选中学生 |
| filters | Object | {} | 筛选条件 |

| 方法 | 功能 | 参数 |
|------|------|------|
| `setStudents(students)` | 设置学生列表 | `students`: Array |
| `setTotal(total)` | 设置总数 | `total`: Number |
| `setCurrentStudent(student)` | 设置当前学生 | `student`: Object |
| `setFilters(filters)` | 设置筛选条件 | `filters`: Object |

## 8. 配置文件

### 8.1 config/index.js

```javascript
export default {
  // API配置
  api: {
    baseUrl: process.env.VUE_APP_API_URL || 'http://localhost:8000/api',
    timeout: 30000,
    retryCount: 3
  },
  
  // 文件配置
  file: {
    maxSize: 10 * 1024 * 1024, // 10MB
    supportedTypes: ['image/jpeg', 'image/png', 'image/jpg'],
    compressQuality: 0.8
  },
  
  // 摄像头配置
  camera: {
    width: 640,
    height: 480,
    facingMode: 'user'
  },
  
  // 分页配置
  pagination: {
    defaultSize: 20,
    pageSizes: [10, 20, 50, 100]
  },
  
  // 情绪类型配置
  emotions: {
    happy: { label: '高兴', color: '#FFD93D' },
    sad: { label: '悲伤', color: '#6B7FD7' },
    surprised: { label: '惊讶', color: '#FF9F43' },
    angry: { label: '愤怒', color: '#FF6B6B' },
    neutral: { label: '中性', color: '#A55EEA' }
  },
  
  // 路由配置
  routes: {
    attendance: '/attendance',
    groupPhoto: '/group-photo',
    analysis: '/analysis',
    student: '/student'
  }
}
```

### 8.2 .env.development

```
VUE_APP_API_URL=http://localhost:8000/api
VUE_APP_APP_NAME=专业考勤系统
VUE_APP_APP_VERSION=1.0.0
```

### 8.3 .env.production

```
VUE_APP_API_URL=https://api.example.com
VUE_APP_APP_NAME=专业考勤系统
VUE_APP_APP_VERSION=1.0.0
```

## 9. 入口文件结构

### 9.1 main.js

| 功能 | 说明 |
|------|------|
| 引入Vue | 创建Vue应用实例 |
| 引入Element Plus | 注册UI组件库 |
| 引入全局样式 | 加载全局CSS |
| 配置路由 | 配置页面路由 |
| 挂载应用 | 挂载到DOM |

### 9.2 App.vue

| 区域 | 说明 |
|------|------|
| template | 根组件模板 |
| script | 组件逻辑 |
| style | 组件样式 |

## 10. 数据流架构

```
用户操作 → 组件事件 → API调用 → 状态更新 → 视图渲染
                    ↓
              错误处理 → 提示用户
```

### 数据流向说明

1. **用户操作**: 用户在界面上进行点击、输入等操作
2. **组件事件**: 组件捕获用户操作并触发相应事件
3. **API调用**: 通过封装的API模块向后端发送请求
4. **状态更新**: 将返回数据更新到对应的状态管理中
5. **视图渲染**: 组件监听状态变化并重新渲染
6. **错误处理**: 统一捕获并处理请求错误

---

**文档版本**: v1.0  
**创建时间**: 2026-05-06  
**适用项目**: 专业考勤系统 - 前端模块
