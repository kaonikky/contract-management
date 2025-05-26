<template>
  <div class="dashboard">
    <h1 class="page-title">Панель управления</h1>
    
    <div class="stats-grid">
      <div class="stat-card">
        <h3 class="stat-title">Активные контракты</h3>
        <p class="stat-value">{{ statistics.active || 0 }}</p>
      </div>
      
      <div class="stat-card">
        <h3 class="stat-title">Истекают скоро</h3>
        <p class="stat-value">{{ statistics.expiringSoon || 0 }}</p>
      </div>
      
      <div class="stat-card">
        <h3 class="stat-title">Истекшие</h3>
        <p class="stat-value">{{ statistics.expired || 0 }}</p>
      </div>
      
      <div class="stat-card">
        <h3 class="stat-title">Всего контрактов</h3>
        <p class="stat-value">{{ statistics.total || 0 }}</p>
      </div>
    </div>
    
    <div class="dashboard-section">
      <h2 class="section-title">Контракты, истекающие в ближайшее время</h2>
      <div v-if="isLoading">Загрузка данных...</div>
      <div v-else-if="error">{{ error }}</div>
      <div v-else-if="expiringContracts.length === 0" class="empty-state">
        Нет контрактов, истекающих в ближайшее время
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Компания</th>
            <th>ИНН</th>
            <th>Дата окончания</th>
            <th>Дней осталось</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="contract in expiringContracts" :key="contract.id">
            <td>{{ contract.company_name }}</td>
            <td>{{ contract.inn }}</td>
            <td>{{ formatDate(contract.end_date) }}</td>
            <td :class="getDaysLeftClass(contract.days_left)">{{ contract.days_left }}</td>
            <td>
              <router-link :to="'/contracts/' + contract.id" class="btn-view">
                Просмотр
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

const authStore = useAuthStore();

interface Contract {
  id: number;
  company_name: string;
  inn: string;
  end_date: string;
  days_left: number;
  status: string;
}

interface Statistics {
  active: number;
  expiringSoon: number;
  expired: number;
  total: number;
}

const contracts = ref<Contract[]>([]);
const isLoading = ref(true);
const error = ref('');
const statistics = ref<Statistics>({
  active: 0,
  expiringSoon: 0,
  expired: 0,
  total: 0
});

// Получаем контракты, истекающие в ближайшее время (статус "expiring_soon")
const expiringContracts = computed(() => {
  return contracts.value.filter(contract => contract.status === 'expiring_soon')
    .sort((a, b) => a.days_left - b.days_left);
});

// Загружаем данные контрактов
const fetchContracts = async () => {
  isLoading.value = true;
  try {
    const response = await axios.get('/api/contracts', {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    });
    contracts.value = response.data;
    
    // Рассчитываем статистику
    calculateStatistics();
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Ошибка при загрузке данных';
  } finally {
    isLoading.value = false;
  }
};

// Рассчитываем статистику по контрактам
const calculateStatistics = () => {
  statistics.value = {
    active: contracts.value.filter(c => c.status === 'active').length,
    expiringSoon: contracts.value.filter(c => c.status === 'expiring_soon').length,
    expired: contracts.value.filter(c => c.status === 'expired').length,
    total: contracts.value.length
  };
};

// Форматирование даты
const formatDate = (dateString: string) => {
  return format(new Date(dateString), 'dd MMMM yyyy', { locale: ru });
};

// Определяем класс для отображения количества оставшихся дней
const getDaysLeftClass = (daysLeft: number) => {
  if (daysLeft < 0) return 'days-expired';
  if (daysLeft <= 10) return 'days-critical';
  if (daysLeft <= 30) return 'days-warning';
  return 'days-normal';
};

onMounted(() => {
  fetchContracts();
});
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 1.875rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  text-align: center;
}

.stat-title {
  font-size: 1rem;
  font-weight: 500;
  color: #4b5563;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #1a56db;
}

.dashboard-section {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 1rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #6b7280;
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

.btn-view {
  display: inline-block;
  background-color: #1a56db;
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
  text-decoration: none;
}

.btn-view:hover {
  background-color: #1e429f;
}
</style>