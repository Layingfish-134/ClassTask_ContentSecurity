<template>
  <div class="app-container">
    <PageHeader @nav-change="handleNavChange" />
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
import { ref } from 'vue'
import PageHeader from './components/Common/PageHeader.vue'
import PageFooter from './components/Common/PageFooter.vue'
import AttendancePage from './views/AttendancePage.vue'
import GroupPhotoPage from './views/GroupPhotoPage.vue'
import AnalysisPage from './views/AnalysisPage.vue'
import StudentPage from './views/StudentPage.vue'

const currentPage = ref('attendance')

const handleNavChange = (page) => {
  currentPage.value = page
}
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
