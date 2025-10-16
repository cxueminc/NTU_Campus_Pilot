import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  Alert, 
  StyleSheet, 
  ScrollView,
  TextInput 
} from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../../hooks/useClerkAuth';

export default function ClerkEmailVerificationScreen() {
  const router = useRouter();
  const { unverifiedUser, verifyEmail, resendVerificationEmail } = useAuth();
  const [verificationCode, setVerificationCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [hasWaited, setHasWaited] = useState(false);

  // Handle navigation when no unverified user - but wait a moment for state to load
  useEffect(() => {
    const timer = setTimeout(() => {
      setHasWaited(true);
    }, 2000); // Wait 2 seconds for auth state to stabilize

    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (hasWaited && !unverifiedUser) {
      console.log('No unverified user found after waiting, redirecting to sign-in');
      router.replace('/authentication/signin');
    }
  }, [hasWaited, unverifiedUser, router]);

  const handleVerifyEmail = async () => {
    if (!verificationCode.trim()) {
      Alert.alert("Code Required", "Please enter the verification code from your email.");
      return;
    }

    try {
      setIsVerifying(true);
      console.log('Starting email verification process...');
      
      // Verify email with Clerk
      await verifyEmail(verificationCode);
      
      console.log('Email verification completed successfully');
      
      // Navigate directly to chat screen without showing success popup
      console.log('Navigating directly to chat screen...');
      router.replace('/screen/chat/chat');
      
    } catch (error) {
      console.error('Verification failed:', error);
      
      let errorMessage = "Verification failed. Please check your code and try again.";
      if (error.message.includes('incorrect')) {
        errorMessage = "The verification code is incorrect. Please check your email and try again.";
      } else if (error.message.includes('expired')) {
        errorMessage = "The verification code has expired. Please request a new one.";
      }
      
      Alert.alert("Verification Failed", errorMessage);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleResendCode = async () => {
    try {
      setIsResending(true);
      await resendVerificationEmail();
      
      Alert.alert(
        "New Code Sent! 📧",
        "A new verification code has been sent to your NTU email address. Please check your inbox."
      );
      
      setVerificationCode(''); // Clear the input
    } catch (error) {
      console.error('Resend failed:', error);
      Alert.alert("Error", "Failed to resend verification code. Please try again.");
    } finally {
      setIsResending(false);
    }
  };

  // Show loading while waiting for auth state to stabilize
  if (!hasWaited || !unverifiedUser) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading verification screen...</Text>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.logoContainer}>
        <Text style={styles.appTitle}>NTU Campus Pilot</Text>
      </View>

      <View style={styles.content}>
        <Text style={styles.emoji}>📧</Text>
        <Text style={styles.title}>Verify Your Email</Text>
        
        <Text style={styles.message}>
          We've sent a verification code to:
        </Text>
        
        <Text style={styles.email}>
          {unverifiedUser?.emailAddresses?.[0]?.emailAddress || unverifiedUser?.emailAddress}
        </Text>
        
        <Text style={styles.instructions}>
          Please enter the 6-digit verification code from your email below.
        </Text>

        <View style={styles.helpBox}>
          <Text style={styles.helpTitle}>📍 Can't find the email?</Text>
          <Text style={styles.helpText}>
            • Check your spam/junk folder{'\n'}
            • Make sure the email address is correct{'\n'}
            • Wait a few minutes for delivery{'\n'}
            • Codes are valid for 10 minutes{'\n'}
            • Use the "Resend Code" button for a fresh code
          </Text>
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>Verification Code</Text>
          <TextInput
            style={styles.codeInput}
            value={verificationCode}
            onChangeText={setVerificationCode}
            placeholder="Enter 6-digit code"
            maxLength={6}
            keyboardType="number-pad"
            autoCapitalize="none"
            autoCorrect={false}
          />
        </View>

        {/* Action Buttons */}
        <TouchableOpacity 
          style={[
            styles.button, 
            styles.primaryButton,
            (isVerifying || !verificationCode.trim()) && styles.disabledButton
          ]} 
          onPress={handleVerifyEmail}
          disabled={isVerifying || !verificationCode.trim()}
        >
          <Text style={[
            styles.primaryButtonText,
            (isVerifying || !verificationCode.trim()) && styles.disabledButtonText
          ]}>
            {isVerifying ? "🔄 Verifying..." : "Verify Email"}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.button, styles.secondaryButton]} 
          onPress={handleResendCode}
          disabled={isResending}
        >
          <Text style={styles.secondaryButtonText}>
            {isResending ? "Sending..." : "Resend Code"}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.button, styles.outlineButton]} 
          onPress={() => router.replace('/authentication/signin')}
        >
          <Text style={styles.outlineButtonText}>
            Back to Sign In
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: '#f5f5f5',
    paddingHorizontal: 20,
    paddingVertical: 40,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  appTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 10,
  },
  content: {
    alignItems: 'center',
    width: '100%',
  },
  emoji: {
    fontSize: 60,
    marginBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
    textAlign: 'center',
  },
  message: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 10,
  },
  email: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007AFF',
    textAlign: 'center',
    marginBottom: 20,
  },
  instructions: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 30,
    lineHeight: 22,
  },
  helpBox: {
    backgroundColor: '#e8f4f8',
    padding: 20,
    borderRadius: 12,
    marginBottom: 30,
    width: '100%',
  },
  helpTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c5aa0',
    marginBottom: 10,
  },
  helpText: {
    fontSize: 14,
    color: '#555',
    lineHeight: 20,
  },
  inputContainer: {
    width: '100%',
    marginBottom: 30,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  codeInput: {
    width: '100%',
    height: 50,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 15,
    fontSize: 18,
    backgroundColor: 'white',
    textAlign: 'center',
    letterSpacing: 3,
  },
  button: {
    width: '100%',
    height: 50,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  primaryButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  disabledButton: {
    backgroundColor: '#ccc',
  },
  disabledButtonText: {
    color: '#888',
  },
  secondaryButton: {
    backgroundColor: '#34C759',
  },
  secondaryButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  outlineButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#999',
  },
  outlineButtonText: {
    color: '#666',
    fontSize: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    paddingHorizontal: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 10,
  },
});