import { google } from 'googleapis';
import { drizzle } from 'drizzle-orm/node-postgres';
import { eq } from 'drizzle-orm';
import pg from 'pg';
const { Pool } = pg;
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Импортируем схему из .ts файла с помощью динамического импорта
// Мы используем динамический импорт, так как это ES модуль, но импортируем TypeScript файл
let schemaModule;
try {
  // Попытка импортировать из скомпилированного JS
  schemaModule = await import('./shared/schema.js');
} catch (error) {
  console.error('Ошибка импорта схемы:', error.message);
  console.error('Убедитесь, что TypeScript файлы были скомпилированы в JavaScript');
  process.exit(1);
}

const { users, contracts } = schemaModule;
import crypto from 'crypto';
import { promisify } from 'util';

// Инициализация PostgreSQL подключения
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});
const db = drizzle(pool);

// Функции для хеширования паролей (аналогично auth.ts)
const scryptAsync = promisify(crypto.scrypt);

async function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const buf = await scryptAsync(password, salt, 64);
  return `${buf.toString('hex')}.${salt}`;
}

// Константы
const DEFAULT_PASSWORD = 'password123';  // Пароль по умолчанию для импортированных пользователей

// Класс для работы с Google Sheets API
class GoogleSheetsMigrator {
  constructor(credentialsPath, spreadsheetId) {
    this.credentialsPath = credentialsPath;
    this.spreadsheetId = spreadsheetId;
    this.sheetsApi = null;
    
    console.log(`Инициализация мигратора с ID таблицы: ${spreadsheetId}`);
  }
  
  async initialize() {
    try {
      // Загружаем учетные данные из файла
      const credentialsContent = fs.readFileSync(this.credentialsPath, 'utf8');
      const credentials = JSON.parse(credentialsContent);
      
      // Инициализируем клиент аутентификации
      const auth = new google.auth.GoogleAuth({
        credentials,
        scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly']
      });
      
      // Создаем клиент Google Sheets API
      this.sheetsApi = google.sheets({ version: 'v4', auth: await auth.getClient() });
      console.log('Google Sheets API успешно инициализирован');
      return true;
    } catch (error) {
      console.error(`Ошибка при инициализации Google Sheets API: ${error.message}`);
      return false;
    }
  }
  
  async fetchUsers() {
    try {
      // Получаем данные из листа "Users"
      const response = await this.sheetsApi.spreadsheets.values.get({
        spreadsheetId: this.spreadsheetId,
        range: 'Users!A2:D100'  // Диапазон ячеек с данными пользователей
      });
      
      const rows = response.data.values || [];
      
      if (rows.length === 0) {
        console.warn('Данные о пользователях не найдены');
        return [];
      }
      
      const users = [];
      for (const row of rows) {
        if (row.length >= 3) {  // Проверяем, что в строке есть минимум 3 столбца
          const user = {
            id: row[0] && /^\d+$/.test(row[0]) ? parseInt(row[0], 10) : null,
            username: row[1],
            role: row[2],
            created_at: row.length > 3 ? new Date(row[3]) : new Date()
          };
          users.push(user);
        }
      }
      
      console.log(`Получено ${users.length} пользователей из Google Sheets`);
      return users;
    } catch (error) {
      console.error(`Ошибка при получении данных пользователей: ${error.message}`);
      return [];
    }
  }
  
  async fetchContracts() {
    try {
      // Получаем данные из листа "Contracts"
      const response = await this.sheetsApi.spreadsheets.values.get({
        spreadsheetId: this.spreadsheetId,
        range: 'Contracts!A2:K100'  // Диапазон ячеек с данными контрактов
      });
      
      const rows = response.data.values || [];
      
      if (rows.length === 0) {
        console.warn('Данные о контрактах не найдены');
        return [];
      }
      
      const contracts = [];
      for (const row of rows) {
        if (row.length >= 7) {  // Проверяем, что в строке есть минимум 7 столбцов
          try {
            const contract = {
              id: row[0] && /^\d+$/.test(row[0]) ? parseInt(row[0], 10) : null,
              company_name: row[1],
              inn: row[2],
              director: row[3],
              address: row[4],
              end_date: row[5] ? new Date(row[5]) : null,
              lawyer_id: row[6] && /^\d+$/.test(row[6]) ? parseInt(row[6], 10) : null,
              status: row.length > 7 ? row[7] : 'active',
              comments: row.length > 8 ? row[8] : null,
              has_nd: row.length > 9 ? ['true', '1', 'yes'].includes(row[9].toLowerCase()) : false,
              created_at: row.length > 10 ? new Date(row[10]) : new Date(),
              history: JSON.stringify([])  // Пустая история изменений по умолчанию
            };
            contracts.push(contract);
          } catch (parseError) {
            console.error(`Ошибка при обработке строки контракта: ${parseError.message}`);
          }
        }
      }
      
      console.log(`Получено ${contracts.length} контрактов из Google Sheets`);
      return contracts;
    } catch (error) {
      console.error(`Ошибка при получении данных контрактов: ${error.message}`);
      return [];
    }
  }
}

