import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { theme } from '@app/styles/theme';

export interface AIInputBarProps {
  onSend: (message: string) => void;
  onCamera?: () => void;
  onVoice?: () => void;
  placeholder?: string;
}

export function AIInputBar({
  onSend,
  onCamera,
  onVoice,
  placeholder = '说点什么...',
}: AIInputBarProps) {
  const [text, setText] = useState('');

  const handleSend = () => {
    if (text.trim()) {
      onSend(text.trim());
      setText('');
    }
  };

  return (
    <View style={styles.container}>
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
      <View style={styles.inputWrapper}>
        <TextInput
          style={styles.input}
          value={text}
          onChangeText={setText}
          placeholder={placeholder}
          placeholderTextColor={theme.colors.textTertiary}
          returnKeyType="send"
          onSubmitEditing={handleSend}
        />
      </View>
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
