import React from 'react';
import {
  Modal as RNModal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { colors, radius, spacing, typography, shadows } from '@app/styles/tokens';

interface ModalProps {
  visible: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
}

/**
 * 模态框组件
 * 封装 React Native 内置 Modal 组件
 * 用于展示需要用户关注的内容（如详情、表单等）
 *
 * Props:
 * - visible: 是否显示模态框
 * - onClose: 关闭回调函数
 * - children: 模态框内容
 * - title: 可选标题
 */
export const Modal: React.FC<ModalProps> = ({
  visible,
  onClose,
  children,
  title,
}) => {
  return (
    <RNModal
      visible={visible}
      transparent // 背景透明，显示遮罩
      animationType="fade" // 淡入淡出动画
      onRequestClose={onClose} // Android 返回键处理
    >
      {/* 遮罩层 */}
      <TouchableOpacity
        style={styles.overlay}
        activeOpacity={1}
        onPress={onClose}
      >
        {/* 内容区 */}
        <TouchableOpacity
          activeOpacity={1}
          onPress={(e) => e.stopPropagation()} // 阻止点击事件冒泡到遮罩层
        >
          <View style={styles.content}>
            {title && (
              <View style={styles.header}>
                <Text style={styles.title}>{title}</Text>
              </View>
            )}
            <View style={styles.body}>{children}</View>
          </View>
        </TouchableOpacity>
      </TouchableOpacity>
    </RNModal>
  );
};

const { width: screenWidth } = Dimensions.get('window');

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: colors.overlay, // rgba(0,0,0,0.4)
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    width: screenWidth - 48, // 左右各留 24px
    backgroundColor: colors.bgCard,
    borderRadius: radius.lg, // 16px
    ...shadows.modal,
  },
  header: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    paddingBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  title: {
    fontSize: typography.cardTitle.fontSize,
    fontWeight: typography.cardTitle.fontWeight,
    color: colors.textPrimary,
  },
  body: {
    padding: spacing.lg,
  },
});
