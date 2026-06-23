import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Platform,
  RefreshControl,
  ActivityIndicator,
  Dimensions,
  StatusBar,
  KeyboardAvoidingView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Animated, {
  FadeInDown,
  FadeInUp,
  FadeIn,
  FadeInRight,
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withRepeat,
  withTiming,
  withSequence,
  Easing,
} from 'react-native-reanimated';
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import { API_URL, C, CARD_COLORS, CARD_EMOJIS, getCardColor, getCardEmoji } from '../constants';

const setStorageItemAsync = async (key: string, value: string) => {
  if (Platform.OS === 'web') {
    try { localStorage.setItem(key, value); } catch (e) {}
  } else {
    await SecureStore.setItemAsync(key, value);
  }
};

const getStorageItemAsync = async (key: string) => {
  if (Platform.OS === 'web') {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  } else {
    return await SecureStore.getItemAsync(key);
  }
};

const deleteStorageItemAsync = async (key: string) => {
  if (Platform.OS === 'web') {
    try { localStorage.removeItem(key); } catch (e) {}
  } else {
    await SecureStore.deleteItemAsync(key);
  }
};

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ── Confetti Dot ─────────────────────────────────────────────────────
function ConfettiDot({
  size,
  color,
  top,
  left,
  delay,
}: {
  size: number;
  color: string;
  top: number;
  left: number;
  delay: number;
}) {
  const opacity = useSharedValue(0);

  useEffect(() => {
    opacity.value = withRepeat(
      withSequence(
        withTiming(0.6, { duration: 1200 + delay, easing: Easing.inOut(Easing.ease) }),
        withTiming(0.15, { duration: 1200 + delay, easing: Easing.inOut(Easing.ease) })
      ),
      -1,
      true
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [delay]);

  const animStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }));

  return (
    <Animated.View
      style={[
        {
          position: 'absolute',
          width: size,
          height: size,
          borderRadius: size / 2,
          backgroundColor: color,
          top,
          left,
        },
        animStyle,
      ]}
    />
  );
}

// ── Animated Emoji Hero ──────────────────────────────────────────────
function AnimatedEmojiHero() {
  const floatY = useSharedValue(0);

  useEffect(() => {
    floatY.value = withRepeat(
      withSequence(
        withTiming(-8, { duration: 1800, easing: Easing.inOut(Easing.ease) }),
        withTiming(8, { duration: 1800, easing: Easing.inOut(Easing.ease) })
      ),
      -1,
      true
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const animStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: floatY.value }],
  }));

  return (
    <View style={styles.emojiHeroOuter}>
      {/* Gradient-like circular background using concentric rings */}
      <View style={styles.emojiRing3} />
      <View style={styles.emojiRing2} />
      <View style={styles.emojiRing1} />
      <Animated.Text style={[styles.landingEmojiLarge, animStyle]}>🌶️</Animated.Text>
    </View>
  );
}

// ── Spots Progress Bar ───────────────────────────────────────────────
function SpotsBar({ spotsLeft, total }: { spotsLeft: number; total: number }) {
  const filled = Math.max(0, total - spotsLeft);
  const pct = Math.min((filled / total) * 100, 100);
  const isFull = spotsLeft <= 0;
  const isAlmostFull = spotsLeft <= 2 && spotsLeft > 0;

  return (
    <View style={styles.spotsBarContainer}>
      <View style={styles.spotsBarTrack}>
        <View
          style={[
            styles.spotsBarFill,
            {
              width: `${pct}%`,
              backgroundColor: isFull ? C.textMuted : isAlmostFull ? '#FF8C00' : C.success,
            },
          ]}
        />
      </View>
      <Text style={styles.spotsBarLabel}>
        {isFull ? 'Full' : `${spotsLeft} of ${total} spots left`}
      </Text>
    </View>
  );
}

