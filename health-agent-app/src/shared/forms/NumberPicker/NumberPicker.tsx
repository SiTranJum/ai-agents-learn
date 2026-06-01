import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  ScrollView,
  StyleSheet,
} from 'react-native';
import { colors, radius, spacing, typography } from '@app/styles/tokens';

export interface NumberPickerProps {
  label?: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  unit?: string;
  placeholder?: string;
  error?: string;
}

export function NumberPicker({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  unit = '',
  placeholder = '请选择',
  error,
}: NumberPickerProps) {
  const [modalVisible, setModalVisible] = React.useState(false);

  // 生成选项列表
  const options: number[] = [];
  for (let i = min; i <= max; i += step) {
    options.push(i);
  }

  const displayText = value ? `${value} ${unit}` : placeholder;

  const handleSelect = (selectedValue: number) => {
    onChange(selectedValue);
    setModalVisible(false);
  };

  return (
    <View style={styles.container}>
      {label && <Text style={styles.label}>{label}</Text>}
      <TouchableOpacity
        style={[styles.inputBox, error ? styles.errorBorder : null]}
        onPress={() => setModalVisible(true)}
        activeOpacity={0.7}
      >
        <Text style={[styles.inputText, !value && styles.placeholder]}>
          {displayText}
        </Text>
      </TouchableOpacity>
      {error && <Text style={styles.errorText}>{error}</Text>}

      <Modal
        visible={modalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setModalVisible(false)}
      >
        <TouchableOpacity
          style={styles.overlay}
          activeOpacity={1}
          onPress={() => setModalVisible(false)}
        >
          <View style={styles.modalContent} onStartShouldSetResponder={() => true}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{label || '请选择'}</Text>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Text style={styles.closeButton}>✕</Text>
              </TouchableOpacity>
            </View>
            <ScrollView style={styles.optionList}>
              {options.map((option) => (
                <TouchableOpacity
                  key={option}
                  style={[
                    styles.optionItem,
                    option === value && styles.selectedOption,
                  ]}
                  onPress={() => handleSelect(option)}
                >
                  <Text
                    style={[
                      styles.optionText,
                      option === value && styles.selectedText,
                    ]}
                  >
                    {option} {unit}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing.lg,
  },
  label: {
    ...typography.bodySm,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  inputBox: {
    height: 48,
    backgroundColor: colors.inputBg,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: 'transparent',
  },
  inputText: {
    fontSize: typography.body.fontSize,
    color: colors.textPrimary,
  },
  placeholder: {
    color: colors.textTertiary,
  },
  errorBorder: {
    borderColor: colors.error,
  },
  errorText: {
    ...typography.caption,
    color: colors.error,
    marginTop: spacing.xs,
  },
  overlay: {
    flex: 1,
    backgroundColor: colors.overlay,
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: colors.bgCard,
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    maxHeight: '70%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  modalTitle: {
    ...typography.cardTitle,
    color: colors.textPrimary,
  },
  closeButton: {
    fontSize: 24,
    color: colors.textSecondary,
  },
  optionList: {
    maxHeight: 400,
  },
  optionItem: {
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  selectedOption: {
    backgroundColor: colors.primaryLight,
  },
  optionText: {
    ...typography.body,
    color: colors.textPrimary,
  },
  selectedText: {
    color: colors.primary,
    fontWeight: '600',
  },
});

