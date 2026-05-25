// 选项 chips + 自由输入兜底
// 横向 wrap 布局，已选高亮主题色，未选边框灰
// 当 allow_free_text=true 时，提供"自己输入"chip → 唤起输入框

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput } from 'react-native';
import { theme } from '@app/styles/theme';
import type { ChoicePrompt } from '../types';

interface Props {
  prompt: ChoicePrompt;
  /** 已选的 value（变灰显示）；未选时为 undefined */
  selectedValue?: string;
  /** 已输入的自由文本 */
  freeText?: string;
  /** 选中某个 option（chip） */
  onSelect: (value: string, label: string) => void;
  /** 提交自由输入 */
  onFreeText: (text: string) => void;
}

const FREE_TEXT_VALUE = '__free_text__';

export function ChoicePromptView({
  prompt,
  selectedValue,
  freeText,
  onSelect,
  onFreeText,
}: Props) {
  const [showInput, setShowInput] = useState(false);
  const [draft, setDraft] = useState('');
  const isAnswered = selectedValue !== undefined || freeText !== undefined;

  const handlePress = (value: string, label: string) => {
    if (isAnswered) return;
    if (value === FREE_TEXT_VALUE) {
      setShowInput(true);
      return;
    }
    onSelect(value, label);
  };

  const handleSubmit = () => {
    const text = draft.trim();
    if (!text) return;
    onFreeText(text);
    setShowInput(false);
  };

  return (
    <View style={styles.wrap}>
      {prompt.question && <Text style={styles.question}>{prompt.question}</Text>}
      <View style={styles.chipsRow}>
        {prompt.options.map((opt) => {
          const isSelected = selectedValue === opt.value;
          const isDisabled = isAnswered && !isSelected;
          return (
            <TouchableOpacity
              key={opt.value}
              style={[
                styles.chip,
                isSelected && styles.chipSelected,
                isDisabled && styles.chipDisabled,
              ]}
              onPress={() => handlePress(opt.value, opt.label)}
              disabled={isAnswered}
              activeOpacity={0.7}
            >
              {isSelected && <Text style={styles.checkmark}>✓ </Text>}
              <Text
                style={[
                  styles.chipLabel,
                  isSelected && styles.chipLabelSelected,
                  isDisabled && styles.chipLabelDisabled,
                ]}
              >
                {opt.label}
              </Text>
            </TouchableOpacity>
          );
        })}
        {prompt.allow_free_text && !isAnswered && (
          <TouchableOpacity
            style={styles.chip}
            onPress={() => handlePress(FREE_TEXT_VALUE, '自己输入')}
            activeOpacity={0.7}
          >
            <Text style={styles.chipLabel}>✎ 自己输入</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* 用户已用自由文本回答 → 显示文本 */}
      {freeText !== undefined && (
        <View style={styles.freeTextDisplay}>
          <Text style={styles.freeTextLabel}>你的回答: </Text>
          <Text style={styles.freeTextValue}>{freeText}</Text>
        </View>
      )}

      {/* 输入面板 */}
      {showInput && !isAnswered && (
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={draft}
            onChangeText={setDraft}
            placeholder="说说你的答案..."
            placeholderTextColor={theme.colors.textTertiary}
            autoFocus
            onSubmitEditing={handleSubmit}
            returnKeyType="send"
          />
          <TouchableOpacity
            style={[styles.sendBtn, !draft.trim() && styles.sendBtnDisabled]}
            onPress={handleSubmit}
            disabled={!draft.trim()}
          >
            <Text style={styles.sendBtnText}>发送</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    paddingVertical: theme.spacing.sm,
  },
  question: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.sm,
  },
  chipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.colors.divider,
    backgroundColor: theme.colors.bgCard,
  },
  chipSelected: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
  chipDisabled: {
    opacity: 0.5,
  },
  chipLabel: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
  },
  chipLabelSelected: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  chipLabelDisabled: {
    color: theme.colors.textTertiary,
  },
  checkmark: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  freeTextDisplay: {
    flexDirection: 'row',
    marginTop: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    backgroundColor: theme.colors.primaryLight,
    borderRadius: theme.radius.md,
  },
  freeTextLabel: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
  },
  freeTextValue: {
    ...theme.typography.caption,
    color: theme.colors.primary,
    fontWeight: '600',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: theme.spacing.sm,
    gap: theme.spacing.sm,
  },
  input: {
    flex: 1,
    ...theme.typography.bodySm,
    backgroundColor: theme.colors.inputBg,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.md,
    color: theme.colors.textPrimary,
  },
  sendBtn: {
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
    backgroundColor: theme.colors.primary,
    borderRadius: theme.radius.md,
  },
  sendBtnDisabled: {
    opacity: 0.4,
  },
  sendBtnText: {
    ...theme.typography.bodySm,
    color: '#FFFFFF',
    fontWeight: '600',
  },
});
