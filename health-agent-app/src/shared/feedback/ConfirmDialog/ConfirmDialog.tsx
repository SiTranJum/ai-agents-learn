import React from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { colors, radius, spacing, typography, shadows } from '@app/styles/tokens';

interface ConfirmDialogProps {
  visible: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  variant?: 'default' | 'danger';
}

/**
 * 确认对话框组件
 * 用于需要用户确认的操作（如删除、退出等）
 *
 * Props:
 * - visible: 是否显示对话框
 * - title: 标题
 * - message: 提示信息
 * - confirmText: 确认按钮文字（默认"确认"）
 * - cancelText: 取消按钮文字（默认"取消"）
 * - onConfirm: 确认回调
 * - onCancel: 取消回调
 * - variant: 样式变体，'default' 或 'danger'（危险操作用红色）
 */
export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  visible,
  title,
  message,
  confirmText = '确认',
  cancelText = '取消',
  onConfirm,
  onCancel,
  variant = 'default',
}) => {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onCancel}
    >
      <TouchableOpacity
        style={styles.overlay}
        activeOpacity={1}
        onPress={onCancel}
      >
        <TouchableOpacity
          activeOpacity={1}
          onPress={(e) => e.stopPropagation()}
        >
          <View style={styles.dialog}>
            <Text style={styles.title}>{title}</Text>
            <Text style={styles.message}>{message}</Text>
            <View style={styles.buttonRow}>
              <TouchableOpacity
                style={[styles.button, styles.cancelButton]}
                onPress={onCancel}
              >
                <Text style={styles.cancelText}>{cancelText}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.button,
                  styles.confirmButton,
                  variant === 'danger' && styles.dangerButton,
                ]}
                onPress={onConfirm}
              >
                <Text style={styles.confirmText}>{confirmText}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </TouchableOpacity>
      </TouchableOpacity>
    </Modal>
  );
};

const { width: screenWidth } = Dimensions.get('window');

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: colors.overlay,
    justifyContent: 'center',
    alignItems: 'center',
  },
  dialog: {
    width: screenWidth * 0.8, // 屏宽 80%
    backgroundColor: colors.bgCard,
    borderRadius: radius.lg, // 16px
    padding: 20, // 20px 内边距
    ...shadows.modal,
  },
  title: {
    fontSize: typography.cardTitle.fontSize,
    fontWeight: typography.cardTitle.fontWeight,
    color: colors.textPrimary,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  message: {
    fontSize: typography.body.fontSize,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.xl,
    lineHeight: 22,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  button: {
    flex: 1,
    height: 44, // 44px 高
    borderRadius: radius.md, // 12px 圆角
    justifyContent: 'center',
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: colors.inputBg,
  },
  confirmButton: {
    backgroundColor: colors.primary,
  },
  dangerButton: {
    backgroundColor: colors.error,
  },
  cancelText: {
    fontSize: typography.body.fontSize,
    fontWeight: '500',
    color: colors.textSecondary,
  },
  confirmText: {
    fontSize: typography.body.fontSize,
    fontWeight: '500',
    color: '#FFFFFF',
  },
});