// ── Animated Input ───────────────────────────────────────────────────
function AnimatedInput({
  label,
  placeholder,
  value,
  onChangeText,
  secureTextEntry,
  keyboardType,
  autoCapitalize,
  autoFocus,
}: {
  label: string;
  placeholder: string;
  value: string;
  onChangeText: (t: string) => void;
  secureTextEntry?: boolean;
  keyboardType?: 'default' | 'email-address' | 'numeric';
  autoCapitalize?: 'none' | 'sentences';
  autoFocus?: boolean;
}) {
  const [focused, setFocused] = useState(false);

  return (
    <Animated.View entering={FadeInRight.duration(400).springify()} style={styles.inputContainer}>
      <Text style={styles.inputLabel}>{label}</Text>
      <View
        style={[
          styles.inputWrapper,
          {
            borderColor: focused ? C.primary : C.border,
            backgroundColor: focused ? C.surface : C.inputBg,
          },
        ]}
      >
        <TextInput
          style={styles.input}
          placeholder={placeholder}
          placeholderTextColor={C.textMuted}
          value={value}
          onChangeText={onChangeText}
          secureTextEntry={secureTextEntry}
          keyboardType={keyboardType}
          autoCapitalize={autoCapitalize}
          autoFocus={autoFocus}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
        />
      </View>
    </Animated.View>
  );
}

// ── Primary Button ───────────────────────────────────────────────────
function PrimaryButton({
  label,
  onPress,
  loading,
  disabled,
}: {
  label: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
}) {
  const scale = useSharedValue(1);
  const animStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return (
    <Animated.View style={[animStyle, { width: '100%', marginTop: 'auto', paddingTop: 20 }]}>
      <TouchableOpacity
        style={[styles.primaryBtn, disabled && { opacity: 0.5, backgroundColor: C.border }]}
        onPress={onPress}
        disabled={disabled || loading}
        activeOpacity={0.9}
        onPressIn={() => {
          scale.value = withSpring(0.96);
        }}
        onPressOut={() => {
          scale.value = withSpring(1);
        }}
      >
        {loading ? (
          <ActivityIndicator color={disabled ? C.textMuted : C.text} size="small" />
        ) : (
          <Text style={[styles.primaryBtnText, disabled && { color: C.textMuted }]}>{label}</Text>
        )}
      </TouchableOpacity>
    </Animated.View>
  );
}

interface MeetupData {
  id: number;
  title: string;
  description: string | null;
  location: string;
  host: { username: string } | null;
  attendee_count: number;
  max_attendees: number;
  spots_left?: number;
}

// ── Meetup Card (Partiful Celebratory + Airbnb Spacing) ──────────────
function MeetupCard({
  meetup,
  onJoin,
  index,
}: {
  meetup: MeetupData;
  onJoin: (id: number) => void;
  index: number;
}) {
  const hostInitial = meetup.host?.username?.charAt(0)?.toUpperCase() || '?';
  const spotsLeft = meetup.spots_left ?? (meetup.max_attendees - (meetup.attendee_count || 0));
  const totalSpots = meetup.max_attendees || 10;
  const isFull = spotsLeft <= 0;

  const bgColor = getCardColor(index);
  const emoji = getCardEmoji(index);

  const joinScale = useSharedValue(1);
  const joinAnimStyle = useAnimatedStyle(() => ({
    transform: [{ scale: joinScale.value }],
  }));

  return (
    <Animated.View
      entering={FadeInUp.delay(100 * index)
        .duration(500)
        .springify()}
      style={styles.card}
    >
      {/* Gradient accent strip at top */}
      <View style={styles.cardAccentStrip}>
        <View style={styles.cardAccentLeft} />
        <View style={styles.cardAccentRight} />
      </View>

      {/* Colorful emoji header band */}
      <View style={[styles.cardGraphic, { backgroundColor: bgColor }]}>
        <Text style={styles.cardGraphicEmoji}>{emoji}</Text>
      </View>

      <View style={styles.cardContent}>
        <View style={styles.cardHeader}>
          <View style={{ flex: 1, paddingRight: 12 }}>
            <Text style={styles.cardTitle} numberOfLines={2}>
              {meetup.title}
            </Text>
            <Text style={styles.cardSubtitle}>
              Hosted by {meetup.host?.username || 'Unknown'}
            </Text>
          </View>
          {/* Host avatar with gradient border effect */}
          <View style={styles.hostAvatarOuter}>
            <View style={styles.hostAvatar}>
              <Text style={styles.hostInitial}>{hostInitial}</Text>
            </View>
          </View>
        </View>

        {meetup.description ? (
          <Text style={styles.cardDesc} numberOfLines={2}>
            {meetup.description}
          </Text>
        ) : null}

        <View style={styles.cardDivider} />

        <View style={styles.cardDetails}>
          <View style={styles.detailItem}>
            <Text style={styles.detailIcon}>📍</Text>
            <Text style={styles.detailText} numberOfLines={1}>
              {meetup.location}
            </Text>
          </View>
        </View>

        {/* Spots progress bar */}
        <SpotsBar spotsLeft={spotsLeft} total={totalSpots} />

        {/* Join button */}
        <Animated.View style={joinAnimStyle}>
          <TouchableOpacity
            style={[styles.joinBtn, isFull && styles.joinBtnDisabled]}
            onPress={() => onJoin(meetup.id)}
            disabled={isFull}
            activeOpacity={0.85}
            onPressIn={() => {
              joinScale.value = withSpring(0.96);
            }}
            onPressOut={() => {
              joinScale.value = withSpring(1);
            }}
          >
            <Text style={[styles.joinBtnText, isFull && styles.joinBtnTextDisabled]}>
              {isFull ? 'Meetup Full' : '🎉 Join Meetup'}
            </Text>
          </TouchableOpacity>
        </Animated.View>
      </View>
    </Animated.View>
  );
}

