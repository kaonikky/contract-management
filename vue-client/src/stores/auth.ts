import { defineStore } from 'pinia'
import axios from 'axios'

interface User {
  id: number
  username: string
  role: string
}

interface LoginCredentials {
  username: string
  password: string
}

interface State {
  user: User | null
  isLoading: boolean
  error: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): State => ({
    user: null,
    isLoading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => {
      // Проверяем наличие пользователя или флага в localStorage
      return !!state.user || localStorage.getItem('authenticated') === 'true'
    }
  },

  actions: {
    async login(credentials: LoginCredentials) {
      this.isLoading = true
      this.error = null
      try {
        const response = await axios.post('/api/login', credentials)
        this.user = response.data
        // Сохраняем признак авторизации, поскольку используем сессионную аутентификацию
        localStorage.setItem('authenticated', 'true')
        
        return this.user
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Ошибка при входе в систему'
        throw new Error(this.error)
      } finally {
        this.isLoading = false
      }
    },

    async fetchCurrentUser() {
      try {
        const response = await axios.get('/api/user')
        this.user = response.data
        return this.user
      } catch (error) {
        this.logout()
        return null
      }
    },

    async register(userData: LoginCredentials & { role: string }) {
      this.isLoading = true
      this.error = null
      try {
        const response = await axios.post('/api/users', userData)
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Ошибка при регистрации пользователя'
        throw new Error(this.error)
      } finally {
        this.isLoading = false
      }
    },

    async logout() {
      try {
        await axios.post('/api/logout')
      } catch (error) {
        console.error('Ошибка при выходе из системы:', error)
      } finally {
        this.user = null
        localStorage.removeItem('authenticated')
      }
    },

    async updateUserPassword(userId: number, password: string) {
      this.isLoading = true
      this.error = null
      try {
        const response = await axios.put(`/api/users/${userId}/password`, { password })
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Ошибка при обновлении пароля'
        throw new Error(this.error)
      } finally {
        this.isLoading = false
      }
    },

    async checkAuth() {
      if (localStorage.getItem('authenticated') === 'true' && !this.user) {
        await this.fetchCurrentUser()
      }
      return this.isAuthenticated
    }
  }
})