import React, { createContext, useContext, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
} from 'react-native';
import { colors, radius, spacing, typography, animation } from '@app/styles/tokens';

type ToastType = 'success' | 'error' | 'info';

interface ToastConfig {
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastContextValue {
  show: (config: ToastConfig) => void;
}

// 创建 Context
const ToastContext = createContext<ToastContextValue | null>(null);

/**
 * Toast Provider 组件
 * 提供全局 Toast 功能，需要包裹在应用根组件外层
 *
 * 使用方式：
 * 1. 在 App.tsx 中用 ToastProvider 包裹根组件
 * 2. 在任意组件中调用：const toast = useToast(); toast.show({ type: 'success', message: '保存成功' });
 */
export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [visible, setVisible] = useState(false);
  const [config, setConfig] = useState<ToastConfig>({ type: 'info', message: '' });
  const translateY = useRef(new Animated.Value(-100)).current; // 初始位置在顶部外
  const opacity = useRef(new Animated.Value(0)).current;
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const show = (newConfig: ToastConfig) => {
    // 如果已有 Toast 显示，先清除定时器
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    setConfig(newConfig);
    setVisible(true);

    // 动画：从顶部下滑 + 淡入
    Animated.parallel([
      Animated.timing(translateY, {
        toValue: 0,
        duration: animation.toastShow,
        useNativeDriver: true,
      }),
      Animated.timing(opacity, {
        toValue: 1,
        duration: animation.toastShow,
        useNativeDriver: true,
      }),
    ]).start();

    // 自动隐藏
    const duration = newConfig.duration ?? 2000;
    timeoutRef.current = setTimeout(() => {
      hide();
    }, duration);
  };

  const hide = () => {
    Animated.parallel([
      Animated.timing(translateY, {
        toValue: -100,
        duration: animation.toastHide,
        useNativeDriver: true,
      }),
      Animated.timing(opacity, {
        toValue: 0,
        duration: animation.toastHide,
        useNativeDriver: true,
      }),
    ]).start(() => {
      setVisible(false);
    });
  };

  // 根据类型获取背景色
  const getBackgroundColor = (type: ToastType): string => {
    switch (type) {
      case 'success':
        return colors.success;
      case 'error':
        return colors.error;
      case 'info':
        return colors.info;
    }
  };

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      {visible && (
        <Animated.View
          style={[
            styles.container,
            {
              backgroundColor: getBackgroundColor(config.type),
              transform: [{ translateY }],
              opacity,
            },
          ]}
        >
          <Text style={styles.message}>{config.message}</Text>
        </Animated.View>
      )}
    </ToastContext.Provider>
  );
};

/**
 * useToast Hook
 * 在组件中获取 Toast 实例，调用 show 方法显示 Toast
 */
export const useToast = (): ToastContextValue => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

const { width: screenWidth } = Dimensions.get('window');

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 60, // 状态栏下方
    left: spacing.lg,
    right: spacing.lg,
    minHeight: 44,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999,
    elevation: 9999,
  },
  message: {
    color: '#FFFFFF',
    fontSize: typography.body.fontSize,
    fontWeight: '500',
    textAlign: 'center',
  },
});
