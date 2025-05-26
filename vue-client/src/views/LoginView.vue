<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card">
        <h1 class="login-title">Вход в систему</h1>
        <form @submit.prevent="handleLogin" class="login-form">
          <div class="form-group">
            <label for="username" class="form-label">Имя пользователя</label>
            <input 
              type="text" 
              id="username" 
              v-model="form.username" 
              class="form-input" 
              required 
              autocomplete="username"
            />
          </div>
          
          <div class="form-group">
            <label for="password" class="form-label">Пароль</label>
            <input 
              type="password" 
              id="password" 
              v-model="form.password" 
              class="form-input" 
              required 
              autocomplete="current-password"
            />
          </div>
          
          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>
          
          <button 
            type="submit" 
            class="login-button"
            :disabled="isLoading"
          >
            {{ isLoading ? 'Вход...' : 'Войти' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const form = reactive({
  username: '',
  password: ''
});

const isLoading = ref(false);
const errorMessage = ref('');

const handleLogin = async () => {
  if (!form.username || !form.password) {
    errorMessage.value = 'Пожалуйста, заполните все поля';
    return;
  }
  
  errorMessage.value = '';
  isLoading.value = true;
  
  try {
    await authStore.login({
      username: form.username,
      password: form.password
    });
    
    // После успешного входа перенаправляем на главную страницу
    router.push('/');
  } catch (error: any) {
    errorMessage.value = error.message || 'Ошибка при входе в систему';
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f3f4f6;
}

.login-container {
  width: 100%;
  max-width: 400px;
  padding: 1rem;
}

.login-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 2rem;
}

.login-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 1.5rem;
  text-align: center;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.login-button {
  background-color: #1a56db;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-top: 0.5rem;
}

.login-button:hover {
  background-color: #1e429f;
}

.login-button:disabled {
  background-color: #6b7280;
  cursor: not-allowed;
}

.error-message {
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}
</style>