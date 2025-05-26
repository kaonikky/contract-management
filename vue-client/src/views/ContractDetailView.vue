<template>
  <div class="contract-detail">
    <div class="back-button-container">
      <router-link to="/contracts" class="back-button">
        &larr; Назад к списку контрактов
      </router-link>
    </div>

    <div v-if="isLoading" class="loading-state">
      Загрузка данных...
    </div>

    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-else class="contract-container">
      <div class="header-section">
        <div>
          <h1 class="page-title">{{ contract.company_name }}</h1>
          <div class="company-inn">ИНН: {{ contract.inn }}</div>
        </div>
        
        <div class="status-badge-container">
          <span :class="getStatusBadgeClass(contract.status)">
            {{ getStatusText(contract.status) }}
          </span>
          
          <div class="days-left">
            <span :class="getDaysLeftClass(contract.days_left)">
              {{ contract.days_left > 0 ? `${contract.days_left} дней до истечения` : 'Срок истек' }}
            </span>
          </div>
        </div>
      </div>

      <div class="contract-actions">
        <button @click="isEditMode = true" class="btn-edit" v-if="!isEditMode">
          Редактировать
        </button>
        <button @click="saveContract" class="btn-save" v-if="isEditMode">
          Сохранить
        </button>
        <button @click="cancelEdit" class="btn-cancel" v-if="isEditMode">
          Отменить
        </button>
      </div>

      <!-- Данные контракта для просмотра -->
      <div v-if="!isEditMode" class="contract-details">
        <!-- Основная информация -->
        <div class="details-section">
          <h2 class="section-title">Информация о компании</h2>
          
          <div class="detail-row">
            <div class="detail-label">Название компании:</div>
            <div class="detail-value">{{ contract.company_name }}</div>
          </div>
          
          <div class="detail-row">
            <div class="detail-label">ИНН:</div>
            <div class="detail-value">{{ contract.inn }}</div>
          </div>
          
          <div class="detail-row">
            <div class="detail-label">Директор:</div>
            <div class="detail-value">{{ contract.director }}</div>
          </div>
          
          <div class="detail-row">
            <div class="detail-label">Адрес:</div>
            <div class="detail-value">{{ contract.address }}</div>
          </div>
        </div>

        <!-- Данные контракта -->
        <div class="details-section">
          <h2 class="section-title">Данные контракта</h2>
          
          <div class="detail-row">
            <div class="detail-label">Дата окончания:</div>
            <div class="detail-value">{{ formatDate(contract.end_date) }}</div>
          </div>
          
          <div class="detail-row">
            <div class="detail-label">Наличие NDA:</div>
            <div class="detail-value">{{ contract.has_nd ? 'Да' : 'Нет' }}</div>
          </div>
          
          <div class="detail-row">
            <div class="detail-label">Комментарии:</div>
            <div class="detail-value">{{ contract.comments || 'Нет комментариев' }}</div>
          </div>
        </div>

        <!-- История изменений -->
        <div class="details-section">
          <h2 class="section-title">История изменений</h2>
          
          <div v-if="!contract.history || contract.history.length === 0" class="no-history">
            Нет истории изменений
          </div>
          
          <div v-else class="history-list">
            <div v-for="(entry, index) in contract.history" :key="index" class="history-entry">
              <div class="history-header">
                <span class="history-action">{{ getActionText(entry.action) }}</span>
                <span class="history-user">{{ entry.username }}</span>
                <span class="history-time">{{ formatDateTime(entry.timestamp) }}</span>
              </div>
              
              <div v-if="entry.changes && Object.keys(entry.changes).length > 0" class="history-changes">
                <div v-for="(change, field) in entry.changes" :key="field" class="change-entry">
                  <span class="change-field">{{ getFieldName(field) }}:</span>
                  <span class="change-old">{{ formatChangeValue(field, change.old) }}</span>
                  <span class="change-arrow">&rarr;</span>
                  <span class="change-new">{{ formatChangeValue(field, change.new) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Форма редактирования -->
      <div v-if="isEditMode" class="edit-form">
        <div class="form-section">
          <h2 class="section-title">Информация о компании</h2>
          
          <div class="form-group">
            <label for="company_name" class="form-label">Название компании</label>
            <input 
              type="text"
              id="company_name"
              v-model="editedContract.company_name"
              class="form-input"
              required
            />
          </div>
          
          <div class="form-group">
            <label for="inn" class="form-label">ИНН</label>
            <input 
              type="text"
              id="inn"
              v-model="editedContract.inn"
              class="form-input"
              required
            />
          </div>
          
          <div class="form-group">
            <label for="director" class="form-label">Директор</label>
            <input 
              type="text"
              id="director"
              v-model="editedContract.director"
              class="form-input"
              required
            />
          </div>
          
          <div class="form-group">
            <label for="address" class="form-label">Адрес</label>
            <textarea
              id="address"
              v-model="editedContract.address"
              class="form-textarea"
              required
            ></textarea>
          </div>
        </div>

        <div class="form-section">
          <h2 class="section-title">Данные контракта</h2>
          
          <div class="form-group">
            <label for="end_date" class="form-label">Дата окончания</label>
            <input 
              type="date"
              id="end_date"
              v-model="endDateFormatted"
              class="form-input"
              required
            />
          </div>
          
          <div class="form-group">
            <label class="form-label has-nd-checkbox">
              <input type="checkbox" v-model="editedContract.has_nd" />
              Наличие NDA
            </label>
          </div>
          
          <div class="form-group">
            <label for="comments" class="form-label">Комментарии</label>
            <textarea
              id="comments"
              v-model="editedContract.comments"
              class="form-textarea"
            ></textarea>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import { format, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

interface ContractHistoryEntry {
  userId: number;
  username: string;
  action: string;
  changes: Record<string, { old: any; new: any }>;
  timestamp: string;
}

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
  history: ContractHistoryEntry[];
  created_at: string;
  updated_at?: string;
}

// Состояние
const contract = ref<Contract>({} as Contract);
const editedContract = ref<Contract>({} as Contract);
const isLoading = ref(true);
const error = ref('');
const isEditMode = ref(false);

// Форматированная дата окончания для input type="date"
const endDateFormatted = computed({
  get: () => {
    if (!editedContract.value.end_date) return '';
    const date = new Date(editedContract.value.end_date);
    return format(date, 'yyyy-MM-dd');
  },
  set: (value: string) => {
    editedContract.value.end_date = value;
  }
});

// Загрузка контракта
const fetchContract = async () => {
  const contractId = route.params.id;
  
  isLoading.value = true;
  try {
    const response = await axios.get(`/api/contracts/${contractId}`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    });
    contract.value = response.data;
    // Копируем данные в объект для редактирования
    editedContract.value = { ...response.data };
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Ошибка при загрузке данных контракта';
  } finally {
    isLoading.value = false;
  }
};

// Сохранение изменений
const saveContract = async () => {
  isLoading.value = true;
  try {
    const response = await axios.put(`/api/contracts/${contract.value.id}`, editedContract.value, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    });
    contract.value = response.data;
    isEditMode.value = false;
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Ошибка при сохранении данных контракта';
  } finally {
    isLoading.value = false;
  }
};

