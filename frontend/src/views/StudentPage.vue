<template>
  <div class="student-page">
    <div class="search-section">
      <el-card class="search-card">
        <div class="search-bar">
          <el-input 
            v-model="searchForm.keyword" 
            placeholder="请输入学号或姓名" 
            class="search-input"
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button @click="handleSearch"><el-icon><Search /></el-icon></el-button>
            </template>
          </el-input>
          <el-input 
            v-model="searchForm.class_name" 
            placeholder="班级" 
            class="class-input"
          />
          <el-button 
            v-if="isTeacherOrAdmin" 
            type="primary" 
            @click="handleAdd"
          >
            <el-icon><Plus /></el-icon>
            添加学生
          </el-button>
        </div>
      </el-card>
    </div>
    
    <el-card title="学生列表" class="list-card">
      <el-table 
        :data="students" 
        border 
        :loading="loading"
        class="student-table"
      >
        <el-table-column prop="student_id" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="class_name" label="班级" width="150" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" v-if="isTeacherOrAdmin">
          <template #default="scope">
            <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="pagination.page"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pagination.size"
        layout="total, sizes, prev, pager, next, jumper"
        :total="pagination.total"
      />
    </el-card>
    
    <el-dialog :title="isEditing ? '编辑学生' : '添加学生'" :visible="showDialog" @close="handleCloseDialog">
      <el-form :model="form" class="dialog-form">
        <el-form-item label="学号" :rules="[{ required: true, message: '请输入学号' }]">
          <el-input v-model="form.student_id" :disabled="isEditing"></el-input>
        </el-form-item>
        <el-form-item label="姓名" :rules="[{ required: true, message: '请输入姓名' }]">
          <el-input v-model="form.name"></el-input>
        </el-form-item>
        <el-form-item label="班级" :rules="[{ required: true, message: '请输入班级' }]">
          <el-input v-model="form.class_name"></el-input>
        </el-form-item>
        <el-form-item label="人脸照片">
          <input 
            type="file" 
            accept="image/jpeg,image/png" 
            class="file-input"
            @change="handleFaceImageChange"
          />
          <div v-if="faceImagePreview" class="image-preview">
            <img :src="faceImagePreview" class="preview-img" />
          </div>
          <div v-if="isEditing && !faceImagePreview" class="image-tip">
            <span class="text-gray">如需更新人脸照片，请选择新图片</span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleCloseDialog">取消</el-button>
        <el-button type="primary" @click="handleSubmit">提交</el-button>
      </template>
    </el-dialog>
    
    <Loading :visible="isProcessing" text="处理中..." />
    <ErrorAlert 
      :visible="showError" 
      :message="errorMessage"
      type="error"
      @close="showError = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Plus } from '@element-plus/icons-vue'
import Loading from '../components/Common/Loading.vue'
import ErrorAlert from '../components/Common/ErrorAlert.vue'
import { create, list, update, remove } from '../api/student'
import { formatDateTime } from '../utils/format'
import { fileToBase64 } from '../utils/file'
import { getCurrentUser } from '../api/auth'

const loading = ref(false)
const isProcessing = ref(false)
const showError = ref(false)
const errorMessage = ref('')
const showDialog = ref(false)
const isEditing = ref(false)
const isTeacherOrAdmin = ref(false)
const currentUser = ref(null)

const searchForm = reactive({
  keyword: '',
  class_name: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const students = ref([])

const form = reactive({
  student_id: '',
  name: '',
  class_name: ''
})

const faceImagePreview = ref('')
const faceImageBase64 = ref('')

const fetchCurrentUser = async () => {
  try {
    const response = await getCurrentUser()
    if (response.code === 200) {
      currentUser.value = response.data
      isTeacherOrAdmin.value = ['teacher', 'admin'].includes(response.data.role)
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

const handleSearch = async () => {
  pagination.page = 1
  await loadStudents()
}

const handleAdd = () => {
  isEditing.value = false
  form.student_id = ''
  form.name = ''
  form.class_name = ''
  faceImagePreview.value = ''
  faceImageBase64.value = ''
  showDialog.value = true
}

const handleEdit = (row) => {
  isEditing.value = true
  form.student_id = row.student_id
  form.name = row.name
  form.class_name = row.class_name
  faceImagePreview.value = ''
  faceImageBase64.value = ''
  showDialog.value = true
}

const handleDelete = async (row) => {
  if (!confirm(`确定要删除学生 ${row.name} 吗？`)) return
  
  isProcessing.value = true
  
  try {
    const response = await remove(row.student_id)
    
    if (response.code === 200) {
      await loadStudents()
    } else {
      showError.value = true
      errorMessage.value = response.message || '删除失败'
    }
  } catch (error) {
    showError.value = true
    errorMessage.value = error.message || '删除失败'
  } finally {
    isProcessing.value = false
  }
}

const handleCloseDialog = () => {
  showDialog.value = false
}

const handleFaceImageChange = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  
  try {
    faceImagePreview.value = await fileToBase64(file)
    faceImageBase64.value = faceImagePreview.value
  } catch (error) {
    showError.value = true
    errorMessage.value = '图片上传失败'
  }
}

const handleSubmit = async () => {
  if (!form.student_id || !form.name || !form.class_name) {
    showError.value = true
    errorMessage.value = '请填写完整信息'
    return
  }
  
  if (!isEditing.value && !faceImageBase64.value) {
    showError.value = true
    errorMessage.value = '请上传人脸照片'
    return
  }
  
  isProcessing.value = true
  
  try {
    const data = {
      student_id: form.student_id,
      name: form.name,
      class_name: form.class_name
    }
    
    if (faceImageBase64.value) {
      data.face_image_base64 = faceImageBase64.value
    }
    
    const response = isEditing.value 
      ? await update(form.student_id, data)
      : await create(data)
    
    if (response.code === 200 || response.code === 201) {
      showDialog.value = false
      await loadStudents()
    } else {
      showError.value = true
      errorMessage.value = response.message || '操作失败'
    }
  } catch (error) {
    showError.value = true
    errorMessage.value = error.message || '操作失败'
  } finally {
    isProcessing.value = false
  }
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  loadStudents()
}

const handleCurrentChange = (page) => {
  pagination.page = page
  loadStudents()
}

const loadStudents = async () => {
  loading.value = true
  
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (searchForm.class_name) params.class_name = searchForm.class_name
    
    const response = await list(params)
    
    if (response.code === 200) {
      students.value = response.data.records || []
      pagination.total = response.data.total || 0
    }
  } catch (error) {
    console.error('加载学生列表失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchCurrentUser()
  await loadStudents()
})
</script>

<style scoped>
.student-page {
  max-width: 1200px;
  margin: 0 auto;
}

.search-section {
  margin-bottom: 20px;
}

.search-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.search-input {
  width: 250px;
}

.class-input {
  width: 150px;
}

.student-table {
  margin-bottom: 16px;
}

.dialog-form {
  max-width: 400px;
}

.file-input {
  display: block;
  margin-bottom: 12px;
}

.image-preview {
  max-width: 200px;
}

.preview-img {
  width: 100%;
  border-radius: 8px;
}

.image-tip {
  color: #999;
  font-size: 12px;
}

.text-gray {
  color: #999;
}
</style>