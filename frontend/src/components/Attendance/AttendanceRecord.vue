<template>
  <el-card title="考勤记录" class="record-card">
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
      <el-select v-model="searchForm.status" placeholder="考勤状态">
        <el-option :value="''" label="全部"></el-option>
        <el-option :value="1" label="成功"></el-option>
        <el-option :value="0" label="失败"></el-option>
      </el-select>
      <el-input 
        v-model="searchForm.class_name" 
        placeholder="专业" 
        class="class-input"
      />
      <el-button type="primary" @click="handleSearch">查询</el-button>
    </div>
    <el-table 
      :data="records" 
      border 
      :loading="loading"
      class="record-table"
    >
      <el-table-column prop="record_id" label="记录ID" width="80" />
      <el-table-column prop="student_id" label="学号" width="120" />
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column prop="class_name" label="专业" width="150" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="scope">
          <span :class="scope.row.status === 1 ? 'status-success' : 'status-failed'">
            {{ scope.row.status === 1 ? '成功' : '失败' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="confidence" label="匹配度" width="100">
        <template #default="scope">
          {{ formatConfidence(scope.row.confidence) }}
        </template>
      </el-table-column>
      <el-table-column prop="emotion" label="情绪" width="100">
        <template #default="scope">
          <span :class="getEmotionClass(scope.row.emotion)" class="emotion-tag">
            {{ getEmotionLabel(scope.row.emotion) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="attendance_time" label="考勤时间" width="180">
        <template #default="scope">
          {{ formatDateTime(scope.row.attendance_time) }}
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
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { formatDateTime, formatConfidence, getEmotionLabel, getEmotionClass } from '../../utils/format'

defineProps({
  records: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  pagination: {
    type: Object,
    default: () => ({
      page: 1,
      size: 20,
      total: 0
    })
  }
})

const emit = defineEmits(['search', 'page-change'])

const searchForm = reactive({
  keyword: '',
  status: '',
  class_name: ''
})

const handleSearch = () => {
  emit('search', {
    keyword: searchForm.keyword,
    status: searchForm.status,
    class_name: searchForm.class_name,
    page: 1
  })
}

const handleSizeChange = (size) => {
  emit('page-change', { size, page: 1 })
}

const handleCurrentChange = (page) => {
  emit('page-change', { page })
}
</script>

<style scoped>
.record-card {
  margin-top: 20px;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.search-input {
  width: 200px;
}

.class-input {
  width: 150px;
}

.record-table {
  margin-top: 16px;
}
</style>
