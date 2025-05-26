<template>
  <div class="users-page">
    <div class="header-section">
      <h1 class="page-title">Пользователи</h1>
      <button @click="openCreateModal" class="btn-create">
        <span class="icon">+</span> Добавить пользователя
      </button>
    </div>

    <div class="users-table-container">
      <div v-if="isLoading" class="loading-indicator">
        Загрузка данных...
      </div>
      
      <div v-else-if="error" class="error-message">
        {{ error }}
      </div>
      
      <div v-else-if="users.length === 0" class="empty-state">
        Пользователи не найдены
      </div>
      
      <table v-else class="users-table">
        <thead>
          <tr>
            <th>Имя пользователя</th>
            <th>Роль</th>
            <th>Контракты</th>
            <th>Активные</th>
            <th>Истекают скоро</th>
            <th>Истекшие</th>
            <th>Дата регистрации</th>
            <th>Действия</th>
          </tr>
        </thead>
        
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.username }}</td>
            <td>
              <span :class="getRoleBadgeClass(user.role)">
                {{ getRoleText(user.role) }}
              </span>
            </td>
            <td>{{ user.total_contracts || 0 }}</td>
            <td>{{ user.active_contracts || 0 }}</td>
            <td>{{ user.expiring_contracts || 0 }}</td>
            <td>{{ user.expired_contracts || 0 }}</td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td class="actions-cell">
              <button @click="openEditModal(user)" class="btn-edit">
                Изменить
              </button>
              <button @click="openPasswordModal(user)" class="btn-password">
                Пароль
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Модальное окно создания/редактирования пользователя -->
    <div v-if="isModalOpen" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2 class="modal-title">{{ isEditMode ? 'Редактирование пользователя' : 'Новый пользователь' }}</h2>
          <button @click="closeModal" class="modal-close">&times;</button>
        </div>
        
        <form @submit.prevent="saveUser" class="user-form">
          <div class="form-group">
            <label for="username" class="form-label">Имя пользователя</label>
            <input 
              type="text"
              id="username"
              v-model="currentUser.username"
              class="form-input"
              required
            />
          </div>
          
          <div class="form-group" v-if="!isEditMode">
            <label for="password" class="form-label">Пароль</label>
            <input 
              type="password"
              id="password"
              v-model="currentUser.password"
              class="form-input"
              required
            />
          </div>
          
          <div class="form-group">
            <label for="role" class="form-label">Роль</label>
            <select 
              id="role"
              v-model="currentUser.role"
              class="form-select"
              required
            >
              <option value="lawyer">Юрист</option>
              <option value="admin">Администратор</option>
            </select>
          </div>
          
          <div class="form-actions">
            <button type="submit" class="btn-submit">
              {{ isEditMode ? 'Сохранить' : 'Создать' }}
            </button>
            <button type="button" @click="closeModal" class="btn-cancel">
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Модальное окно изменения пароля -->
    <div v-if="isPasswordModalOpen" class="modal-overlay" @click="closePasswordModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2 class="modal-title">Изменение пароля</h2>
          <button @click="closePasswordModal" class="modal-close">&times;</button>
        </div>
        
        <form @submit.prevent="changePassword" class="password-form">
          <div class="form-group">
            <label for="current_password" class="form-label">Текущий пароль</label>
            <input 
              type="password"
              id="current_password"
              v-model="passwordData.current_password"
              class="form-input"
              required
            />
          </div>
          
          <div class="form-group">
            <label for="new_password" class="form-label">Новый пароль</label>
            <input 
              type="password"
              id="new_password"
              v-model="passwordData.new_password"
              class="form-input"
              required
            />
          </div>
          
          <div class="form-actions">
            <button type="submit" class="btn-submit">
              Изменить пароль
            </button>
            <button type="button" @click="closePasswordModal" class="btn-cancel">
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

const authStore = useAuthStore();

interface User {
  id: number;
  username: string;
  role: string;
  created_at: string;
  updated_at?: string;
  total_contracts?: number;
  active_contracts?: number;
  expiring_contracts?: number;
  expired_contracts?: number;
}

interface UserCreate {
  username: string;
  password: string;
  role: string;
}

interface UserUpdate {
  username: string;
  role: string;
}

interface PasswordChange {
  current_password: string;
  new_password: string;
}

// Состояние
const users = ref<User[]>([]);
const isLoading = ref(true);
const error = ref('');
const isModalOpen = ref(false);
const isPasswordModalOpen = ref(false);
const isEditMode = ref(false);
const currentUser = ref<UserCreate & { id?: number }>({
  username: '',
  password: '',
  role: 'lawyer'
});
const passwordData = ref<PasswordChange>({
  current_password: '',
  new_password: ''
});
const selectedUserId = ref<number | null>(null);

