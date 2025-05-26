<template>
  <div class="app-layout" :class="{ 'sidebar-open': isSidebarOpen }">
    <!-- Верхняя панель -->
    <header class="app-header">
      <div class="header-start">
        <button @click="toggleSidebar" class="sidebar-toggle">
          <span class="toggle-icon">&#9776;</span>
        </button>
        <div class="app-title">Система управления контрактами</div>
      </div>
      
      <div class="header-end">
        <div class="user-menu" ref="userMenuRef">
          <button @click="toggleUserMenu" class="user-menu-toggle">
            {{ authStore.user?.username }}
            <span class="arrow-icon">&#9662;</span>
          </button>
          
          <div v-if="isUserMenuOpen" class="user-dropdown">
            <div class="user-info">
              <div class="username">{{ authStore.user?.username }}</div>
              <div class="user-role">{{ getRoleText(authStore.user?.role) }}</div>
            </div>
            
            <hr class="dropdown-divider" />
            
            <button @click="handleLogout" class="logout-button">
              Выйти
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Боковая панель -->
    <aside class="app-sidebar">
      <nav class="sidebar-nav">
        <router-link to="/" class="nav-link" active-class="active">
          <span class="nav-icon">📊</span>
          <span class="nav-text">Панель управления</span>
        </router-link>
        
        <router-link to="/contracts" class="nav-link" active-class="active">
          <span class="nav-icon">📄</span>
          <span class="nav-text">Контракты</span>
        </router-link>
        
        <router-link v-if="isAdmin" to="/users" class="nav-link" active-class="active">
          <span class="nav-icon">👥</span>
          <span class="nav-text">Пользователи</span>
        </router-link>
      </nav>
    </aside>

    <!-- Основное содержимое -->
    <main class="app-content">
      <slot></slot>
    </main>

    <!-- Затемнение для мобильных устройств -->
    <div 
      v-if="isSidebarOpen" 
      class="sidebar-backdrop"
      @click="closeSidebar"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const authStore = useAuthStore();

// Состояние
const isSidebarOpen = ref(false);
const isUserMenuOpen = ref(false);
const userMenuRef = ref<HTMLElement | null>(null);

// Проверка на администратора
const isAdmin = computed(() => {
  return authStore.user?.role === 'admin';
});

// Переключение состояния боковой панели
const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value;
};

// Закрытие боковой панели
const closeSidebar = () => {
  isSidebarOpen.value = false;
};

// Переключение меню пользователя
const toggleUserMenu = () => {
  isUserMenuOpen.value = !isUserMenuOpen.value;
};

// Закрытие меню пользователя при клике вне его
const closeUserMenuOutside = (event: MouseEvent) => {
  if (userMenuRef.value && !userMenuRef.value.contains(event.target as Node)) {
    isUserMenuOpen.value = false;
  }
};

// Обработка выхода из системы
const handleLogout = async () => {
  await authStore.logout();
  router.push('/login');
};

// Получение текста роли
const getRoleText = (role?: string) => {
  if (!role) return '';
  
  switch (role) {
    case 'admin': return 'Администратор';
    case 'lawyer': return 'Юрист';
    default: return role;
  }
};

// Добавление обработчика клика при монтировании
onMounted(() => {
  document.addEventListener('click', closeUserMenuOutside);
});

// Удаление обработчика при размонтировании
onBeforeUnmount(() => {
  document.removeEventListener('click', closeUserMenuOutside);
});
</script>

<style scoped>
.app-layout {
  display: grid;
  grid-template-areas:
    "header header"
    "sidebar content";
  grid-template-columns: 250px 1fr;
  grid-template-rows: auto 1fr;
  min-height: 100vh;
}

/* Верхняя панель */
.app-header {
  grid-area: header;
  background-color: #1a56db;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 1rem;
  height: 60px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
  z-index: 20;
}

.header-start,
.header-end {
  display: flex;
  align-items: center;
}

.app-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-left: 1rem;
}

.sidebar-toggle {
  background: none;
  border: none;
  color: white;
  font-size: 1.25rem;
  cursor: pointer;
  display: none;
}

/* Боковая панель */
.app-sidebar {
  grid-area: sidebar;
  background-color: #f3f4f6;
  border-right: 1px solid #e5e7eb;
  padding: 1rem 0;
  z-index: 10;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-link {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  color: #4b5563;
  text-decoration: none;
  transition: background-color 0.2s;
  border-radius: 4px;
  margin: 0 0.5rem;
}

.nav-link:hover {
  background-color: #e5e7eb;
}

.nav-link.active {
  background-color: #dbeafe;
  color: #1e40af;
  font-weight: 500;
}

.nav-icon {
  margin-right: 0.75rem;
  font-size: 1.25rem;
}

/* Основное содержимое */
.app-content {
  grid-area: content;
  padding: 1.5rem;
  background-color: #f9fafb;
  overflow-y: auto;
}

/* Меню пользователя */
.user-menu {
  position: relative;
}

.user-menu-toggle {
  background: none;
  border: none;
  color: white;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 0.5rem;
}

.arrow-icon {
  margin-left: 0.5rem;
}

.user-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 200px;
  z-index: 30;
  overflow: hidden;
}

.user-info {
  padding: 1rem;
}

.username {
  font-weight: 600;
  color: #111827;
  margin-bottom: 0.25rem;
}

.user-role {
  font-size: 0.75rem;
  color: #6b7280;
}

.dropdown-divider {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 0;
}

.logout-button {
  width: 100%;
  padding: 0.75rem 1rem;
  text-align: left;
  background: none;
  border: none;
  color: #ef4444;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.logout-button:hover {
  background-color: #fee2e2;
}

/* Затемнение для мобильных устройств */
.sidebar-backdrop {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 5;
}

/* Адаптивная верстка */
@media (max-width: 768px) {
  .app-layout {
    grid-template-columns: 1fr;
    grid-template-areas:
      "header"
      "content";
  }
  
  .sidebar-toggle {
    display: block;
  }
  
  .app-sidebar {
    position: fixed;
    left: -250px;
    top: 60px;
    bottom: 0;
    width: 250px;
    transition: left 0.3s ease;
    box-shadow: 2px 0 4px rgba(0, 0, 0, 0.1);
  }
  
  .sidebar-open .app-sidebar {
    left: 0;
  }
  
  .sidebar-open .sidebar-backdrop {
    display: block;
  }
}
</style>