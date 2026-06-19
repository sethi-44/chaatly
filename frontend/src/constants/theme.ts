/**
 * Chaatly Design System — Theme Constants
 *
 * A vibrant, social-food-meetup palette that blends:
 *   • Partiful's event energy  — hot pink #FF2D78, electric coral #FF6B6B, party purple #8B5CF6
 *   • Airbnb's spatial polish   — 8 px grid, refined shadow layers, generous whitespace
 *   • Bumble BFF's warmth       — honey gold #FFC629, warm cream surfaces, inviting radii
 *
 * Light mode: warm cream / ivory surfaces
 * Dark mode: deep charcoal / ink surfaces
 */

import '@/global.css';

import { Platform } from 'react-native';

/* ─────────────────────────── Colors ─────────────────────────── */

export const Colors = {
  light: {
    // ── Core text ──
    text: '#1A1A2E',
    textSecondary: '#6E6E82',
    textTertiary: '#9E9EB0',
    textInverse: '#FFFFFF',

    // ── Backgrounds ──
    background: '#FFF9F4',
    backgroundElement: '#F4ECE4',
    backgroundSelected: '#EDE3D8',
    backgroundElevated: '#FFFFFF',

    // ── Brand — Primary (Partiful coral-pink energy) ──
    primary: '#FF2D78',
    primaryLight: '#FF6B9D',
    primaryDark: '#D9205F',
    primaryMuted: 'rgba(255, 45, 120, 0.10)',

    // ── Brand — Accent (Bumble honey gold warmth) ──
    accent: '#FFC629',
    accentLight: '#FFD966',
    accentDark: '#E0A800',
    accentMuted: 'rgba(255, 198, 41, 0.15)',

    // ── Brand — Secondary (Partiful party purple) ──
    secondary: '#8B5CF6',
    secondaryLight: '#A78BFA',
    secondaryDark: '#7C3AED',
    secondaryMuted: 'rgba(139, 92, 246, 0.10)',

    // ── Brand — Tertiary (electric coral) ──
    coral: '#FF6B6B',
    coralLight: '#FF9999',
    coralDark: '#E04545',
    coralMuted: 'rgba(255, 107, 107, 0.10)',

    // ── Surfaces ──
    cardBackground: '#FFFFFF',
    cardBorder: 'rgba(0, 0, 0, 0.06)',
    cardBackgroundHover: '#FFF5ED',

    // ── Feedback ──
    success: '#22C55E',
    successLight: '#DCFCE7',
    warning: '#F59E0B',
    warningLight: '#FEF3C7',
    error: '#EF4444',
    errorLight: '#FEE2E2',
    info: '#3B82F6',
    infoLight: '#DBEAFE',

    // ── Inputs ──
    inputBackground: '#FFFFFF',
    inputBorder: '#E0D6CC',
    inputBorderFocus: '#FF2D78',
    inputText: '#1A1A2E',
    inputPlaceholder: '#9E9EB0',

    // ── Misc / Chrome ──
    shadowColor: 'rgba(26, 26, 46, 0.08)',
    divider: 'rgba(0, 0, 0, 0.07)',
    overlay: 'rgba(26, 26, 46, 0.50)',
    scrim: 'rgba(26, 26, 46, 0.25)',
    tabIconDefault: '#A8A0B0',
    tabIconSelected: '#FF2D78',
    badge: '#FF2D78',
    link: '#8B5CF6',
  },

  dark: {
    // ── Core text ──
    text: '#F5F0EB',
    textSecondary: '#9A9AB0',
    textTertiary: '#6E6E82',
    textInverse: '#1A1A2E',

    // ── Backgrounds ──
    background: '#0E0E14',
    backgroundElement: '#1A1A28',
    backgroundSelected: '#262636',
    backgroundElevated: '#1E1E2C',

    // ── Brand — Primary (Partiful coral-pink energy) ──
    primary: '#FF4D8E',
    primaryLight: '#FF7EB0',
    primaryDark: '#CC2060',
    primaryMuted: 'rgba(255, 77, 142, 0.15)',

    // ── Brand — Accent (Bumble honey gold warmth) ──
    accent: '#FFD04A',
    accentLight: '#FFE080',
    accentDark: '#CCA000',
    accentMuted: 'rgba(255, 208, 74, 0.15)',

    // ── Brand — Secondary (Partiful party purple) ──
    secondary: '#A78BFA',
    secondaryLight: '#C4B5FD',
    secondaryDark: '#8B5CF6',
    secondaryMuted: 'rgba(167, 139, 250, 0.15)',

    // ── Brand — Tertiary (electric coral) ──
    coral: '#FF8080',
    coralLight: '#FFADAD',
    coralDark: '#FF5252',
    coralMuted: 'rgba(255, 128, 128, 0.12)',

    // ── Surfaces ──
    cardBackground: '#1A1A28',
    cardBorder: 'rgba(255, 255, 255, 0.06)',
    cardBackgroundHover: '#222234',

    // ── Feedback ──
    success: '#34D399',
    successLight: 'rgba(52, 211, 153, 0.15)',
    warning: '#FBBF24',
    warningLight: 'rgba(251, 191, 36, 0.15)',
    error: '#F87171',
    errorLight: 'rgba(248, 113, 113, 0.15)',
    info: '#60A5FA',
    infoLight: 'rgba(96, 165, 250, 0.15)',

    // ── Inputs ──
    inputBackground: '#262636',
    inputBorder: '#35354A',
    inputBorderFocus: '#FF4D8E',
    inputText: '#F5F0EB',
    inputPlaceholder: '#6E6E82',

    // ── Misc / Chrome ──
    shadowColor: 'rgba(0, 0, 0, 0.50)',
    divider: 'rgba(255, 255, 255, 0.07)',
    overlay: 'rgba(0, 0, 0, 0.70)',
    scrim: 'rgba(0, 0, 0, 0.40)',
    tabIconDefault: '#6E6E82',
    tabIconSelected: '#FF4D8E',
    badge: '#FF4D8E',
    link: '#A78BFA',
  },
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;

/* ─────────────────────────── Gradients ─────────────────────────── */

/**
 * Gradient presets for LinearGradient usage throughout the app.
 * Each entry is a tuple of colour stops (2-3 stops).
 */
export const Gradients = {
  light: {
    /** Primary CTA buttons & hero accents */
    primary: ['#FF2D78', '#FF6B6B'] as const,
    /** Party-purple → coral energy */
    vivid: ['#8B5CF6', '#FF2D78', '#FF6B6B'] as const,
    /** Warm background washes */
    warm: ['#FFF9F4', '#FFF0E4'] as const,
    /** Sunset-inspired hero banners */
    sunset: ['#FF6B6B', '#FFC629'] as const,
    /** Honey gold shimmer for badges / highlights */
    gold: ['#FFC629', '#FFE080'] as const,
    /** Subtle elevated card surface */
    card: ['#FFFFFF', '#FFF8F0'] as const,
    /** Purple to pink party gradient */
    party: ['#8B5CF6', '#FF2D78'] as const,
  },
  dark: {
    /** Primary CTA buttons & hero accents */
    primary: ['#FF4D8E', '#FF8080'] as const,
    /** Party-purple → coral energy */
    vivid: ['#A78BFA', '#FF4D8E', '#FF8080'] as const,
    /** Deep background washes */
    warm: ['#0E0E14', '#1A1A28'] as const,
    /** Rich sunset-inspired hero banners */
    sunset: ['#FF5252', '#CCA000'] as const,
    /** Honey gold shimmer for badges / highlights */
    gold: ['#FFD04A', '#FFE080'] as const,
    /** Elevated card surfaces */
    card: ['#1A1A28', '#262636'] as const,
    /** Purple to pink party gradient */
    party: ['#A78BFA', '#FF4D8E'] as const,
  },
} as const;

/* ─────────────────────────── Fonts ─────────────────────────── */

export const Fonts = Platform.select({
  ios: {
    /** iOS system default */
    sans: 'system-ui',
    /** iOS serif */
    serif: 'ui-serif',
    /** iOS rounded — perfect for the friendly Chaatly brand */
    rounded: 'ui-rounded',
    /** iOS monospace */
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
  web: {
    sans: 'var(--font-display)',
    serif: 'var(--font-serif)',
    rounded: 'var(--font-rounded)',
    mono: 'var(--font-mono)',
  },
});

/* ─────────────────────────── Spacing ─────────────────────────── */

/**
 * Airbnb-inspired 8 px grid with friendly named aliases.
 *
 *   half=2  one=4  two=8  three=16  four=24  five=32  six=64  seven=80  eight=96
 *
 * Numeric keys follow the clean 4/8 px progression:
 *   xs=4  sm=8  md=12  base=16  lg=20  xl=24  '2xl'=32  '3xl'=40  '4xl'=48  '5xl'=64  '6xl'=80  '7xl'=96
 */
export const Spacing = {
  // ── Named aliases (backward-compat) ──
  half: 2,
  one: 4,
  two: 8,
  three: 16,
  four: 24,
  five: 32,
  six: 64,
  seven: 80,
  eight: 96,

  // ── Numeric 8 px grid scale ──
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 20,
  xl: 24,
  '2xl': 32,
  '3xl': 40,
  '4xl': 48,
  '5xl': 64,
  '6xl': 80,
  '7xl': 96,
} as const;

/* ─────────────────────────── Shadows ─────────────────────────── */

/**
 * Airbnb-inspired elevation layers.
 * Use with React Native's `style` prop (spread the object).
 * On web these translate to box-shadows via RNW.
 */
export const Shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.10,
    shadowRadius: 16,
    elevation: 6,
  },
  xl: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.12,
    shadowRadius: 24,
    elevation: 10,
  },
} as const;