// ── Main App Component ───────────────────────────────────────────────
type AuthStep =
  | 'landing'
  | 'register_email'
  | 'register_username'
  | 'register_password'
  | 'login_email'
  | 'login_password'
  | 'dashboard';

export default function App() {
  const [token, setToken] = useState('');
  const [currentUser, setCurrentUser] = useState('');
  const [step, setStep] = useState<AuthStep>('landing');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const handleLogout = async () => {
    try {
      const rToken = await getStorageItemAsync('refreshToken');
      if (rToken) {
        await axios.post(`${API_URL}/supabase/logout`, { refresh_token: rToken });
      }
    } catch (e) {
      console.warn('Logout error', e);
    } finally {
      await deleteStorageItemAsync('userToken');
      await deleteStorageItemAsync('refreshToken');
      setToken('');
      setCurrentUser('');
      setStep('landing');
    }
  };

  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          try {
            const rToken = await getStorageItemAsync('refreshToken');
            if (rToken) {
              const res = await axios.post(`${API_URL}/supabase/refresh`, { refresh_token: rToken });
              const newAccess = res.data.access_token;
              const newRefresh = res.data.refresh_token;
              await setStorageItemAsync('userToken', newAccess);
              await setStorageItemAsync('refreshToken', newRefresh);
              setToken(newAccess);
              originalRequest.headers.Authorization = `Bearer ${newAccess}`;
              return axios(originalRequest);
            }
          } catch (e) {
            handleLogout();
          }
        }
        return Promise.reject(error);
      }
    );

    const loadToken = async () => {
      try {
        console.log("Loading token...");
        const storedToken = await getStorageItemAsync('userToken');
        console.log("Loaded:", storedToken);
        if (storedToken) {
          setToken(storedToken);
          setStep('dashboard');
        }
      } catch (e) {
        console.warn('Failed to load token', e);
      }
    };
    loadToken();

    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, []);

  // Auth fields
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Dashboard fields
  const [meetups, setMeetups] = useState<MeetupData[]>([]);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [maxAttendees, setMaxAttendees] = useState('10');

  const fetchCurrentUser = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_URL}/supabase/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCurrentUser(res.data.username);
    } catch (err: any) {
      console.warn('Failed to fetch user:', err);
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (detail || 'Failed to fetch user'));
      setTimeout(() => setError(''), 5000);
    }
  }, [token]);

  const fetchMeetups = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/meetups`);
      setMeetups(res.data);
    } catch (err: any) {
      console.warn('Failed to fetch meetups:', err);
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (detail || 'Failed to fetch meetups'));
      setTimeout(() => setError(''), 5000);
    }
  }, []);

  useEffect(() => {
    if (token && step === 'dashboard') {
      fetchMeetups();
      fetchCurrentUser();
    }
  }, [token, step, fetchMeetups, fetchCurrentUser]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchMeetups();
    setRefreshing(false);
  }, [fetchMeetups]);

  const handleRegister = async () => {
    console.log("Register clicked");
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API_URL}/supabase/register`, { username, email, password });
      console.log("Backend response:", res.data);
      setToken(res.data.access_token);
      console.log("Token set in state");
      
      await setStorageItemAsync('userToken', res.data.access_token);
      if (res.data.refresh_token) {
        await setStorageItemAsync('refreshToken', res.data.refresh_token);
      }
      console.log("Token saved");
      
      setStep('dashboard');
      console.log("Navigated to dashboard");
    } catch (err: any) {
      console.error("REGISTER FAILED");
      console.error(err);
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (detail || 'Registration failed.'));
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const loginPayload = `grant_type=password&username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;
      const res = await axios.post(`${API_URL}/supabase/login`, loginPayload, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      setToken(res.data.access_token);
      
      await setStorageItemAsync('userToken', res.data.access_token);
      if (res.data.refresh_token) {
        await setStorageItemAsync('refreshToken', res.data.refresh_token);
      }
      
      setStep('dashboard');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (detail || 'Login failed.'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateMeetup = async () => {
    if (!title || !location) {
      setError('Title and location are required');
      setTimeout(() => setError(''), 3000);
      return;
    }
    try {
      await axios.post(
        `${API_URL}/meetups`,
        { title, description, location, max_attendees: parseInt(maxAttendees, 10) || 10 },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTitle('');
      setDescription('');
      setLocation('');
      setMaxAttendees('10');
      fetchMeetups();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (detail || 'Failed to create meetup'));
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleJoin = async (id: number) => {
    try {
      await axios.post(
        `${API_URL}/meetups/${id}/join`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchMeetups();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (detail || 'Could not join meetup'));
      setTimeout(() => setError(''), 3000);
    }
  };

  // ── Back Navigation Handler ────────────────────────────────────────
  const handleBack = () => {
    setEmail('');
    setUsername('');
    setPassword('');
    switch (step) {
      case 'register_email':
      case 'login_email':
        setStep('landing');
        setError('');
        break;
      case 'register_username':
        setStep('register_email');
        setError('');
        break;
      case 'register_password':
        setStep('register_username');
        setError('');
        break;
      case 'login_password':
        setStep('login_email');
        setError('');
        break;
      default:
        setStep('landing');
        setError('');
    }
  };

  // ── Onboarding Experience (Bumble BFF Style) ───────────────────────
  const renderOnboarding = () => {
    return (
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.onboardingContainer}>
          {step !== 'landing' && (
            <TouchableOpacity style={styles.backBtn} onPress={handleBack}>
              <Text style={styles.backBtnText}>← Back</Text>
            </TouchableOpacity>
          )}

          {error ? (
            <Animated.View entering={FadeInDown} style={styles.errorBanner}>
              <Text style={styles.errorText}>{error}</Text>
            </Animated.View>
          ) : null}

          {step === 'landing' && (
            <Animated.View entering={FadeInDown.duration(600)} style={styles.stepContent}>
              <View style={styles.landingHero}>
                {/* Confetti-like decorative dots */}
                <ConfettiDot size={8} color={C.primary} top={20} left={30} delay={0} />
                <ConfettiDot size={6} color={C.accent} top={60} left={SCREEN_WIDTH - 80} delay={200} />
                <ConfettiDot size={10} color={C.purple} top={110} left={50} delay={400} />
                <ConfettiDot size={7} color={C.success} top={40} left={SCREEN_WIDTH - 120} delay={100} />
                <ConfettiDot size={5} color={C.primary} top={140} left={SCREEN_WIDTH - 70} delay={300} />
                <ConfettiDot size={9} color={C.accent} top={160} left={80} delay={500} />
                <ConfettiDot size={6} color={C.purple} top={90} left={SCREEN_WIDTH - 100} delay={150} />
                <ConfettiDot size={8} color={C.primary} top={180} left={SCREEN_WIDTH / 2 + 60} delay={250} />

                <AnimatedEmojiHero />

                {/* Brand name with gradient-like effect */}
                <View style={styles.brandNameContainer}>
                  <View style={styles.brandGradientBg}>
                    <Text style={styles.landingTitle}>Chaatly</Text>
                  </View>
                </View>

                <Text style={styles.landingTagline}>
                  Where strangers become{'\n'}friends over food 🍜
                </Text>
              </View>

              <View style={styles.landingFooter}>
                <TouchableOpacity
                  style={styles.landingBtnPrimary}
                  onPress={() => setStep('register_email')}
                  activeOpacity={0.85}
                >
                  <Text style={styles.landingBtnPrimaryText}>Get Started</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.landingBtnSecondary}
                  onPress={() => setStep('login_email')}
                  activeOpacity={0.7}
                >
                  <Text style={styles.landingBtnSecondaryText}>
                    I already have an account
                  </Text>
                </TouchableOpacity>
              </View>
            </Animated.View>
          )}

          {step === 'register_email' && (
            <Animated.View entering={FadeInRight} style={styles.stepContent}>
              <Text style={styles.stepEmoji}>📧</Text>
              <Text style={styles.stepTitle}>{`What's your email\naddress?`}</Text>
              <Text style={styles.stepSubtitle}>
                {`We'll use this to keep your account safe.`}
              </Text>
              <AnimatedInput
                label="Email"
                placeholder="you@example.com"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoFocus
              />
              <PrimaryButton
                label="Continue"
                disabled={!email.includes('@')}
                onPress={() => setStep('register_username')}
              />
            </Animated.View>
          )}

          {step === 'register_username' && (
            <Animated.View entering={FadeInRight} style={styles.stepContent}>
              <Text style={styles.stepEmoji}>👤</Text>
              <Text style={styles.stepTitle}>Pick a username</Text>
              <Text style={styles.stepSubtitle}>
                This is how other foodies will see you.
              </Text>
              <AnimatedInput
                label="Username"
                placeholder="e.g. spicylover99"
                value={username}
                onChangeText={setUsername}
                autoCapitalize="none"
                autoFocus
              />
              <PrimaryButton
                label="Continue"
                disabled={username.length < 3}
                onPress={() => setStep('register_password')}
              />
            </Animated.View>
          )}

          {step === 'register_password' && (
            <Animated.View entering={FadeInRight} style={styles.stepContent}>
              <Text style={styles.stepEmoji}>🔒</Text>
              <Text style={styles.stepTitle}>Set a password</Text>
              <Text style={styles.stepSubtitle}>Make it a secret recipe.</Text>
              <AnimatedInput
                label="Password"
                placeholder="At least 8 characters"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                autoFocus
              />
              <PrimaryButton
                label="Complete Sign Up 🎉"
                disabled={password.length < 8}
                loading={loading}
                onPress={handleRegister}
              />
            </Animated.View>
          )}

          {step === 'login_email' && (
            <Animated.View entering={FadeInRight} style={styles.stepContent}>
              <Text style={styles.stepEmoji}>👋</Text>
              <Text style={styles.stepTitle}>Welcome back!</Text>
              <Text style={styles.stepSubtitle}>
                Enter your email to continue.
              </Text>
              <AnimatedInput
                label="Email"
                placeholder="you@example.com"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoFocus
              />
              <PrimaryButton
                label="Continue"
                disabled={!email.includes('@')}
                onPress={() => setStep('login_password')}
              />
            </Animated.View>
          )}

          {step === 'login_password' && (
            <Animated.View entering={FadeInRight} style={styles.stepContent}>
              <Text style={styles.stepEmoji}>🔑</Text>
              <Text style={styles.stepTitle}>Enter your password</Text>
              <Text style={styles.stepSubtitle}>
                {`Let's get you back to the table.`}
              </Text>
              <AnimatedInput
                label="Password"
                placeholder="••••••••"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                autoFocus
              />
              <PrimaryButton
                label="Log In"
                disabled={password.length < 1}
                loading={loading}
                onPress={handleLogin}
              />
            </Animated.View>
          )}
        </View>
      </KeyboardAvoidingView>
    );
  };

  // ── Dashboard (Airbnb Spacing + Partiful Aesthetic) ────────────────
  const renderDashboard = () => (
    <View style={styles.dashboardContainer}>
      {/* Dashboard Header */}
      <Animated.View entering={FadeInDown} style={styles.dashHeader}>
        <View style={styles.dashHeaderLeft}>
          <Text style={styles.dashLogoEmoji}>🌶️</Text>
          <Text style={styles.dashLogo}>Chaatly</Text>
        </View>
        <TouchableOpacity
          style={styles.profileBtn}
          onPress={handleLogout}
          activeOpacity={0.8}
        >
          <Text style={styles.profileBtnInitial}>
            {currentUser?.charAt(0)?.toUpperCase() || 'U'}
          </Text>
        </TouchableOpacity>
      </Animated.View>
      <View style={styles.dashDivider} />

      <ScrollView
        contentContainerStyle={{ paddingBottom: 100, paddingHorizontal: 24 }}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.primary} />
        }
      >
        {/* Error banner in dashboard */}
        {error ? (
          <Animated.View entering={FadeInDown} style={styles.errorBanner}>
            <Text style={styles.errorText}>{error}</Text>
          </Animated.View>
        ) : null}

        {/* Host an Event Section */}
        <Animated.View entering={FadeInUp.delay(100)} style={styles.hostSection}>
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionHeader}>Host an event</Text>
            <Text style={styles.sectionHeaderEmoji}>✨</Text>
          </View>

          <View style={styles.hostCard}>
            {/* Gradient accent strip */}
            <View style={styles.hostCardAccent}>
              <View style={styles.hostCardAccentLeft} />
              <View style={styles.hostCardAccentRight} />
            </View>

            <View style={styles.hostCardInner}>
              <TextInput
                style={styles.hostInput}
                placeholder="What's the meetup called?"
                placeholderTextColor={C.textMuted}
                value={title}
                onChangeText={setTitle}
              />
              <TextInput
                style={[styles.hostInput, styles.hostInputMultiline]}
                placeholder="Tell people what to expect... (optional)"
                placeholderTextColor={C.textMuted}
                value={description}
                onChangeText={setDescription}
                multiline
                numberOfLines={3}
                textAlignVertical="top"
              />
              <TextInput
                style={styles.hostInput}
                placeholder="📍 Where is it?"
                placeholderTextColor={C.textMuted}
                value={location}
                onChangeText={setLocation}
              />

              <View style={styles.hostAttendeesRow}>
                <Text style={styles.hostAttendeesLabel}>👥 Max attendees</Text>
                <TextInput
                  style={styles.hostAttendeesInput}
                  value={maxAttendees}
                  onChangeText={setMaxAttendees}
                  keyboardType="numeric"
                  placeholderTextColor={C.textMuted}
                />
              </View>

              <TouchableOpacity
                style={styles.hostBtn}
                onPress={handleCreateMeetup}
                activeOpacity={0.85}
              >
                <Text style={styles.hostBtnText}>Create Meetup ✨</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Animated.View>

        {/* Discover Section */}
        <Animated.View entering={FadeInUp.delay(200)}>
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionHeader}>Discover</Text>
            <Text style={styles.sectionHeaderEmoji}>🔥</Text>
          </View>

          {meetups.length === 0 ? (
            <Animated.View entering={FadeIn.delay(300)} style={styles.emptyState}>
              <Text style={styles.emptyEmoji}>🍽️</Text>
              <Text style={styles.emptyTitle}>No meetups yet</Text>
              <Text style={styles.emptySubtitle}>
                Be the first to host! Create a meetup{'\n'}and invite foodies near you.
              </Text>
            </Animated.View>
          ) : (
            meetups.map((m, i) => (
              <MeetupCard key={m.id} meetup={m} onJoin={handleJoin} index={i} />
            ))
          )}
        </Animated.View>
      </ScrollView>
    </View>
  );

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <StatusBar barStyle="dark-content" backgroundColor={C.bg} />
      {step === 'dashboard' && token ? renderDashboard() : renderOnboarding()}
    </SafeAreaView>
  );
}

