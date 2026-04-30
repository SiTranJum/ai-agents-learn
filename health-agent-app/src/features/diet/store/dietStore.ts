// Diet Store - Zustand
// 参考: docs/specs/frontend/modules/12-diet-module.md §6

import { create } from 'zustand';

interface DietStore {
  /** 当前选中的日期（YYYY-MM-DD） */
  selectedDate: string;
  setSelectedDate: (date: string) => void;
}

const today = (): string => {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
};

export const useDietStore = create<DietStore>((set) => ({
  selectedDate: today(),
  setSelectedDate: (date) => set({ selectedDate: date }),
}));
