// Home Service - Mock 实现
// 参考: docs/specs/frontend/modules/11-home-module.md §7

import type { HomeData } from '../types/home.types';
import { dataHomeMock } from '../mocks/homeMocks';

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export interface HomeService {
  /**
   * 获取首页聚合数据
   * @param date - YYYY-MM-DD
   */
  getHomeData(date: string): Promise<HomeData>;
}

export const homeService: HomeService = {
  async getHomeData(date) {
    await delay(500);
    // Mock-First：默认返回有数据态，便于演示。
    // 若需切换为 emptyHomeMock / pendingHomeMock，可在此根据 date 或全局开关返回不同 mock。
    return { ...dataHomeMock, date };
  },
};
