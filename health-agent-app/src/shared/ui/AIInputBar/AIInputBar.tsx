import React, { useState, useEffect } from 'react';
import { View, TextInput, TouchableOpacity, StyleSheet, Keyboard, Platform, Text, Animated } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { theme } from '@app/styles/theme';

export interface AIInputBarProps {
  onSend: (message: string) => void;
  onCamera?: () => void;
  onVoice?: () => void;
  /** 输入框区域被点击时触发（包括首次获焦和后续点击） */
  onInputPress?: () => void;
  /** 展开全屏按钮点击回调 */
  onExpandPress?: () => void;
  /** 未读消息数（显示在展开按钮上） */
  unreadCount?: number;
  placeholder?: string;
}

export function AIInputBar({
  onSend,
  onCamera,
  onVoice,
  onInputPress,
  onExpandPress,
  unreadCount = 0,
  placeholder = '说点什么...',
}: AIInputBarProps) {
  const [text, setText] = useState('');
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  const pulseAnim = React.useRef(new Animated.Value(1)).current;

  // 监听键盘事件，获取键盘高度
  useEffect(() => {
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';

    const showListener = Keyboard.addListener(showEvent, (e) => {
      setKeyboardHeight(e.endCoordinates.height);
    });

    const hideListener = Keyboard.addListener(hideEvent, () => {
      setKeyboardHeight(0);
    });

    return () => {
      showListener.remove();
      hideListener.remove();
    };
  }, []);

  // 未读数字脉冲动画
  useEffect(() => {
    if (unreadCount > 0) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.2,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();
      return () => pulse.stop();
    }
  }, [unreadCount, pulseAnim]);

  const handleSend = () => {
    if (text.trim()) {
      onSend(text.trim());
      setText('');
    }
  };

  return (
    <View style={[styles.container, { marginBottom: Math.max(0, keyboardHeight - 60) }]}>
      {/* 常驻展开按钮 */}
      {onExpandPress && (
        <TouchableOpacity style={styles.expandBtn} onPress={onExpandPress}>
          <Feather name="message-circle" size={22} color={theme.colors.primary} />
          {unreadCount > 0 && (
            <Animated.View
              style={[
                styles.badge,
                {
                  transform: [{ scale: pulseAnim }],
                },
              ]}
            >
              <Text style={styles.badgeText}>{unreadCount > 99 ? '99+' : unreadCount}</Text>
            </Animated.View>
          )}
        </TouchableOpacity>
      )}

      <View style={styles.inputWrapper}>
        <TextInput
          style={styles.input}
          value={text}
          onChangeText={setText}
          placeholder={placeholder}
          placeholderTextColor={theme.colors.textTertiary}
          returnKeyType="send"
          onSubmitEditing={handleSend}
          onPressIn={onInputPress}
        />
      </View>

      {onCamera && (
        <TouchableOpacity style={styles.iconBtn} onPress={onCamera}>
          <Feather name="camera" size={20} color={theme.colors.textTertiary} />
        </TouchableOpacity>
      )}
      {onVoice && (
        <TouchableOpacity style={styles.iconBtn} onPress={onVoice}>
          <Feather name="mic" size={20} color={theme.colors.textTertiary} />
        </TouchableOpacity>
      )}

      <TouchableOpacity
        style={[styles.sendBtn, text.trim() ? styles.sendBtnActive : null]}
        onPress={handleSend}
        disabled={!text.trim()}
      >
        <Feather
          name="send"
          size={18}
          color={text.trim() ? '#FFFFFF' : theme.colors.textTertiary}
        />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    backgroundColor: theme.colors.bgCard,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: theme.colors.divider,
  },
  expandBtn: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 4,
  },
  badge: {
    position: 'absolute',
    top: 2,
    right: 2,
    minWidth: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: '#FF4444',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  iconBtn: {
    width: 36,
    height: 36,
    justifyContent: 'center',
    alignItems: 'center',
  },
  inputWrapper: {
    flex: 1,
    height: 40,
    backgroundColor: theme.colors.inputBg,
    borderRadius: theme.radius.pill,
    justifyContent: 'center',
    paddingHorizontal: 14,
    marginHorizontal: 8,
  },
  input: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    padding: 0,
  },
  sendBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: theme.colors.divider,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendBtnActive: {
    backgroundColor: theme.colors.primary,
  },
});
