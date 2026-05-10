<template>
  <div class="app-container">
    <PageHeader :current-nav="currentPage" :user-role="userRole" @nav-change="handleNavChange" />
    <main class="main-content">
      <AttendancePage v-if="currentPage === 'attendance'" />
      <GroupPhotoPage v-else-if="currentPage === 'groupPhoto'" />
      <AnalysisPage v-else-if="currentPage === 'analysis'" />
      <StudentPage v-else-if="currentPage === 'student'" />
    </main>
    <PageFooter />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from './components/Common/PageHeader.vue'
import PageFooter from './components/Common/PageFooter.vue'
import AttendancePage from './views/AttendancePage.vue'
import GroupPhotoPage from './views/GroupPhotoPage.vue'
import AnalysisPage from './views/AnalysisPage.vue'
import StudentPage from './views/StudentPage.vue'
import { getCurrentUser } from './api/auth'

const currentPage = ref('attendance')
const userRole = ref('')

const studentBlockedPages = ['analysis', 'student']

const handleNavChange = (page) => {
  if (userRole.value === 'student' && studentBlockedPages.includes(page)) {
    currentPage.value = 'attendance'
    return
  }
  currentPage.value = page
}

onMounted(async () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  if (!sessionStorage.getItem('access_token')) {
    window.location.href = '/login.html'
    return
  }

  try {
    const response = await getCurrentUser()
    if (response.code === 200) {
      userRole.value = response.data.role
      if (userRole.value === 'student' && studentBlockedPages.includes(currentPage.value)) {
        currentPage.value = 'attendance'
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
</style>