// Отмена редактирования
const cancelEdit = () => {
  editedContract.value = { ...contract.value };
  isEditMode.value = false;
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

// Получение класса для количества дней
const getDaysLeftClass = (daysLeft: number) => {
  if (daysLeft < 0) return 'days-left-expired';
  if (daysLeft <= 10) return 'days-left-critical';
  if (daysLeft <= 30) return 'days-left-warning';
  return 'days-left-normal';
};

// Получение текста действия
const getActionText = (action: string) => {
  switch (action) {
    case 'create': return 'Создан';
    case 'update': return 'Обновлен';
    case 'delete': return 'Удален';
    default: return action;
  }
};

// Получение имени поля для истории
const getFieldName = (field: string) => {
  const fieldMap: Record<string, string> = {
    company_name: 'Название компании',
    inn: 'ИНН',
    director: 'Директор',
    address: 'Адрес',
    end_date: 'Дата окончания',
    has_nd: 'Наличие NDA',
    comments: 'Комментарии',
    status: 'Статус',
    lawyer_id: 'Юрист'
  };
  
  return fieldMap[field] || field;
};

// Форматирование значения изменения
const formatChangeValue = (field: string, value: any) => {
  if (value === null || value === undefined) return 'Не указано';
  
  if (field === 'end_date') {
    return format(new Date(value), 'dd MMMM yyyy', { locale: ru });
  }
  
  if (field === 'has_nd') {
    return value ? 'Да' : 'Нет';
  }
  
  return value.toString();
};

// Форматирование даты
const formatDate = (dateString: string) => {
  return format(new Date(dateString), 'dd MMMM yyyy', { locale: ru });
};

// Форматирование даты и времени
const formatDateTime = (dateTimeString: string) => {
  return format(parseISO(dateTimeString), 'dd.MM.yyyy HH:mm', { locale: ru });
};

onMounted(() => {
  fetchContract();
});
</script>

<style scoped>
.contract-detail {
  max-width: 900px;
  margin: 0 auto;
  padding: 1rem;
}

.back-button-container {
  margin-bottom: 1.5rem;
}

.back-button {
  display: inline-block;
  color: #4b5563;
  text-decoration: none;
  font-size: 0.875rem;
}

.back-button:hover {
  color: #1a56db;
}

.loading-state,
.error-message {
  padding: 2rem;
  text-align: center;
}

.error-message {
  color: #dc2626;
}

.contract-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 0.25rem;
}

