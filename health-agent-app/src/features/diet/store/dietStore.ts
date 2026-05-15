// Diet Store - Zustand
// 参考: docs/specs/frontend/modules/12-diet-module.md §6

import { create } from 'zustand';
import type { FoodItem, MealType } from '../types/diet.types';

/** AI 解析后尚未确认的饮食记录 */
export interface PendingDietRecord {
  date: string;
  mealType: MealType;
  foods: FoodItem[];
  sessionId?: string;
  createdAt: number; // timestamp，用于超时清理
}

interface DietStore {
  /** 当前选中的日期（YYYY-MM-DD） */
  selectedDate: string;
  setSelectedDate: (date: string) => void;

  /** AI 解析后待确认的记录，key = `${date}_${mealType}` */
  pendingRecords: Record<string, PendingDietRecord>;
  setPending: (record: PendingDietRecord) => void;
  clearPending: (date: string, mealType: MealType) => void;
  clearAllPending: () => void;
  getPending: (date: string, mealType: MealType) => PendingDietRecord | undefined;
}

const today = (): string => {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
};

function pendingKey(date: string, mealType: MealType): string {
  return `${date}_${mealType}`;
}

export const useDietStore = create<DietStore>((set, get) => ({
  selectedDate: today(),
  setSelectedDate: (date) => set({ selectedDate: date }),

  pendingRecords: {},

  setPending: (record) =>
    set((state) => ({
      pendingRecords: {
        ...state.pendingRecords,
        [pendingKey(record.date, record.mealType)]: record,
      },
    })),

  clearPending: (date, mealType) =>
    set((state) => {
      const next = { ...state.pendingRecords };
      delete next[pendingKey(date, mealType)];
      return { pendingRecords: next };
    }),

  clearAllPending: () => set({ pendingRecords: {} }),

  getPending: (date, mealType) =>
    get().pendingRecords[pendingKey(date, mealType)],
}));
