// Body Pending Store - Zustand
// AI 解析身体数据（饮水/睡眠/运动/排便）后尚未确认的记录。
// 与 dietStore.pendingRecords 对称，但字段按身体数据类型组织。
// 首页辅助卡片读取此 store 显示「待确认」态（确认/取消）。

import { create } from 'zustand';

export type BodyRecordKind = 'water' | 'sleep' | 'exercise' | 'bowel';

/** AI 解析后待确认的身体数据记录 */
export interface PendingBodyRecord {
  date: string;
  recordType: BodyRecordKind;
  /** 写入语义：仅 water 用 append（累加）；其余恒 replace */
  operation?: 'append' | 'replace';
  /** 来源 AI 卡片的唯一 id，用于首页确认/取消后同步聊天卡片状态 */
  cardId?: string;
  sessionId?: string;
  createdAt: number;

  // ===== 各类型字段（按 recordType 填充）=====
  // water
  waterAmount?: number;
  // sleep
  sleepBedTime?: string;
  sleepWakeTime?: string;
  sleepQuality?: 'excellent' | 'good' | 'fair' | 'poor';
  // exercise
  exerciseType?: string;
  exerciseDuration?: number;
  // bowel
  bowelTime?: string;
  bowelStatus?: 'normal' | 'constipation' | 'diarrhea';
}

interface BodyPendingStore {
  /** key = `${date}_${recordType}` */
  pendingRecords: Record<string, PendingBodyRecord>;
  setPending: (record: PendingBodyRecord) => void;
  clearPending: (date: string, recordType: BodyRecordKind) => void;
  clearAllPending: () => void;
  getPending: (date: string, recordType: BodyRecordKind) => PendingBodyRecord | undefined;
}

function pendingKey(date: string, recordType: BodyRecordKind): string {
  return `${date}_${recordType}`;
}

export const useBodyPendingStore = create<BodyPendingStore>((set, get) => ({
  pendingRecords: {},

  setPending: (record) =>
    set((state) => ({
      pendingRecords: {
        ...state.pendingRecords,
        [pendingKey(record.date, record.recordType)]: record,
      },
    })),

  clearPending: (date, recordType) =>
    set((state) => {
      const next = { ...state.pendingRecords };
      delete next[pendingKey(date, recordType)];
      return { pendingRecords: next };
    }),

  clearAllPending: () => set({ pendingRecords: {} }),

  getPending: (date, recordType) =>
    get().pendingRecords[pendingKey(date, recordType)],
}));
