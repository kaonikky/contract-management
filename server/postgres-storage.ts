import { User, InsertUser, Contract, InsertContract, ContractHistoryEntry, users, contracts } from "@shared/schema";
import { db, pool } from "./db";
import { IStorage } from "./storage";
import { eq, and } from "drizzle-orm";
import { addDays, parseISO, isAfter, differenceInDays } from "date-fns";
import session from "express-session";
import connectPg from "connect-pg-simple";

// Инициализируем хранилище сессий с PostgreSQL
const PostgresSessionStore = connectPg(session);

export class PostgresStorage implements IStorage {
  sessionStore: session.Store;

  constructor() {
    this.sessionStore = new PostgresSessionStore({
      pool,
      // Указываем, что нужно создать таблицу, если её нет
      createTableIfMissing: true
    });
  }

  // Вспомогательная функция для расчета статуса контракта
  private calculateContractStatus(endDate: Date): { status: "active" | "expiring_soon" | "expired"; daysLeft: number } {
    const today = new Date();
    const thirtyDaysFromNow = addDays(today, 30);
    const daysLeft = differenceInDays(new Date(endDate), today);

    if (isAfter(today, endDate)) {
      return { status: "expired", daysLeft };
    } else if (isAfter(thirtyDaysFromNow, endDate)) {
      return { status: "expiring_soon", daysLeft };
    }
    return { status: "active", daysLeft };
  }

  // Получение пользователя по ID
  async getUser(id: number): Promise<User | undefined> {
    try {
      const result = await db.select().from(users).where(eq(users.id, id)).limit(1);
      return result.length > 0 ? result[0] : undefined;
    } catch (error) {
      console.error("Ошибка при получении пользователя по ID:", error);
      throw error;
    }
  }

  // Получение пользователя по имени пользователя
  async getUserByUsername(username: string): Promise<User | undefined> {
    try {
      const result = await db.select().from(users).where(eq(users.username, username)).limit(1);
      return result.length > 0 ? result[0] : undefined;
    } catch (error) {
      console.error("Ошибка при получении пользователя по имени:", error);
      throw error;
    }
  }

  // Создание нового пользователя
  async createUser(insertUser: InsertUser): Promise<User> {
    try {
      // Проверяем, существует ли пользователь с таким именем
      const existingUser = await this.getUserByUsername(insertUser.username);
      if (existingUser) {
        throw new Error("Пользователь с таким именем уже существует");
      }

      // Создаем пользователя с ролью по умолчанию "lawyer", если роль не указана
      const user = {
        ...insertUser,
        role: insertUser.role || "lawyer"
      };

      const result = await db.insert(users).values(user).returning();
      return result[0];
    } catch (error) {
      console.error("Ошибка при создании пользователя:", error);
      throw error;
    }
  }

  // Получение всех пользователей
  async getAllUsers(): Promise<User[]> {
    try {
      return await db.select().from(users);
    } catch (error) {
      console.error("Ошибка при получении списка пользователей:", error);
      throw error;
    }
  }

  // Обновление пароля пользователя
  async updateUserPassword(id: number, hashedPassword: string): Promise<void> {
    try {
      await db.update(users)
        .set({ password: hashedPassword })
        .where(eq(users.id, id));
    } catch (error) {
      console.error("Ошибка при обновлении пароля пользователя:", error);
      throw error;
    }
  }

  // Получение всех контрактов с расчетом статуса
  async getContracts(): Promise<Contract[]> {
    try {
      const allContracts = await db.select().from(contracts);
      
      // Рассчитываем статус и количество дней для каждого контракта
      return allContracts.map(contract => {
        const { status, daysLeft } = this.calculateContractStatus(new Date(contract.endDate));
        return {
          ...contract,
          status,
          daysLeft
        };
      });
    } catch (error) {
      console.error("Ошибка при получении контрактов:", error);
      throw error;
    }
  }

  // Получение контракта по ID
  async getContract(id: number): Promise<Contract | undefined> {
    try {
      const result = await db.select().from(contracts).where(eq(contracts.id, id)).limit(1);
      
      if (result.length === 0) {
        return undefined;
      }
      
      const contract = result[0];
      const { status, daysLeft } = this.calculateContractStatus(new Date(contract.endDate));
      
      return {
        ...contract,
        status,
        daysLeft
      };
    } catch (error) {
      console.error("Ошибка при получении контракта по ID:", error);
      throw error;
    }
  }

