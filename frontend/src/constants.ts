import { Platform } from 'react-native';

export const API_URL = process.env.EXPO_PUBLIC_API_URL || Platform.select({
  android: 'http://10.0.2.2:8000',
  default: 'http://localhost:8000',
});

export const C = {
  bg: '#FFFDF9',
  surface: '#FFFFFF',
  card: '#FFFFFF',
  cardBorder: '#EBEBEB',
  primary: '#FF2D78',
  primaryLight: '#FF6B9D',
  primaryDark: '#E02468',
  accent: '#FFC629',
  purple: '#8B5CF6',
  text: '#222222',
  textSecondary: '#717171',
  textMuted: '#B0B0B0',
  border: '#EBEBEB',
  input: '#F7F7F9',
  inputBg: '#F7F7F9',
  inputBorder: '#EBEBEB',
  error: '#E31C5F',
  success: '#00A699',
  shadow: 'rgba(0,0,0,0.08)',
  searchBg: '#FFFFFF',
} as const;

export const CARD_COLORS = ['#FFEBF0', '#FFF0E6', '#F0E6FF', '#E6FFF0', '#FFF5E6', '#E6F0FF'];
export const CARD_EMOJIS = ['🍕', '🌮', '🍜', '🥘', '🍣', '🧆', '🥗', '🍲', '🫕', '🥂'];

export const { width: SCREEN_W } = require('react-native').Dimensions.get('window');
export const SMALL_CARD_W = SCREEN_W * 0.52;

export const SHADOW_SM = {
  shadowColor: '#000',
  shadowOffset: { width: 0, height: 1 },
  shadowOpacity: 0.04,
  shadowRadius: 3,
  elevation: 1,
};

export const SHADOW_MD = {
  shadowColor: '#000',
  shadowOffset: { width: 0, height: 3 },
  shadowOpacity: 0.07,
  shadowRadius: 8,
  elevation: 3,
};

export function softBg(hex: string, opacity: number = 0.1): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${opacity})`;
}

export function getCardColor(index: number): string {
  return CARD_COLORS[index % CARD_COLORS.length];
}

export function getCardEmoji(index: number): string {
  return CARD_EMOJIS[index % CARD_EMOJIS.length];
}

export const ACTIVE_COLOR = '#FF2D78';
export const INACTIVE_COLOR = '#9CA3AF';
export const TAB_BAR_BG = 'rgba(255, 253, 250, 0.92)';
export const TAB_BAR_BORDER = 'rgba(0, 0, 0, 0.06)';