// Загрузка пользователей
const fetchUsers = async () => {
  isLoading.value = true;
  try {
    const response = await axios.get('/api/users/with-stats', {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    });
    users.value = response.data;
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Ошибка при загрузке данных пользователей';
  } finally {
    isLoading.value = false;
  }
};

// Открытие модального окна создания
const openCreateModal = () => {
  currentUser.value = {
    username: '',
    password: '',
    role: 'lawyer'
  };
  isEditMode.value = false;
  isModalOpen.value = true;
};

// Открытие модального окна редактирования
const openEditModal = (user: User) => {
  currentUser.value = {
    id: user.id,
    username: user.username,
    password: '', // Пароль не загружаем при редактировании
    role: user.role
  };
  isEditMode.value = true;
  isModalOpen.value = true;
};

// Открытие модального окна смены пароля
const openPasswordModal = (user: User) => {
  selectedUserId.value = user.id;
  passwordData.value = {
    current_password: '',
    new_password: ''
  };
  isPasswordModalOpen.value = true;
};

// Закрытие модального окна
const closeModal = () => {
  isModalOpen.value = false;
};

// Закрытие модального окна смены пароля
const closePasswordModal = () => {
  isPasswordModalOpen.value = false;
  selectedUserId.value = null;
};

// Сохранение пользователя
const saveUser = async () => {
  try {
    if (isEditMode.value && currentUser.value.id) {
      // Редактирование
      const userData: UserUpdate = {
        username: currentUser.value.username,
        role: currentUser.value.role
      };
      
      await axios.put(`/api/users/${currentUser.value.id}`, userData, {
        headers: {
          Authorization: `Bearer ${authStore.token}`
        }
      });
    } else {
      // Создание
      await axios.post('/api/users', currentUser.value, {
        headers: {
          Authorization: `Bearer ${authStore.token}`
        }
      });
    }
    
    // Обновляем список пользователей
    await fetchUsers();
    closeModal();
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Ошибка при сохранении пользователя';
  }
};

// Изменение пароля
const changePassword = async () => {
  if (!selectedUserId.value) return;
  
  try {
    await axios.put(`/api/users/${selectedUserId.value}/password`, passwordData.value, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    });
    
    closePasswordModal();
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Ошибка при изменении пароля';
  }
};

// Получение класса для роли
const getRoleBadgeClass = (role: string) => {
  switch (role) {
    case 'admin': return 'role-badge role-admin';
    case 'lawyer': return 'role-badge role-lawyer';
    default: return 'role-badge';
  }
};

// Получение текста роли
const getRoleText = (role: string) => {
  switch (role) {
    case 'admin': return 'Администратор';
    case 'lawyer': return 'Юрист';
    default: return role;
  }
};

// Форматирование даты
const formatDate = (dateString: string) => {
  return format(new Date(dateString), 'dd.MM.yyyy', { locale: ru });
};

onMounted(() => {
  fetchUsers();
});
</script>

<style scoped>
.users-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-title {
  font-size: 1.875rem;
  font-weight: 600;
  color: #111827;
}

.btn-create {
  display: flex;
  align-items: center;
  background-color: #1a56db;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-create:hover {
  background-color: #1e429f;
}

.icon {
  font-size: 1.25rem;
  margin-right: 0.25rem;
}

.users-table-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th,
.users-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.users-table th {
  background-color: #f9fafb;
  font-weight: 600;
  color: #4b5563;
}

.loading-indicator,
.error-message,
.empty-state {
  padding: 2rem;
  text-align: center;
}

.error-message {
  color: #dc2626;
}

.role-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.role-admin {
  background-color: #fecaca;
  color: #b91c1c;
}

.role-lawyer {
  background-color: #bfdbfe;
  color: #1e40af;
}

.actions-cell {
  display: flex;
  gap: 0.5rem;
}

.btn-edit,
.btn-password {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  border: none;
  cursor: pointer;
}

.btn-edit {
  background-color: #1a56db;
  color: white;
}

.btn-edit:hover {
  background-color: #1e429f;
}

.btn-password {
  background-color: #f3f4f6;
  color: #4b5563;
  border: 1px solid #d1d5db;
}

.btn-password:hover {
  background-color: #e5e7eb;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 500px;
  overflow: hidden;
}

.modal-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e5e7eb;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
}

.user-form,
.password-form {
  padding: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-label {
  display: block;
  font-weight: 500;
  color: #4b5563;
  margin-bottom: 0.375rem;
}

.form-input,
.form-select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.btn-submit,
.btn-cancel {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-size: 0.875rem;
  cursor: pointer;
}

.btn-submit {
  background-color: #1a56db;
  color: white;
  border: none;
}

.btn-submit:hover {
  background-color: #1e429f;
}

.btn-cancel {
  background-color: #f3f4f6;
  color: #4b5563;
  border: 1px solid #d1d5db;
}

.btn-cancel:hover {
  background-color: #e5e7eb;
}
</style>