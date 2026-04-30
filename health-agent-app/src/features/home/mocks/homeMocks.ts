// 首页 Mock 数据
// 参考: docs/specs/frontend/modules/11-home-module.md §4 Mock 数据要求

import type { HomeData } from '../types/home.types';

export const emptyHomeMock: HomeData = {
  date: '2026-04-29',
  calories: { current: 0, target: 1800 },
  nutrients: {
    carbs: { current: 0, target: 225 },
    protein: { current: 0, target: 90 },
    fat: { current: 0, target: 60 },
  },
  meals: [
    { type: 'breakfast', status: 'empty', foods: '', calories: 0 },
    { type: 'lunch', status: 'empty', foods: '', calories: 0 },
    { type: 'dinner', status: 'empty', foods: '', calories: 0 },
    { type: 'snack', status: 'empty', foods: '', calories: 0 },
  ],
  aiInsight: '欢迎使用健康管家！试试在下方输入框记录你的第一餐吧。',
  plan: null,
  auxiliary: {
    water: { current: 0, target: 2000 },
    sleep: null,
    exercise: null,
    bowel: null,
  },
};

export const dataHomeMock: HomeData = {
  date: '2026-04-29',
  calories: { current: 1250, target: 1800 },
  nutrients: {
    carbs: { current: 150, target: 225 },
    protein: { current: 55, target: 90 },
    fat: { current: 38, target: 60 },
  },
  meals: [
    { type: 'breakfast', status: 'recorded', foods: '全麦面包、牛奶、鸡蛋', calories: 380, time: '08:15' },
    { type: 'lunch', status: 'recorded', foods: '米饭、西兰花炒鸡胸、紫菜汤', calories: 550, time: '12:30' },
    { type: 'dinner', status: 'recorded', foods: '杂粮粥、凉拌黄瓜', calories: 320, time: '18:45' },
    { type: 'snack', status: 'empty', foods: '', calories: 0 },
  ],
  aiInsight: '今天蛋白质摄入偏低，晚餐建议加个鸡蛋或豆腐补充一下。',
  plan: {
    id: 'plan-001',
    name: '30 天减脂计划',
    progress: 43,
    completedTasks: 3,
    totalTasks: 7,
  },
  auxiliary: {
    water: { current: 1200, target: 2000 },
    sleep: { duration: '7h 30min' },
    exercise: { duration: '45min' },
    bowel: { status: '正常' },
  },
};

export const pendingHomeMock: HomeData = {
  ...dataHomeMock,
  meals: [
    { type: 'breakfast', status: 'recorded', foods: '全麦面包、牛奶、鸡蛋', calories: 380, time: '08:15' },
    { type: 'lunch', status: 'pending', foods: '牛肉面、卤蛋（AI 识别中）', calories: 620, time: '12:20' },
    { type: 'dinner', status: 'empty', foods: '', calories: 0 },
    { type: 'snack', status: 'empty', foods: '', calories: 0 },
  ],
};
