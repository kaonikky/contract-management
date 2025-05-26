import { google } from 'googleapis';
import type { JWT } from 'google-auth-library';
import { User, Contract, ContractHistoryEntry } from "@shared/schema";
import { differenceInDays, parse, isValid, format } from 'date-fns';

export class GoogleSheetsStorage {
  private auth: JWT;
  private sheets: any;
  private spreadsheetId: string;

  constructor(credentials: any) {
    this.auth = new google.auth.JWT(
      credentials.client_email,
      undefined,
      credentials.private_key,
      ['https://www.googleapis.com/auth/spreadsheets']
    );

    this.sheets = google.sheets({ version: 'v4', auth: this.auth });
    this.spreadsheetId = process.env.VITE_GOOGLE_SHEETS_ID!;
  }

  private async initializeSheets() {
    const sheetsInfo = await this.sheets.spreadsheets.get({
      spreadsheetId: this.spreadsheetId
    });

    const sheets = sheetsInfo.data.sheets;
    const requiredSheets = ['users', 'contracts'];

    for (const sheetName of requiredSheets) {
      if (!sheets.find((s: any) => s.properties.title === sheetName)) {
        await this.sheets.spreadsheets.batchUpdate({
          spreadsheetId: this.spreadsheetId,
          requestBody: {
            requests: [{
              addSheet: {
                properties: { title: sheetName }
              }
            }]
          }
        });

        const headers = sheetName === 'users'
          ? ['username', 'password', 'role']
          : ['companyName', 'inn', 'director', 'address', 'endDate', 'comments', 'hasND', 'lawyerId', 'status', 'history'];

        await this.sheets.spreadsheets.values.update({
          spreadsheetId: this.spreadsheetId,
          range: `${sheetName}!A1:${String.fromCharCode(65 + headers.length - 1)}1`,
          valueInputOption: 'RAW',
          requestBody: {
            values: [headers]
          }
        });
      }
    }
  }

  async initialize() {
    await this.initializeSheets();
  }

  async getAllUsers(): Promise<User[]> {
    try {
      const response = await this.sheets.spreadsheets.values.get({
        spreadsheetId: this.spreadsheetId,
        range: 'users!A2:D'
      });

      const values = response.data.values || [];
      return values.map((row: any[], index: number) => ({
        id: index + 1,
        username: row[0] || '',
        password: row[1] || '',
        role: (row[2] || 'lawyer') as "admin" | "lawyer"
      }));
    } catch (error) {
      console.error("Ошибка при получении пользователей:", error);
      throw error;
    }
  }

  async createUser(user: Omit<User, 'id'>): Promise<User> {
    try {
      const users = await this.getAllUsers();
      const newId = users.length + 1;

      await this.sheets.spreadsheets.values.append({
        spreadsheetId: this.spreadsheetId,
        range: 'users!A2:D2',
        valueInputOption: 'RAW',
        requestBody: {
          values: [[user.username, user.password, user.role]]
        }
      });

      return { ...user, id: newId };
    } catch (error) {
      console.error("Ошибка при создании пользователя:", error);
      throw error;
    }
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    try {
      const users = await this.getAllUsers();
      return users.find(user => user.username === username);
    } catch (error) {
      console.error("Ошибка при поиске пользователя по имени:", error);
      throw error;
    }
  }

  async getUser(id: number): Promise<User | undefined> {
    try {
      const users = await this.getAllUsers();
      return users.find(user => user.id === id);
    } catch (error) {
      console.error(`Ошибка при получении пользователя с ID ${id}:`, error);
      throw error;
    }
  }

  async getAllContracts(): Promise<Contract[]> {
    try {
      const response = await this.sheets.spreadsheets.values.get({
        spreadsheetId: this.spreadsheetId,
        range: 'contracts!A2:J'
      });

      const values = response.data.values || [];
      return values.map((row: any[], index: number) => {
        try {
          // Проверка на минимальную длину строки
          if (!row || row.length < 5 || !row[4]) {
            console.warn(`Строка ${index + 2} имеет неверный формат или отсутствует дата. Пропускаем.`);
            return null;
          }

          // Обработка даты с проверкой на валидность
          let endDate;
          try {
            endDate = parse(row[4], 'dd.MM.yyyy', new Date());
            if (!isValid(endDate)) {
              console.warn(`Неверный формат даты в строке ${index + 2}: ${row[4]}. Используем текущую дату.`);
              endDate = new Date();
            }
          } catch (error) {
            console.warn(`Ошибка при парсинге даты в строке ${index + 2}: ${row[4]}. Используем текущую дату.`);
            endDate = new Date();
          }

          const today = new Date();
          const daysLeft = -differenceInDays(today, endDate);

          // Обработка истории с защитой от ошибок JSON
          let history: ContractHistoryEntry[] = [];
          try {
            const historyStr = row[9] || '[]';
            // Удостоверяемся, что история - это строка
            if (typeof historyStr === 'string') {
              history = JSON.parse(historyStr);
              if (!Array.isArray(history)) {
                console.warn(`Неверный формат истории в строке ${index + 2}. Используем пустой массив.`);
                history = [];
              }
            } else {
              console.warn(`Неверный формат истории в строке ${index + 2}. Используем пустой массив.`);
              history = [];
            }
          } catch (error) {
            console.warn(`Ошибка при парсинге истории в строке ${index + 2}: ${error}. Используем пустой массив.`);
            history = [];
          }

          // Проверка на наличие всех необходимых полей и коррекция типов данных
          return {
            id: index + 1,
            companyName: String(row[0] || ''),
            inn: String(row[1] || ''),
            director: String(row[2] || ''),
            address: String(row[3] || ''),
            endDate: endDate,
            comments: String(row[5] || ''),
            hasND: String(row[6]).toLowerCase() === 'true',
            lawyerId: parseInt(String(row[7])) || 0,
            status: (row[8] as "active" | "expiring_soon" | "expired") || "active",
            history: history,
            createdAt: new Date(),
            daysLeft
          };
        } catch (error) {
          console.error(`Ошибка при обработке контракта в строке ${index + 2}:`, error);
          return null;
        }
      }).filter(Boolean) as Contract[];
    } catch (error) {
      console.error("Ошибка при получении всех контрактов:", error);
      throw error;
    }
  }

