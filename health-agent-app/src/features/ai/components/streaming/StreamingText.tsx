// 流式文本：末尾闪烁光标 ▌（500ms 周期）
// 流式中显示光标，done 后隐藏
// T6 从 demo/components/StreamingText.tsx 提升

import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { theme } from '@app/styles/theme';

interface Props {
  content: string;
  /** 是否仍在流式中 */
  streaming: boolean;
}

export function StreamingText({ content, streaming }: Props) {
  const [cursorVisible, setCursorVisible] = useState(true);

  useEffect(() => {
    if (!streaming) {
      setCursorVisible(false);
      return;
    }
    const timer = setInterval(() => {
      setCursorVisible((v) => !v);
    }, 500);
    return () => clearInterval(timer);
  }, [streaming]);

  return (
    <View style={styles.container}>
      <Text style={styles.text}>
        {content}
        {streaming && (
          <Text style={[styles.cursor, !cursorVisible && styles.cursorHidden]}>
            ▌
          </Text>
        )}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: theme.spacing.xs,
  },
  text: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    lineHeight: 22,
  },
  cursor: {
    color: theme.colors.primary,
    fontWeight: '700',
  },
  cursorHidden: {
    color: 'transparent',
  },
});
