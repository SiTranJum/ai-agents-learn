import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  ScrollView,
  StyleSheet,
} from 'react-native';
import { format } from 'date-fns';
import { colors, radius, spacing, typography } from '@app/styles/tokens';

export interface DatePickerProps {
  label?: string;
  value?: Date;
  onChange: (date: Date) => void;
  placeholder?: string;
  error?: string;
  minYear?: number;
  maxYear?: number;
}

export function DatePicker({
  label,
  value,
  onChange,
  placeholder = '请选择日期',
  error,
  minYear = 1900,
  maxYear = new Date().getFullYear(),
}: DatePickerProps) {
  const [modalVisible, setModalVisible] = React.useState(false);

  // 当前选中的年月日（用于模态框内的临时状态）
  const [selectedYear, setSelectedYear] = React.useState(
    value ? value.getFullYear() : new Date().getFullYear()
  );
  const [selectedMonth, setSelectedMonth] = React.useState(
    value ? value.getMonth() + 1 : 1
  );
  const [selectedDay, setSelectedDay] = React.useState(
    value ? value.getDate() : 1
  );

  // 生成年份选项
  const years: number[] = [];
  for (let y = maxYear; y >= minYear; y--) {
    years.push(y);
  }

  // 生成月份选项
  const months = Array.from({ length: 12 }, (_, i) => i + 1);

  // 根据选中的年月，计算该月有多少天
  const getDaysInMonth = (year: number, month: number) => {
    return new Date(year, month, 0).getDate();
  };

  const days = Array.from(
    { length: getDaysInMonth(selectedYear, selectedMonth) },
    (_, i) => i + 1
  );

  const displayValue = value ? format(value, 'yyyy-MM-dd') : '';

  const handleOpen = () => {
    if (value) {
      setSelectedYear(value.getFullYear());
      setSelectedMonth(value.getMonth() + 1);
      setSelectedDay(value.getDate());
    }
    setModalVisible(true);
  };

  const handleConfirm = () => {
    const date = new Date(selectedYear, selectedMonth - 1, selectedDay);
    onChange(date);
    setModalVisible(false);
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
              <Text style={styles.modalTitle}>{label || '选择日期'}</Text>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Text style={styles.closeButton}>✕</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.pickerRow}>
              {/* 年份选择 */}
              <View style={styles.pickerColumn}>
                <Text style={styles.columnLabel}>年</Text>
                <ScrollView style={styles.columnScroll}>
                  {years.map((year) => (
                    <TouchableOpacity
                      key={year}
                      style={[
                        styles.pickerItem,
                        year === selectedYear && styles.selectedItem,
                      ]}
                      onPress={() => setSelectedYear(year)}
                    >
                      <Text
                        style={[
                          styles.pickerText,
                          year === selectedYear && styles.selectedText,
                        ]}
                      >
                        {year}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>

              {/* 月份选择 */}
              <View style={styles.pickerColumn}>
                <Text style={styles.columnLabel}>月</Text>
                <ScrollView style={styles.columnScroll}>
                  {months.map((month) => (
                    <TouchableOpacity
                      key={month}
                      style={[
                        styles.pickerItem,
                        month === selectedMonth && styles.selectedItem,
                      ]}
                      onPress={() => setSelectedMonth(month)}
                    >
                      <Text
                        style={[
                          styles.pickerText,
                          month === selectedMonth && styles.selectedText,
                        ]}
                      >
                        {month}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>

              {/* 日期选择 */}
              <View style={styles.pickerColumn}>
                <Text style={styles.columnLabel}>日</Text>
                <ScrollView style={styles.columnScroll}>
                  {days.map((day) => (
                    <TouchableOpacity
                      key={day}
                      style={[
                        styles.pickerItem,
                        day === selectedDay && styles.selectedItem,
                      ]}
                      onPress={() => setSelectedDay(day)}
                    >
                      <Text
                        style={[
                          styles.pickerText,
                          day === selectedDay && styles.selectedText,
                        ]}
                      >
                        {day}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>
            </View>

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
  pickerRow: {
    flexDirection: 'row',
    height: 250,
    paddingVertical: spacing.md,
  },
  pickerColumn: {
    flex: 1,
    borderRightWidth: 1,
    borderRightColor: colors.divider,
  },
  columnLabel: {
    ...typography.bodySm,
    color: colors.textSecondary,
    textAlign: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  columnScroll: {
    flex: 1,
  },
  pickerItem: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.sm,
    alignItems: 'center',
  },
  selectedItem: {
    backgroundColor: colors.primaryLight,
  },
  pickerText: {
    ...typography.body,
    color: colors.textPrimary,
  },
  selectedText: {
    color: colors.primary,
    fontWeight: '600',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: spacing.md,
    padding: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.divider,
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
