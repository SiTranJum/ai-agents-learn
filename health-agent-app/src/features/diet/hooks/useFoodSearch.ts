// useFoodSearch - 食物搜索 hook（带 200ms 防抖）
// 参考: docs/specs/frontend/modules/12-diet-module.md §6

import { useEffect, useState } from 'react';
import { foodService } from '../services/dietService';
import type { FoodCandidate } from '../types/diet.types';

export function useFoodSearch(keyword: string, minLength: number = 1) {
  const [results, setResults] = useState<FoodCandidate[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (keyword.trim().length < minLength) {
      setResults([]);
      return;
    }
    setIsLoading(true);
    const handle = setTimeout(async () => {
      try {
        const list = await foodService.searchFood(keyword);
        setResults(list);
      } finally {
        setIsLoading(false);
      }
    }, 200);
    return () => clearTimeout(handle);
  }, [keyword, minLength]);

  return { results, isLoading };
}