// Функция для миграции пользователей
async function migrateUsers(migrator) {
  const usersData = await migrator.fetchUsers();
  
  if (usersData.length === 0) {
    console.warn('Нет пользователей для миграции');
    return;
  }
  
  let count = 0;
  for (const userData of usersData) {
    try {
      // Проверяем, существует ли пользователь уже в базе
      const existingUser = await db.select().from(users).where(eq(users.username, userData.username));
      
      if (existingUser.length > 0) {
        console.log(`Пользователь ${userData.username} уже существует в базе`);
        continue;
      }
      
      // Хешируем пароль
      const hashedPassword = await hashPassword(DEFAULT_PASSWORD);
      
      // Создаем нового пользователя
      await db.insert(users).values({
        username: userData.username,
        password: hashedPassword,
        role: userData.role
      });
      
      count++;
      console.log(`Создан пользователь ${userData.username}`);
    } catch (error) {
      console.error(`Ошибка при создании пользователя ${userData.username}: ${error.message}`);
    }
  }
  
  console.log(`Миграция пользователей завершена. Создано ${count} новых пользователей`);
}

// Функция для миграции контрактов
async function migrateContracts(migrator) {
  const contractsData = await migrator.fetchContracts();
  
  if (contractsData.length === 0) {
    console.warn('Нет контрактов для миграции');
    return;
  }
  
  let count = 0;
  for (const contractData of contractsData) {
    try {
      // Проверяем, существует ли контракт уже в базе
      const existingContract = await db.select().from(contracts).where(eq(contracts.inn, contractData.inn));
      
      if (existingContract.length > 0) {
        console.log(`Контракт с ИНН ${contractData.inn} уже существует в базе`);
        continue;
      }
      
      // Проверяем, существует ли юрист
      const lawyer = await db.select().from(users).where(eq(users.id, contractData.lawyer_id));
      
      if (lawyer.length === 0) {
        console.warn(`Юрист с ID ${contractData.lawyer_id} не найден. Пропускаем контракт ${contractData.company_name}`);
        continue;
      }
      
      // Создаем запись в истории
      const historyEntry = [{
        userId: lawyer[0].id,
        username: lawyer[0].username,
        action: 'create',
        changes: {},
        timestamp: new Date().toISOString()
      }];
      
      // Создаем новый контракт
      await db.insert(contracts).values({
        companyName: contractData.company_name,
        inn: contractData.inn,
        director: contractData.director,
        address: contractData.address,
        endDate: contractData.end_date,
        status: contractData.status,
        comments: contractData.comments,
        hasND: contractData.has_nd,
        lawyerId: lawyer[0].id,
        createdAt: contractData.created_at,
        history: JSON.stringify(historyEntry)
      });
      
      count++;
      console.log(`Создан контракт для компании ${contractData.company_name}`);
    } catch (error) {
      console.error(`Ошибка при создании контракта ${contractData.company_name}: ${error.message}`);
    }
  }
  
  console.log(`Миграция контрактов завершена. Создано ${count} новых контрактов`);
}

// Основная функция миграции
async function runMigration() {
  // Проверяем наличие необходимых переменных окружения
  const credentialsPath = process.env.GOOGLE_CREDENTIALS_PATH;
  const spreadsheetId = process.env.GOOGLE_SPREADSHEET_ID;
  
  if (!credentialsPath || !spreadsheetId) {
    console.error('Отсутствуют необходимые переменные окружения для миграции');
    console.error('Установите переменные окружения GOOGLE_CREDENTIALS_PATH и GOOGLE_SPREADSHEET_ID');
    process.exit(1);
  }
  
  console.log('Начало процесса миграции данных из Google Sheets в PostgreSQL');
  
  // Инициализируем мигратор
  const migrator = new GoogleSheetsMigrator(credentialsPath, spreadsheetId);
  
  if (!(await migrator.initialize())) {
    console.error('Не удалось инициализировать мигратор. Миграция прервана.');
    process.exit(1);
  }
  
  try {
    // Выполняем миграцию пользователей
    console.log('Начало миграции пользователей');
    await migrateUsers(migrator);
    
    // Выполняем миграцию контрактов
    console.log('Начало миграции контрактов');
    await migrateContracts(migrator);
    
    console.log('Миграция успешно завершена');
  } catch (error) {
    console.error(`Ошибка во время миграции: ${error.message}`);
    process.exit(1);
  } finally {
    // Закрываем соединение с базой данных
    await pool.end();
  }
}

// Запускаем процесс миграции
runMigration().catch(error => {
  console.error(`Непредвиденная ошибка: ${error.message}`);
  process.exit(1);
});