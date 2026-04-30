import React from 'react';
import { View, Image, Text, StyleSheet } from 'react-native';
import { colors, radius } from '@app/styles/tokens';

export interface AvatarProps {
  uri?: string;
  name: string;
  size?: number;
}

export function Avatar({ uri, name, size = 48 }: AvatarProps) {
  const firstLetter = name.charAt(0).toUpperCase();

  return (
    <View style={[styles.container, { width: size, height: size, borderRadius: size / 2 }]}>
      {uri ? (
        <Image source={{ uri }} style={[styles.image, { width: size, height: size, borderRadius: size / 2 }]} />
      ) : (
        <Text style={[styles.letter, { fontSize: size * 0.4 }]}>{firstLetter}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  image: {
    resizeMode: 'cover',
  },
  letter: {
    color: colors.primary,
    fontWeight: '600',
  },
});
