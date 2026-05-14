// useProfile - TanStack Query 封装
// 参考: docs/specs/frontend/modules/15-profile-module.md §6

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { profileService } from '../services/profileService';
import { useGlobalStore } from '@core/store/globalStore';
import type { AppSettings, UserProfile } from '../types/profile.types';

export function useUserProfile() {
  return useQuery({
    queryKey: ['profile'],
    queryFn: () => profileService.getUserProfile(),
  });
}

export function useUpdateUserProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<UserProfile>) =>
      profileService.updateUserProfile(data),
    onSuccess: (profile) => {
      qc.setQueryData(['profile'], profile);
      qc.invalidateQueries({ queryKey: ['home'] });
      // 同步到 globalStore
      useGlobalStore.getState().setUserProfile({
        id: profile.id,
        email: profile.email,
        nickname: profile.nickname,
        gender: profile.gender,
        birthDate: profile.birthDate,
        height: profile.height,
        weight: profile.weight,
        targetWeight: profile.targetWeight,
        activityLevel: profile.activityLevel,
        healthGoals: profile.goalType ? [profile.goalType] : [],
        dietPreferences: profile.dietType ? [profile.dietType] : [],
        allergies: profile.allergies,
        restrictions: profile.restrictions,
        diseases: profile.diseases,
        onboardingCompleted: true,
      });
    },
  });
}

export function useDeleteAccount() {
  return useMutation({
    mutationFn: () => profileService.deleteAccount(),
  });
}

export function useExportData() {
  return useMutation({
    mutationFn: () => profileService.exportData(),
  });
}

export function useAppSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: () => profileService.getAppSettings(),
  });
}

export function useUpdateAppSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<AppSettings>) =>
      profileService.updateAppSettings(data),
    onSuccess: (data) => {
      qc.setQueryData(['settings'], data);
    },
  });
}
