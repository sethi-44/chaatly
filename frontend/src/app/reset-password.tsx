import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, ActivityIndicator, Platform } from 'react-native';
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
  input: '#F7F7F9',
  inputBorder: '#EBEBEB',
  error: '#E31C5F',
  success: '#00A699',
};

export default function ResetPasswordScreen() {
  const { token } = useLocalSearchParams<{ token?: string }>();
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  if (!token) {
    return (
      <View style={styles.container}>
        <Animated.View entering={FadeInDown.duration(600)} style={styles.card}>
          <Text style={styles.emoji}>🔗</Text>
          <Text style={[styles.message, { color: C.error }]}>Invalid password reset link.</Text>
          <TouchableOpacity onPress={() => router.replace('/')} activeOpacity={0.7}>
            <Text style={styles.link}>Go back</Text>
          </TouchableOpacity>
        </Animated.View>
      </View>
    );
  }

  const handleReset = async () => {
    if (password.length < 8) {
      setStatus('error');
      setMessage('Password must be at least 8 characters');
      return;
    }

    setStatus('loading');
    try {
      await axios.post(`${API_URL}/reset-password`, { token, new_password: password });
      setStatus('success');
      setMessage('Password has been successfully reset!');
    } catch (err: any) {
      setStatus('error');
      setMessage(err.response?.data?.detail || 'Failed to reset password');
    }
  };

  return (
    <View style={styles.container}>
      <Animated.View entering={FadeInDown.duration(600)} style={styles.card}>
        <Text style={styles.title}>Reset Password</Text>
        <Text style={styles.subtitle}>Enter your new password below</Text>

        {status === 'success' ? (
          <View style={styles.statusContainer}>
            <View style={styles.successIconWrap}>
              <Text style={styles.emoji}>✅</Text>
            </View>
            <Text style={[styles.statusMessage, { color: C.success }]}>{message}</Text>
            <TouchableOpacity
              style={styles.btn}
              onPress={() => router.replace('/')}
              activeOpacity={0.85}
            >
              <Text style={styles.btnText}>Go to Login</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            {status === 'error' && (
              <View style={styles.errorBanner}>
                <Text style={styles.errorText}>{message}</Text>
              </View>
            )}

            <View style={styles.inputWrapper}>
              <Text style={styles.inputLabel}>New Password</Text>
              <TextInput
                style={[
                  styles.input,
                  status === 'error' && { borderColor: C.error },
                ]}
                placeholder="At least 8 characters"
                placeholderTextColor={C.textSecondary}
                secureTextEntry
                value={password}
                onChangeText={(text) => {
                  setPassword(text);
                  if (status === 'error') {
                    setStatus('idle');
                    setMessage('');
                  }
                }}
                autoCapitalize="none"
              />
            </View>

            <TouchableOpacity
              style={[styles.btn, status === 'loading' && { opacity: 0.7 }]}
              onPress={handleReset}
              disabled={status === 'loading'}
              activeOpacity={0.85}
            >
              {status === 'loading' ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.btnText}>Reset Password</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity onPress={() => router.replace('/')} activeOpacity={0.7}>
              <Text style={styles.link}>← Back to login</Text>
            </TouchableOpacity>
          </>
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
    padding: 32,
    width: '100%',
    maxWidth: 400,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 24,
    elevation: 6,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: C.text,
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    color: C.textSecondary,
    textAlign: 'center',
    marginBottom: 28,
  },
  inputWrapper: {
    marginBottom: 24,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: C.text,
    marginBottom: 8,
    letterSpacing: 0.2,
  },
  input: {
    backgroundColor: C.input,
    borderWidth: 2,
    borderColor: C.inputBorder,
    borderRadius: 16,
    paddingHorizontal: 18,
    height: 64,
    color: C.text,
    fontSize: 16,
  },
  btn: {
    backgroundColor: C.primary,
    paddingVertical: 18,
    paddingHorizontal: 32,
    borderRadius: 999,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 56,
  },
  btnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  errorBanner: {
    backgroundColor: '#FFF0F3',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#FDDDE6',
  },
  errorText: {
    fontSize: 14,
    color: C.error,
    textAlign: 'center',
    fontWeight: '500',
    lineHeight: 20,
  },
  message: {
    fontSize: 15,
    textAlign: 'center',
    fontWeight: '500',
    lineHeight: 22,
  },
  statusMessage: {
    fontSize: 16,
    textAlign: 'center',
    fontWeight: '600',
    lineHeight: 24,
    marginBottom: 28,
  },
  link: {
    marginTop: 24,
    fontSize: 15,
    color: C.primary,
    fontWeight: '600',
    textAlign: 'center',
  },
  statusContainer: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  successIconWrap: {
    marginBottom: 16,
  },
  emoji: {
    fontSize: 48,
    marginBottom: 12,
    textAlign: 'center',
  },
});
