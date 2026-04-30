import { ViewStyle, TextStyle } from 'react-native';

export type ButtonVariant = 'primary' | 'secondary' | 'text';
export type ButtonSize = 'small' | 'medium' | 'large';

export interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  onPress: () => void;
  children: React.ReactNode;
  style?: ViewStyle;
  textStyle?: TextStyle;
}
