module.exports = {
  apps: [
    {
      name: "contracts-backend",
      script: "cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000",
      interpreter: "bash",
      env: {
        NODE_ENV: "production",
        SESSION_SECRET: process.env.SESSION_SECRET || "my-secret-12345"
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G"
    },
    {
      name: "contracts-frontend",
      script: "cd vue-client && npm run preview",
      env: {
        NODE_ENV: "production",
        PORT: 5000
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G"
    }
  ]
};