  async createContract(contract: Omit<Contract, 'id'>): Promise<Contract> {
    try {
      const contracts = await this.getAllContracts();

      // Check for existing INN first
      const existingContract = contracts.find(c => c.inn === contract.inn);
      if (existingContract) {
        throw new Error("Контракт с таким ИНН уже существует");
      }

      const newId = (contracts.length + 1);
      const endDate = new Date(contract.endDate);

      if (!isValid(endDate)) {
        throw new Error("Некорректная дата окончания контракта");
      }

      const endDateStr = format(endDate, 'dd.MM.yyyy');

      await this.sheets.spreadsheets.values.append({
        spreadsheetId: this.spreadsheetId,
        range: 'contracts!A2:J2',
        valueInputOption: 'RAW',
        requestBody: {
          values: [[
            contract.companyName,
            contract.inn,
            contract.director,
            contract.address,
            endDateStr,
            contract.comments || '',
            contract.hasND.toString(),
            contract.lawyerId.toString(),
            contract.status,
            JSON.stringify(contract.history)
          ]]
        }
      });

      return { ...contract, id: newId };
    } catch (error) {
      if (error instanceof Error && error.message.includes("ИНН уже существует")) {
        throw error; // Re-throw INN duplicate error
      }
      console.error('Error in GoogleSheetsStorage.createContract:', error);
      throw new Error("Ошибка при создании контракта");
    }
  }

  async updateContract(id: number, updates: Partial<Contract>): Promise<Contract> {
    try {
      const contracts = await this.getAllContracts();
      const contract = contracts.find(c => c.id === id);
      if (!contract) throw new Error("Contract not found");

      const updatedContract = { ...contract, ...updates };
      const rowIndex = id + 1;

      // Проверяем дату
      const endDate = new Date(updatedContract.endDate);
      if (!isValid(endDate)) {
        throw new Error("Некорректная дата окончания контракта");
      }
      const endDateStr = format(endDate, "dd.MM.yyyy");

      // Проверяем содержимое истории на корректность JSON
      let historyStr;
      try {
        historyStr = JSON.stringify(updatedContract.history || []);
        // Проверка на максимальную длину JSON (ограничение Google Sheets - 50000 символов в ячейке)
        if (historyStr.length > 40000) {
          console.warn(`История контракта слишком большая (${historyStr.length} символов). Обрезаем...`);
          // Обрезаем историю, оставляя только последние 10 записей
          const historyCopy = [...(updatedContract.history || [])];
          const latestEntries = historyCopy.slice(-10);
          updatedContract.history = latestEntries;
          historyStr = JSON.stringify(latestEntries);
        }
      } catch (error) {
        console.error("Ошибка при сериализации истории контракта:", error);
        historyStr = "[]";
        updatedContract.history = [];
      }

      // Проверяем наличие обязательных полей
      const values = [
        updatedContract.companyName || '',
        updatedContract.inn || '',
        updatedContract.director || '',
        updatedContract.address || '',
        endDateStr,
        updatedContract.comments || '',
        String(updatedContract.hasND || false),
        String(updatedContract.lawyerId || 0),
        updatedContract.status || 'active',
        historyStr
      ];

      await this.sheets.spreadsheets.values.update({
        spreadsheetId: this.spreadsheetId,
        range: `contracts!A${rowIndex}:J${rowIndex}`,
        valueInputOption: 'RAW',
        requestBody: {
          values: [values]
        }
      });

      return updatedContract;
    } catch (error) {
      console.error("Ошибка при обновлении контракта в Google Sheets:", error);
      throw error;
    }
  }

  async deleteContract(id: number): Promise<void> {
    try {
      const rowIndex = id + 1;
      await this.sheets.spreadsheets.values.clear({
        spreadsheetId: this.spreadsheetId,
        range: `contracts!A${rowIndex}:J${rowIndex}`
      });
    } catch (error) {
      console.error(`Ошибка при удалении контракта с ID ${id}:`, error);
      throw error;
    }
  }

  async updateUserPassword(id: number, hashedPassword: string): Promise<void> {
    try {
      const users = await this.getAllUsers();
      const userIndex = users.findIndex(user => user.id === id);

      if (userIndex === -1) throw new Error("User not found");

      const rowIndex = userIndex + 2;

      await this.sheets.spreadsheets.values.update({
        spreadsheetId: this.spreadsheetId,
        range: `users!B${rowIndex}`,
        valueInputOption: 'RAW',
        requestBody: {
          values: [[hashedPassword]]
        }
      });
    } catch (error) {
      console.error(`Ошибка при обновлении пароля пользователя с ID ${id}:`, error);
      throw error;
    }
  }
}