/* ─────────────────────────── Border Radii ─────────────────────────── */

/**
 * Bumble-BFF-inspired approachable rounded corners.
 * Generous radii make cards and buttons feel warm and inviting.
 */
export const Radii = {
  /** Subtle rounding — chips, tags */
  sm: 8,
  /** Cards, input fields */
  md: 16,
  /** Modals, bottom sheets */
  lg: 24,
  /** Large buttons, floating actions */
  xl: 32,
  /** Pill / circle */
  full: 9999,
} as const;

/* ─────────────────────────── Animation ─────────────────────────── */

/**
 * Motion timing presets (milliseconds & easing curves).
 * Keep micro-interactions snappy; page transitions smooth.
 */
export const Animation = {
  /** Instant feedback — toggles, taps */
  fast: 120,
  /** Default UI transitions */
  normal: 250,
  /** Page / modal transitions */
  slow: 400,
  /** Dramatic hero reveals */
  slower: 600,

  /** Spring configs for react-native-reanimated / Animated */
  spring: {
    snappy: { damping: 20, stiffness: 300, mass: 0.8 },
    gentle: { damping: 15, stiffness: 150, mass: 1 },
    bouncy: { damping: 12, stiffness: 200, mass: 0.6 },
  },

  /** Standard easing curves (cubic bezier values) */
  easing: {
    easeIn: [0.42, 0, 1, 1] as const,
    easeOut: [0, 0, 0.58, 1] as const,
    easeInOut: [0.42, 0, 0.58, 1] as const,
    spring: [0.175, 0.885, 0.32, 1.275] as const,
  },
} as const;

/* ─────────────────────────── Layout ─────────────────────────── */

export const BottomTabInset = Platform.select({ ios: 50, android: 80 }) ?? 0;
export const MaxContentWidth = 800;
