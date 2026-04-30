import React from 'react';
import {
  View,
  TextInput as RNTextInput,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { colors, radius, spacing, typography } from '@app/styles/tokens';

export interface PasswordInputProps {
  label?: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  error?: string;
}

export function PasswordInput({
  label,
  value,
  onChangeText,
  placeholder,
  error,
}: PasswordInputProps) {
  const [isFocused, setIsFocused] = React.useState(false);
  const [secureEntry, setSecureEntry] = React.useState(true);

  return (
    <View style={styles.container}>
      {label && <Text style={styles.label}>{label}</Text>}
      <View
        style={[
          styles.inputWrapper,
          isFocused && styles.focused,
          error ? styles.errorBorder : null,
        ]}
      >
        <RNTextInput
          style={styles.input}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={colors.textTertiary}
          secureTextEntry={secureEntry}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
        />
        <TouchableOpacity
          style={styles.eyeButton}
          onPress={() => setSecureEntry(!secureEntry)}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Feather
            name={secureEntry ? 'eye-off' : 'eye'}
            size={20}
            color={colors.textTertiary}
          />
        </TouchableOpacity>
      </View>
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
  inputWrapper: {
    height: 48,
    backgroundColor: colors.inputBg,
    borderRadius: radius.md,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    borderWidth: 1.5,
    borderColor: 'transparent',
  },
  input: {
    flex: 1,
    fontSize: typography.body.fontSize,
    color: colors.textPrimary,
    height: '100%',
  },
  eyeButton: {
    marginLeft: spacing.sm,
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
