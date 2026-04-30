import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  TextInput as RNTextInput,
  Modal,
  StyleSheet,
} from 'react-native';
import { format, parse, isValid } from 'date-fns';
import { colors, radius, spacing, typography } from '@app/styles/tokens';

export interface DatePickerProps {
  label?: string;
  value?: Date;
  onChange: (date: Date) => void;
  placeholder?: string;
  error?: string;
  mode?: 'date' | 'time' | 'datetime';
}

export function DatePicker({
  label,
  value,
  onChange,
  placeholder = '请选择日期',
  error,
  mode = 'date',
}: DatePickerProps) {
  const [modalVisible, setModalVisible] = React.useState(false);
  const [inputText, setInputText] = React.useState('');

  const getFormatPattern = () => {
    switch (mode) {
      case 'time':
        return 'HH:mm';
      case 'datetime':
        return 'yyyy-MM-dd HH:mm';
      default:
        return 'yyyy-MM-dd';
    }
  };

  const getPlaceholderHint = () => {
    switch (mode) {
      case 'time':
        return '格式: HH:mm (如 08:30)';
      case 'datetime':
        return '格式: yyyy-MM-dd HH:mm (如 2024-01-15 08:30)';
      default:
        return '格式: yyyy-MM-dd (如 1990-01-15)';
    }
  };

  const displayValue = value ? format(value, getFormatPattern()) : '';

  const handleOpen = () => {
    setInputText(displayValue);
    setModalVisible(true);
  };

  const handleConfirm = () => {
    const pattern = getFormatPattern();
    const parsed = parse(inputText, pattern, new Date());
    if (isValid(parsed)) {
      onChange(parsed);
      setModalVisible(false);
    }
  };

  return (
    <View style={styles.container}>
      {label && <Text style={styles.label}>{label}</Text>}
      <TouchableOpacity
        style={[styles.inputBox, error ? styles.errorBorder : null]}
        onPress={handleOpen}
        activeOpacity={0.7}
      >
        <Text style={[styles.inputText, !displayValue && styles.placeholder]}>
          {displayValue || placeholder}
        </Text>
      </TouchableOpacity>
      {error && <Text style={styles.errorText}>{error}</Text>}

      <Modal
        visible={modalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setModalVisible(false)}
      >
        <TouchableOpacity
          style={styles.overlay}
          activeOpacity={1}
          onPress={() => setModalVisible(false)}
        >
          <View style={styles.modalContent} onStartShouldSetResponder={() => true}>
            <Text style={styles.modalTitle}>输入{mode === 'time' ? '时间' : '日期'}</Text>
            <Text style={styles.hint}>{getPlaceholderHint()}</Text>
            <RNTextInput
              style={styles.modalInput}
              value={inputText}
              onChangeText={setInputText}
              placeholder={getFormatPattern()}
              placeholderTextColor={colors.textTertiary}
              autoFocus
            />
            <View style={styles.buttonRow}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setModalVisible(false)}
              >
                <Text style={styles.cancelText}>取消</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.confirmButton} onPress={handleConfirm}>
                <Text style={styles.confirmText}>确认</Text>
              </TouchableOpacity>
            </View>
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
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: colors.bgCard,
    borderRadius: radius.lg,
    padding: spacing.xl,
    width: '80%',
    maxWidth: 320,
  },
  modalTitle: {
    ...typography.cardTitle,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  hint: {
    ...typography.caption,
    color: colors.textTertiary,
    marginBottom: spacing.lg,
  },
  modalInput: {
    height: 48,
    backgroundColor: colors.inputBg,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    fontSize: typography.body.fontSize,
    color: colors.textPrimary,
    marginBottom: spacing.lg,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: spacing.md,
  },
  cancelButton: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
  },
  cancelText: {
    ...typography.bodySm,
    color: colors.textSecondary,
  },
  confirmButton: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    backgroundColor: colors.primary,
    borderRadius: radius.sm,
  },
  confirmText: {
    ...typography.bodySm,
    color: '#FFFFFF',
    fontWeight: '600',
  },
});
