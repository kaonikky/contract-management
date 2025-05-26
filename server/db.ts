import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "@shared/schema";
import dotenv from "dotenv";

// Загружаем переменные окружения
dotenv.config();

// Проверяем наличие строки подключения
if (!process.env.DATABASE_URL) {
  throw new Error("Отсутствует переменная окружения DATABASE_URL");
}

// Инициализируем пул подключений к PostgreSQL
export const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === "production" ? { rejectUnauthorized: false } : undefined
});

// Инициализируем ORM с нашей схемой
export const db = drizzle(pool, { schema });

// Функция для проверки соединения с базой данных
export async function testConnection(): Promise<boolean> {
  try {
    const client = await pool.connect();
    client.release();
    console.log("✅ Соединение с базой данных установлено успешно");
    return true;
  } catch (error) {
    console.error("❌ Ошибка подключения к базе данных:", error);
    return false;
  }
}

// Инициализируем таблицы сессий, если они еще не созданы
export async function initSessionTable(): Promise<void> {
  try {
    const client = await pool.connect();
    
    try {
      await client.query(`
        CREATE TABLE IF NOT EXISTS "session" (
          "sid" varchar NOT NULL COLLATE "default",
          "sess" json NOT NULL,
          "expire" timestamp(6) NOT NULL
        )
        WITH (OIDS=FALSE);
        
        ALTER TABLE "session" ADD CONSTRAINT "session_pkey" 
          PRIMARY KEY ("sid") NOT DEFERRABLE INITIALLY IMMEDIATE;
          
        CREATE INDEX IF NOT EXISTS "IDX_session_expire" 
          ON "session" ("expire");
      `);
      
      console.log("✅ Таблица сессий успешно инициализирована");
    } finally {
      client.release();
    }
  } catch (error) {
    console.error("❌ Ошибка при инициализации таблицы сессий:", error);
    throw error;
  }
}

// Экспортируем функцию для инициализации базы данных
export async function initializeDatabase(): Promise<void> {
  try {
    await testConnection();
    await initSessionTable();
    console.log("✅ База данных успешно инициализирована");
  } catch (error) {
    console.error("❌ Ошибка инициализации базы данных:", error);
    throw error;
  }
}