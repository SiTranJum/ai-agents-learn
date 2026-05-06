// useProfile - TanStack Query 封装
// 参考: docs/specs/frontend/modules/15-profile-module.md §6

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { profileService } from '../services/profileService';
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
    onSuccess: (data) => {
      qc.setQueryData(['profile'], data);
      qc.invalidateQueries({ queryKey: ['home'] });
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
