import React, { useEffect, useRef } from 'react';
import {
  Modal,
  View,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Dimensions,
} from 'react-native';
import { colors, radius, spacing, shadows, animation } from '@app/styles/tokens';

interface BottomSheetProps {
  visible: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

/**
 * 底部弹出面板组件
 * 使用 React Native 内置 Modal + Animated 实现从底部滑入效果
 * 不依赖 @gorhom/bottom-sheet，避免原生依赖问题
 *
 * Props:
 * - visible: 是否显示面板
 * - onClose: 关闭回调
 * - children: 面板内容
 */
export const BottomSheet: React.FC<BottomSheetProps> = ({
  visible,
  onClose,
  children,
}) => {
  const { height: screenHeight } = Dimensions.get('window');
  const translateY = useRef(new Animated.Value(screenHeight)).current;

  useEffect(() => {
    if (visible) {
      // 从底部滑入
      Animated.timing(translateY, {
        toValue: 0,
        duration: animation.modalShow,
        useNativeDriver: true,
      }).start();
    } else {
      // 滑出到底部
      Animated.timing(translateY, {
        toValue: screenHeight,
        duration: animation.toastHide,
        useNativeDriver: true,
      }).start();
    }
  }, [visible]);

  return (
    <Modal
      visible={visible}
      transparent
      animationType="none" // 动画由 Animated 控制
      onRequestClose={onClose}
    >
      {/* 遮罩层 */}
      <TouchableOpacity
        style={styles.overlay}
        activeOpacity={1}
        onPress={onClose}
      />
      {/* 内容区 */}
      <Animated.View
        style={[
          styles.container,
          { transform: [{ translateY }] },
        ]}
      >
        {/* 拖拽条 */}
        <View style={styles.handleBar} />
        {/* 内容 */}
        <View style={styles.content}>{children}</View>
      </Animated.View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: colors.overlay,
  },
  container: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: colors.bgCard,
    borderTopLeftRadius: radius.lg, // 16px
    borderTopRightRadius: radius.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.xl,
    ...shadows.modal,
  },
  handleBar: {
    width: 36,
    height: 4,
    backgroundColor: '#D9D9D9', // 浅灰拖拽条
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: spacing.md,
  },
  content: {
    paddingHorizontal: spacing.lg, // 16px 内边距
  },
});
