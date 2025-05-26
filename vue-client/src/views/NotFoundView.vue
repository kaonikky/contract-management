<template>
  <div class="not-found">
    <div class="not-found-content">
      <h1 class="error-code">404</h1>
      <h2 class="error-title">Страница не найдена</h2>
      <p class="error-message">
        Извините, запрашиваемая вами страница не существует или была перемещена.
      </p>
      <router-link to="/" class="back-link">
        Вернуться на главную
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 80vh;
  text-align: center;
}

.not-found-content {
  max-width: 500px;
  padding: 2rem;
}

.error-code {
  font-size: 6rem;
  font-weight: 700;
  color: #1a56db;
  margin: 0;
  line-height: 1;
}

.error-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
  margin: 1rem 0;
}

.error-message {
  font-size: 1rem;
  color: #6b7280;
  margin-bottom: 2rem;
}

.back-link {
  display: inline-block;
  background-color: #1a56db;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  text-decoration: none;
  font-weight: 500;
  transition: background-color 0.2s;
}

.back-link:hover {
  background-color: #1e429f;
}
</style>