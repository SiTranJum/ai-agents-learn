import { StyleSheet } from 'react-native';
import { theme } from './theme';

export const globalStyles = StyleSheet.create({
  pageContainer: {
    flex: 1,
    backgroundColor: theme.colors.bgPage,
  },
  pageContent: {
    flex: 1,
    paddingHorizontal: theme.layout.pageHorizontalPadding,
  },
  card: {
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.md,
    padding: theme.layout.cardPadding,
    ...theme.shadows.card,
  },
  sectionGap: {
    marginBottom: theme.layout.cardGap,
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
});
