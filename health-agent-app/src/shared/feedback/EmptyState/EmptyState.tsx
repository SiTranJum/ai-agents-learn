import React from 'react';
import { View, Text, Image, StyleSheet, ImageSourcePropType } from 'react-native';
import { Button } from '@shared/ui/Button';
import { theme } from '@app/styles/theme';

export interface EmptyStateProps {
  image?: ImageSourcePropType;
  title: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
}

export function EmptyState({
  image,
  title,
  description,
  actionText,
  onAction,
}: EmptyStateProps) {
  return (
    <View style={styles.container}>
      {image && <Image source={image} style={styles.image} />}
      <Text style={styles.title}>{title}</Text>
      {description && <Text style={styles.description}>{description}</Text>}
      {actionText && onAction && (
        <Button onPress={onAction} style={styles.button}>
          {actionText}
        </Button>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.xl,
  },
  image: {
    width: 200,
    height: 200,
    marginBottom: theme.spacing.lg,
  },
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.sm,
    textAlign: 'center',
  },
  description: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginBottom: theme.spacing.xl,
  },
  button: {
    marginTop: theme.spacing.md,
  },
});