  // Получение контракта по ИНН
  async getContractByInn(inn: string): Promise<Contract | undefined> {
    try {
      const result = await db.select().from(contracts).where(eq(contracts.inn, inn)).limit(1);
      
      if (result.length === 0) {
        return undefined;
      }
      
      const contract = result[0];
      const { status, daysLeft } = this.calculateContractStatus(new Date(contract.endDate));
      
      return {
        ...contract,
        status,
        daysLeft
      };
    } catch (error) {
      console.error("Ошибка при получении контракта по ИНН:", error);
      throw error;
    }
  }

  // Создание нового контракта
  async createContract(insertContract: InsertContract, userId: number): Promise<Contract> {
    try {
      // Проверяем, существует ли контракт с таким ИНН
      const existingContract = await this.getContractByInn(insertContract.inn);
      if (existingContract) {
        throw new Error("Контракт с таким ИНН уже существует");
      }

      // Получаем имя пользователя для истории
      const user = await this.getUser(userId);
      if (!user) {
        throw new Error("Пользователь не найден");
      }

      const now = new Date();
      
      // Создаем запись в истории
      const historyEntry: ContractHistoryEntry = {
        userId,
        username: user.username,
        action: "created",
        changes: {},
        timestamp: now.toISOString()
      };

      // Создаем новый контракт
      const newContract = {
        ...insertContract,
        status: this.calculateContractStatus(new Date(insertContract.endDate)).status,
        createdAt: now,
        history: JSON.stringify([historyEntry])
      };

      const result = await db.insert(contracts).values(newContract).returning();
      const createdContract = result[0];
      
      // Добавляем расчетное поле daysLeft
      const { daysLeft } = this.calculateContractStatus(new Date(createdContract.endDate));
      
      return {
        ...createdContract,
        daysLeft
      };
    } catch (error) {
      console.error("Ошибка при создании контракта:", error);
      throw error;
    }
  }

  // Обновление контракта
  async updateContract(
    id: number,
    updates: Partial<InsertContract>,
    userId: number
  ): Promise<Contract> {
    try {
      // Получаем текущий контракт
      const existing = await this.getContract(id);
      if (!existing) {
        throw new Error("Контракт не найден");
      }

      // Получаем пользователя для истории
      const user = await this.getUser(userId);
      if (!user) {
        throw new Error("Пользователь не найден");
      }

      // Формируем список изменений для истории
      const changes: Record<string, { old: any; new: any }> = {};
      Object.entries(updates).forEach(([key, value]) => {
        if (existing[key as keyof Contract] !== value) {
          changes[key] = {
            old: existing[key as keyof Contract],
            new: value
          };
        }
      });

      // Создаем запись в истории
      const historyEntry: ContractHistoryEntry = {
        userId,
        username: user.username,
        action: "updated",
        changes,
        timestamp: new Date().toISOString()
      };

      // Получаем текущую историю и добавляем новую запись
      let history = existing.history || [];
      history = [...history, historyEntry];

      // Обновляем контракт
      const result = await db.update(contracts)
        .set({
          ...updates,
          history: JSON.stringify(history)
        })
        .where(eq(contracts.id, id))
        .returning();

      const updatedContract = result[0];
      
      // Рассчитываем статус и дни
      const { status, daysLeft } = this.calculateContractStatus(new Date(updatedContract.endDate));
      
      return {
        ...updatedContract,
        status,
        daysLeft
      };
    } catch (error) {
      console.error("Ошибка при обновлении контракта:", error);
      throw error;
    }
  }

  // Удаление контракта
  async deleteContract(id: number): Promise<void> {
    try {
      await db.delete(contracts).where(eq(contracts.id, id));
    } catch (error) {
      console.error("Ошибка при удалении контракта:", error);
      throw error;
    }
  }

  // Инициализация хранилища
  async initialize(): Promise<void> {
    // PostgreSQL уже инициализирован в db.ts
    return;
  }
}