// ── Styles ───────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: C.bg,
  },

  // ── Onboarding ─────────────────────────────────────────────────────
  onboardingContainer: {
    flex: 1,
    padding: 24,
    paddingTop: 12,
    paddingBottom: 90,
  },
  backBtn: {
    marginBottom: 24,
    alignSelf: 'flex-start',
    paddingVertical: 4,
    paddingRight: 12,
  },
  backBtnText: {
    fontSize: 16,
    color: C.textSecondary,
    fontWeight: '600',
  },
  stepContent: {
    flex: 1,
  },
  stepEmoji: {
    fontSize: 40,
    marginBottom: 16,
  },
  stepTitle: {
    fontSize: 32,
    fontWeight: '800',
    color: C.text,
    marginBottom: 8,
    letterSpacing: -1,
    lineHeight: 40,
  },
  stepSubtitle: {
    fontSize: 17,
    color: C.textSecondary,
    marginBottom: 32,
    lineHeight: 24,
  },

  // ── Landing Hero ───────────────────────────────────────────────────
  landingHero: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emojiHeroOuter: {
    width: 140,
    height: 140,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 32,
  },
  emojiRing3: {
    position: 'absolute',
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: '#FFE0EB',
  },
  emojiRing2: {
    position: 'absolute',
    width: 110,
    height: 110,
    borderRadius: 55,
    backgroundColor: '#FFB3D1',
  },
  emojiRing1: {
    position: 'absolute',
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#FF85B5',
  },
  landingEmojiLarge: {
    fontSize: 56,
    zIndex: 1,
  },
  brandNameContainer: {
    marginBottom: 16,
  },
  brandGradientBg: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  landingTitle: {
    fontSize: 52,
    fontWeight: '900',
    color: C.primary,
    letterSpacing: -2,
    textAlign: 'center',
  },
  landingTagline: {
    fontSize: 18,
    color: C.textSecondary,
    textAlign: 'center',
    lineHeight: 28,
    paddingHorizontal: 24,
  },
  landingFooter: {
    paddingBottom: 24,
  },
  landingBtnPrimary: {
    backgroundColor: C.accent,
    paddingVertical: 18,
    borderRadius: 999,
    alignItems: 'center',
    marginBottom: 16,
    shadowColor: C.accent,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 6,
  },
  landingBtnPrimaryText: {
    color: C.text,
    fontSize: 18,
    fontWeight: '800',
  },
  landingBtnSecondary: {
    backgroundColor: 'transparent',
    paddingVertical: 16,
    alignItems: 'center',
  },
  landingBtnSecondaryText: {
    color: C.textSecondary,
    fontSize: 16,
    fontWeight: '700',
    textDecorationLine: 'underline',
    textDecorationColor: C.border,
  },

  // ── Inputs ─────────────────────────────────────────────────────────
  inputContainer: {
    marginBottom: 24,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: C.text,
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  inputWrapper: {
    borderWidth: 2,
    borderRadius: 16,
    paddingHorizontal: 20,
    height: 64,
    justifyContent: 'center',
  },
  input: {
    fontSize: 18,
    color: C.text,
    height: '100%',
  },

  // ── Primary Button ─────────────────────────────────────────────────
  primaryBtn: {
    backgroundColor: C.text,
    paddingVertical: 18,
    borderRadius: 999,
    alignItems: 'center',
    shadowColor: C.text,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 4,
  },
  primaryBtnText: {
    color: C.surface,
    fontSize: 18,
    fontWeight: '700',
  },

  // ── Dashboard ──────────────────────────────────────────────────────
  dashboardContainer: {
    flex: 1,
  },
  dashHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: 8,
    paddingBottom: 16,
  },
  dashHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dashLogoEmoji: {
    fontSize: 24,
  },
  dashLogo: {
    fontSize: 26,
    fontWeight: '900',
    color: C.primary,
    letterSpacing: -1,
  },
  dashDivider: {
    height: 1,
    backgroundColor: C.border,
    marginHorizontal: 24,
    marginBottom: 24,
  },
  profileBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: C.primary,
    shadowColor: C.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
  },
  profileBtnInitial: {
    color: C.surface,
    fontSize: 18,
    fontWeight: '800',
  },

  // ── Section Headers ────────────────────────────────────────────────
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 8,
  },
  sectionHeader: {
    fontSize: 24,
    fontWeight: '800',
    color: C.text,
    letterSpacing: -0.5,
  },
  sectionHeaderEmoji: {
    fontSize: 20,
  },

  // ── Host Card ──────────────────────────────────────────────────────
  hostSection: {
    marginBottom: 40,
  },
  hostCard: {
    backgroundColor: C.surface,
    borderRadius: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.06,
    shadowRadius: 32,
    elevation: 3,
    borderWidth: 1,
    borderColor: C.border,
    overflow: 'hidden',
  },
  hostCardAccent: {
    height: 4,
    flexDirection: 'row',
  },
  hostCardAccentLeft: {
    flex: 1,
    backgroundColor: C.primary,
  },
  hostCardAccentRight: {
    flex: 1,
    backgroundColor: C.purple,
  },
  hostCardInner: {
    padding: 24,
  },
  hostInput: {
    backgroundColor: C.inputBg,
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    marginBottom: 12,
    color: C.text,
    borderWidth: 1.5,
    borderColor: C.border,
  },
  hostInputMultiline: {
    minHeight: 80,
    paddingTop: 14,
  },
  hostAttendeesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    marginBottom: 16,
    gap: 12,
  },
  hostAttendeesLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: C.text,
  },
  hostAttendeesInput: {
    flex: 1,
    backgroundColor: C.inputBg,
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: C.text,
    borderWidth: 1.5,
    borderColor: C.border,
    textAlign: 'center',
  },
  hostBtn: {
    backgroundColor: C.primary,
    borderRadius: 999,
    paddingVertical: 16,
    alignItems: 'center',
    shadowColor: C.primary,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 4,
  },
  hostBtnText: {
    color: C.surface,
    fontSize: 16,
    fontWeight: '800',
  },

  // ── Meetup Card ────────────────────────────────────────────────────
  card: {
    backgroundColor: C.surface,
    borderRadius: 24,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.06,
    shadowRadius: 32,
    elevation: 3,
    borderWidth: 1,
    borderColor: C.border,
    overflow: 'hidden',
  },
  cardAccentStrip: {
    height: 4,
    flexDirection: 'row',
  },
  cardAccentLeft: {
    flex: 1,
    backgroundColor: C.primary,
  },
  cardAccentRight: {
    flex: 1,
    backgroundColor: C.purple,
  },
  cardGraphic: {
    height: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardGraphicEmoji: {
    fontSize: 48,
  },
  cardContent: {
    padding: 24,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: C.text,
    lineHeight: 28,
    marginBottom: 4,
    letterSpacing: -0.3,
  },
  cardSubtitle: {
    fontSize: 15,
    color: C.textSecondary,
    fontWeight: '500',
  },
  hostAvatarOuter: {
    width: 52,
    height: 52,
    borderRadius: 26,
    padding: 2,
    backgroundColor: C.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  hostAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: C.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  hostInitial: {
    fontSize: 20,
    fontWeight: '800',
    color: C.primary,
  },
  cardDesc: {
    fontSize: 15,
    color: C.textSecondary,
    lineHeight: 22,
    marginBottom: 16,
  },
  cardDivider: {
    height: 1,
    backgroundColor: C.border,
    marginBottom: 16,
  },
  cardDetails: {
    marginBottom: 16,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  detailIcon: {
    fontSize: 16,
    marginRight: 10,
  },
  detailText: {
    fontSize: 15,
    color: C.text,
    fontWeight: '500',
    flex: 1,
  },

  // ── Spots Bar ──────────────────────────────────────────────────────
  spotsBarContainer: {
    marginBottom: 20,
  },
  spotsBarTrack: {
    height: 6,
    backgroundColor: C.inputBg,
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 8,
  },
  spotsBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  spotsBarLabel: {
    fontSize: 13,
    color: C.textSecondary,
    fontWeight: '600',
  },

  // ── Join Button ────────────────────────────────────────────────────
  joinBtn: {
    backgroundColor: C.text,
    borderRadius: 999,
    paddingVertical: 16,
    alignItems: 'center',
  },
  joinBtnDisabled: {
    backgroundColor: C.border,
  },
  joinBtnText: {
    color: C.surface,
    fontSize: 16,
    fontWeight: '800',
  },
  joinBtnTextDisabled: {
    color: C.textMuted,
  },

  // ── Error Banners ──────────────────────────────────────────────────
  errorBanner: {
    backgroundColor: '#FEF0F3',
    padding: 16,
    borderRadius: 14,
    marginBottom: 24,
    borderWidth: 1.5,
    borderColor: C.error + '40',
  },
  errorText: {
    color: C.error,
    fontWeight: '600',
    textAlign: 'center',
    fontSize: 15,
    lineHeight: 21,
  },
  errorTextSm: {
    color: C.error,
    fontSize: 14,
    marginTop: 12,
    textAlign: 'center',
  },

  // ── Empty State ────────────────────────────────────────────────────
  emptyState: {
    alignItems: 'center',
    paddingVertical: 64,
    paddingHorizontal: 24,
  },
  emptyEmoji: {
    fontSize: 72,
    marginBottom: 20,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: C.text,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 16,
    color: C.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
  },
});
