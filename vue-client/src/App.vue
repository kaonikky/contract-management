<template>
  <div class="app">
    <template v-if="isLoggedIn">
      <AppLayout>
        <router-view></router-view>
      </AppLayout>
    </template>
    <template v-else>
      <router-view></router-view>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from './stores/auth';
import AppLayout from './components/AppLayout.vue';

const router = useRouter();
const authStore = useAuthStore();

const isLoggedIn = computed(() => authStore.isAuthenticated);

// Проверка авторизации при загрузке приложения
onMounted(async () => {
  try {
    await authStore.checkAuth();
  } catch (error) {
    console.error('Ошибка при проверке авторизации:', error);
  }
});
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #111827;
}

.app {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
</style>