.company-inn {
  color: #6b7280;
  font-size: 0.875rem;
}

.status-badge-container {
  text-align: right;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
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

.days-left {
  font-size: 0.875rem;
}

.days-left-normal {
  color: #059669;
}

.days-left-warning {
  color: #d97706;
}

.days-left-critical {
  color: #dc2626;
}

.days-left-expired {
  color: #dc2626;
  font-weight: 600;
}

.contract-actions {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.btn-edit,
.btn-save,
.btn-cancel {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-size: 0.875rem;
  cursor: pointer;
  border: none;
}

.btn-edit {
  background-color: #1a56db;
  color: white;
}

.btn-edit:hover {
  background-color: #1e429f;
}

.btn-save {
  background-color: #059669;
  color: white;
}

.btn-save:hover {
  background-color: #047857;
}

.btn-cancel {
  background-color: #f3f4f6;
  color: #4b5563;
  border: 1px solid #d1d5db;
}

.btn-cancel:hover {
  background-color: #e5e7eb;
}

.contract-details,
.edit-form {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}

.details-section,
.form-section {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.detail-row {
  display: grid;
  grid-template-columns: 180px 1fr;
  margin-bottom: 0.75rem;
}

.detail-label {
  font-weight: 500;
  color: #4b5563;
}

.detail-value {
  color: #111827;
}

.no-history {
  color: #6b7280;
  font-style: italic;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.history-entry {
  padding: 0.75rem;
  background-color: #f9fafb;
  border-radius: 4px;
}

.history-header {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.history-action {
  font-weight: 500;
  color: #1a56db;
}

.history-user {
  color: #4b5563;
}

.history-time {
  color: #6b7280;
  font-size: 0.75rem;
  margin-left: auto;
}

.history-changes {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.change-entry {
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.change-field {
  font-weight: 500;
  color: #4b5563;
}

.change-old {
  color: #dc2626;
  text-decoration: line-through;
}

.change-arrow {
  color: #6b7280;
}

.change-new {
  color: #059669;
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
.form-textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
}

.form-textarea {
  min-height: 100px;
  resize: vertical;
}

.has-nd-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

@media (min-width: 768px) {
  .contract-details,
  .edit-form {
    grid-template-columns: 1fr 1fr;
  }
  
  .details-section:last-child,
  .form-section:last-child {
    grid-column: span 2;
  }
}
</style>