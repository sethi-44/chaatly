import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Platform } from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import axios from 'axios';
import Animated, { FadeInDown } from 'react-native-reanimated';

const API_URL = Platform.select({
  android: 'http://10.0.2.2:8000',
  default: 'http://localhost:8000',
});

const C = {
  bg: '#FFFDF9',
  card: '#FFFFFF',
  primary: '#FF2D78',
  text: '#222222',
  textSecondary: '#717171',
  error: '#E31C5F',
  success: '#00A699',
};

export default function VerifyEmailScreen() {
  const { token } = useLocalSearchParams<{ token?: string }>();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('No token provided');
      return;
    }

    axios.post(`${API_URL}/supabase/verify-email`, { token })
      .then((res) => {
        setStatus('success');
        setMessage(res.data.message || 'Email verified successfully!');
      })
      .catch((err) => {
        setStatus('error');
        const detail = err.response?.data?.detail;
        setMessage(Array.isArray(detail) ? detail[0].msg : (detail || 'Failed to verify email'));
      });
  }, [token]);

  return (
    <View style={styles.container}>
      <Animated.View entering={FadeInDown.duration(600)} style={styles.card}>
        <Text style={styles.title}>Email Verification</Text>

        {status === 'loading' && (
          <View style={styles.statusContainer}>
            <ActivityIndicator size="large" color={C.primary} />
            <Text style={styles.message}>Verifying your email…</Text>
          </View>
        )}

        {status === 'success' && (
          <View style={styles.statusContainer}>
            <Text style={styles.emoji}>✅</Text>
            <Text style={[styles.message, { color: C.success }]}>{message}</Text>
            <Text style={styles.link} onPress={() => router.replace('/')}>
              Go to Login
            </Text>
          </View>
        )}

        {status === 'error' && (
          <View style={styles.statusContainer}>
            <Text style={styles.emoji}>❌</Text>
            <Text style={[styles.message, { color: C.error }]}>{message}</Text>
            <Text style={[styles.link, { color: C.error }]} onPress={() => router.replace('/')}>
              Go back
            </Text>
          </View>
        )}
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: C.bg,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  card: {
    backgroundColor: C.card,
    borderRadius: 24,
    padding: 36,
    width: '100%',
    maxWidth: 400,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 24,
    elevation: 6,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: C.text,
    marginBottom: 28,
    letterSpacing: -0.3,
  },
  statusContainer: {
    alignItems: 'center',
    gap: 4,
  },
  message: {
    fontSize: 16,
    color: C.textSecondary,
    textAlign: 'center',
    marginTop: 16,
    lineHeight: 24,
  },
  emoji: {
    fontSize: 48,
  },
  link: {
    marginTop: 24,
    fontSize: 16,
    color: C.primary,
    fontWeight: '600',
  },
});
