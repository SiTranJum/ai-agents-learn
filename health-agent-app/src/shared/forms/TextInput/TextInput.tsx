import React from 'react';
import {
  View,
  TextInput as RNTextInput,
  Text,
  StyleSheet,
  TextInputProps as RNTextInputProps,
} from 'react-native';
import { colors, radius, spacing, typography } from '@app/styles/tokens';

export interface TextInputProps {
  label?: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  error?: string;
  keyboardType?: RNTextInputProps['keyboardType'];
  multiline?: boolean;
  maxLength?: number;
}

export function TextInput({
  label,
  value,
  onChangeText,
  placeholder,
  error,
  keyboardType,
  multiline = false,
  maxLength,
}: TextInputProps) {
  const [isFocused, setIsFocused] = React.useState(false);

  return (
    <View style={styles.container}>
      {label && <Text style={styles.label}>{label}</Text>}
      <RNTextInput
        style={[
          styles.input,
          multiline && styles.multiline,
          isFocused && styles.focused,
          error ? styles.errorBorder : null,
        ]}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={colors.textTertiary}
        keyboardType={keyboardType}
        multiline={multiline}
        maxLength={maxLength}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
      />
      {error && <Text style={styles.errorText}>{error}</Text>}
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
  input: {
    height: 48,
    backgroundColor: colors.inputBg,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    fontSize: typography.body.fontSize,
    color: colors.textPrimary,
    borderWidth: 1.5,
    borderColor: 'transparent',
  },
  multiline: {
    height: 120,
    paddingTop: spacing.md,
    textAlignVertical: 'top',
  },
  focused: {
    borderColor: colors.primary,
  },
  errorBorder: {
    borderColor: colors.error,
  },
  errorText: {
    ...typography.caption,
    color: colors.error,
    marginTop: spacing.xs,
  },
});
