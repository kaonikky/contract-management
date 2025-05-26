<template>
  <div class="contracts-page">
    <div class="header-section">
      <h1 class="page-title">Контракты</h1>
      <button @click="openCreateModal" class="btn-create">
        <span class="icon">+</span> Добавить контракт
      </button>
    </div>

    <div class="filters-section">
      <div class="search-filter">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="Поиск по названию, ИНН..." 
          class="search-input"
          @input="applyFilters"
        />
      </div>
      
      <div class="status-filter">
        <select v-model="statusFilter" @change="applyFilters" class="status-select">
          <option value="">Все статусы</option>
          <option value="active">Активные</option>
          <option value="expiring_soon">Истекают скоро</option>
          <option value="expired">Истекшие</option>
        </select>
      </div>
    </div>

    <div class="contracts-table-container">
      <div v-if="isLoading" class="loading-indicator">
        Загрузка данных...
      </div>
      
      <div v-else-if="error" class="error-message">
        {{ error }}
      </div>
      
      <div v-else-if="filteredContracts.length === 0" class="empty-state">
        Нет контрактов, соответствующих критериям поиска
      </div>
      
      <table v-else class="contracts-table">
        <thead>
          <tr>
            <th>Название компании</th>
            <th>ИНН</th>
            <th>Директор</th>
            <th>Дата окончания</th>
            <th>Дней осталось</th>
            <th>Статус</th>
            <th>Действия</th>
          </tr>
        </thead>
        
        <tbody>
          <tr v-for="contract in filteredContracts" :key="contract.id" :class="getRowClass(contract.status)">
            <td>{{ contract.company_name }}</td>
            <td>{{ contract.inn }}</td>
            <td>{{ contract.director }}</td>
            <td>{{ formatDate(contract.end_date) }}</td>
            <td :class="getDaysLeftClass(contract.days_left)">{{ contract.days_left }}</td>
            <td>
              <span :class="getStatusBadgeClass(contract.status)">
                {{ getStatusText(contract.status) }}
              </span>
            </td>
            <td>
              <router-link :to="'/contracts/' + contract.id" class="btn-view">
                Просмотр
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Пагинация -->
    <div class="pagination" v-if="filteredContracts.length > 0">
      <button 
        :disabled="currentPage === 1" 
        @click="changePage(currentPage - 1)" 
        class="pagination-btn"
      >
        &laquo; Пред.
      </button>
      
      <span class="pagination-info">
        Страница {{ currentPage }} из {{ totalPages }}
      </span>
      
      <button 
        :disabled="currentPage === totalPages" 
        @click="changePage(currentPage + 1)" 
        class="pagination-btn"
      >
        След. &raquo;
      </button>
    </div>

    <!-- Модальное окно создания контракта будет реализовано позже -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

const authStore = useAuthStore();

interface Contract {
  id: number;
  company_name: string;
  inn: string;
  director: string;
  address: string;
  end_date: string;
  days_left: number;
  status: string;
  comments?: string;
  has_nd: boolean;
  lawyer_id: number;
}

// Состояние
const contracts = ref<Contract[]>([]);
const isLoading = ref(true);
const error = ref('');
const searchQuery = ref('');
const statusFilter = ref('');
const currentPage = ref(1);
const itemsPerPage = 10;

// Загрузка контрактов
const fetchContracts = async () => {
  isLoading.value = true;
  try {
    const response = await axios.get('/api/contracts', {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    });
    contracts.value = response.data;
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Ошибка при загрузке данных';
  } finally {
    isLoading.value = false;
  }
};

// Фильтрация контрактов
const filteredContracts = computed(() => {
  let result = [...contracts.value];
  
  // Применяем фильтр поиска
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(contract => 
      contract.company_name.toLowerCase().includes(query) ||
      contract.inn.toLowerCase().includes(query) ||
      contract.director.toLowerCase().includes(query)
    );
  }
  
  // Применяем фильтр статуса
  if (statusFilter.value) {
    result = result.filter(contract => contract.status === statusFilter.value);
  }
  
  // Сортировка по дате окончания (сначала истекающие скоро)
  result.sort((a, b) => {
    const aDate = new Date(a.end_date).getTime();
    const bDate = new Date(b.end_date).getTime();
    return aDate - bDate;
  });
  
  // Пагинация
  const start = (currentPage.value - 1) * itemsPerPage;
  return result.slice(start, start + itemsPerPage);
});

// Общее количество страниц
const totalPages = computed(() => {
  const totalItems = contracts.value.length;
  return Math.ceil(totalItems / itemsPerPage);
});

// Применение фильтров
const applyFilters = () => {
  currentPage.value = 1; // Сбрасываем на первую страницу при применении фильтров
};

// Изменение страницы
const changePage = (page: number) => {
  currentPage.value = page;
};

// Получение класса для строки
const getRowClass = (status: string) => {
  switch (status) {
    case 'expired': return 'expired-row';
    case 'expiring_soon': return 'expiring-row';
    default: return '';
  }
};

// Получение класса для количества дней
const getDaysLeftClass = (daysLeft: number) => {
  if (daysLeft < 0) return 'days-expired';
  if (daysLeft <= 10) return 'days-critical';
  if (daysLeft <= 30) return 'days-warning';
  return 'days-normal';
};

// Получение класса для статуса
const getStatusBadgeClass = (status: string) => {
  switch (status) {
    case 'active': return 'status-badge status-active';
    case 'expiring_soon': return 'status-badge status-expiring';
    case 'expired': return 'status-badge status-expired';
    default: return 'status-badge';
  }
};

// Получение текста статуса
const getStatusText = (status: string) => {
  switch (status) {
    case 'active': return 'Активен';
    case 'expiring_soon': return 'Истекает скоро';
    case 'expired': return 'Истек';
    default: return status;
  }
};

// Открытие модального окна создания контракта
const openCreateModal = () => {
  // Будет реализовано позже
  console.log('Открытие окна создания контракта');
};

// Форматирование даты
const formatDate = (dateString: string) => {
  return format(new Date(dateString), 'dd MMMM yyyy', { locale: ru });
};

onMounted(() => {
  fetchContracts();
});
</script>

<style scoped>
.contracts-page {
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

.filters-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.search-input {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  width: 100%;
  max-width: 300px;
}

.status-select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
}

.contracts-table-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.contracts-table {
  width: 100%;
  border-collapse: collapse;
}

.contracts-table th,
.contracts-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.contracts-table th {
  background-color: #f9fafb;
  font-weight: 600;
  color: #4b5563;
}

.expired-row {
  background-color: #fee2e2;
}

.expiring-row {
  background-color: #fef3c7;
}

.days-normal {
  color: #059669;
}

.days-warning {
  color: #d97706;
}

.days-critical {
  color: #dc2626;
  font-weight: 600;
}

.days-expired {
  color: #dc2626;
  font-weight: 700;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-active {
  background-color: #d1fae5;
  color: #065f46;
}

.status-expiring {
  background-color: #fef3c7;
  color: #92400e;
}

.status-expired {
  background-color: #fee2e2;
  color: #b91c1c;
}

.btn-view {
  display: inline-block;
  background-color: #1a56db;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  text-decoration: none;
}

.btn-view:hover {
  background-color: #1e429f;
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

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

.pagination-btn {
  background-color: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  cursor: pointer;
}

.pagination-btn:disabled {
  background-color: #e5e7eb;
  color: #9ca3af;
  cursor: not-allowed;
}

.pagination-info {
  color: #4b5563;
  font-size: 0.875rem;
}
</style>