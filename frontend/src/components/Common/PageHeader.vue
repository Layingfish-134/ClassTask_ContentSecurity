<template>
  <header class="page-header">
    <div class="flex-between">
      <div class="logo-section">
        <h1 class="logo">班级考勤系统</h1>
      </div>
      <nav class="nav-section">
        <el-menu mode="horizontal" :default-active="currentNav" class="nav-menu">
          <el-menu-item index="attendance" @click="handleNavClick('attendance')">
            <el-icon><VideoCamera /></el-icon>
            <span>实时考勤</span>
          </el-menu-item>
          <el-menu-item index="groupPhoto" @click="handleNavClick('groupPhoto')">
            <el-icon><Picture /></el-icon>
            <span>合照识别</span>
          </el-menu-item>
          <el-menu-item index="analysis" @click="handleNavClick('analysis')">
            <el-icon><PieChart /></el-icon>
            <span>数据分析</span>
          </el-menu-item>
          <el-menu-item index="student" @click="handleNavClick('student')">
            <el-icon><User /></el-icon>
            <span>学生管理</span>
          </el-menu-item>
        </el-menu>
      </nav>
      <div class="user-section">
        <el-dropdown>
          <span class="user-info">
            <el-icon><User /></el-icon>
            <span>{{ username || '管理员' }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { VideoCamera, Picture, PieChart, User } from '@element-plus/icons-vue'
import { getCurrentUser } from '../../api/auth'

defineProps({
  currentNav: {
    type: String,
    default: 'attendance'
  }
})

const emit = defineEmits(['nav-change'])
const username = ref('')

const handleNavClick = (nav) => {
  emit('nav-change', nav)
}

const handleLogout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  window.location.href = '/login.html'
}

onMounted(async () => {
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      window.location.href = '/login.html'
      return
    }
    const response = await getCurrentUser()
    if (response.code === 200) {
      username.value = response.data.username
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    window.location.href = '/login.html'
  }
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.logo-section .logo {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.nav-section {
  flex: 1;
  margin: 0 40px;
}

.nav-menu {
  background: transparent;
  border: none;
}

.nav-menu .el-menu-item {
  color: rgba(255, 255, 255, 0.9);
}

.nav-menu .el-menu-item:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.nav-menu .el-menu-item.is-active {
  color: white;
  background: rgba(255, 255, 255, 0.2);
}

.user-section {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 20px;
  transition: background 0.3s;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.1);
}
</style>
