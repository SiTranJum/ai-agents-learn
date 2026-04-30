// Data Store - Zustand
// 仅保留 UI 层状态（Tab 选中、时间范围），数据走 TanStack Query
// 参考: docs/specs/frontend/modules/13-data-module.md §6

import { create } from 'zustand';
import type { DataTabType, TimeRange } from '../types/data.types';

interface DataStore {
  selectedTab: DataTabType;
  setSelectedTab: (tab: DataTabType) => void;

  selectedTimeRange: TimeRange;
  setSelectedTimeRange: (range: TimeRange) => void;
}

export const useDataStore = create<DataStore>((set) => ({
  selectedTab: 'weight',
  setSelectedTab: (tab) => set({ selectedTab: tab }),

  selectedTimeRange: '30d',
  setSelectedTimeRange: (range) => set({ selectedTimeRange: range }),
}));
