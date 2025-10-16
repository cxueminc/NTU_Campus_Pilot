import { useState } from "react";
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  Alert, 
  StyleSheet, 
  Image, 
  ScrollView, 
  KeyboardAvoidingView, 
  Platform,
  ActivityIndicator 
} from "react-native";
import { useRouter } from 'expo-router';
import { useSignIn } from '@clerk/clerk-expo';

export default function ForgotPasswordScreen() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { signIn, isLoaded } = useSignIn();

  const handleResetPassword = async () => {
    if (!email) {
      Alert.alert("Input Required", "Please enter your email address.");
      return;
    }

    // Validate NTU email
    if (!email.endsWith('@e.ntu.edu.sg')) {
      Alert.alert("Invalid Email", "Please use your NTU email address (@e.ntu.edu.sg)");
      return;
    }

    if (!isLoaded) {
      return;
    }

    setLoading(true);
    
    try {
      // Use Clerk's password reset functionality
      await signIn.create({
        strategy: 'reset_password_email_code',
        identifier: email,
      });

      Alert.alert(
        "Reset Email Sent! 📧", 
        `A password reset code has been sent to ${email}. Please check your email and enter the code to reset your password.`,
        [
          {
            text: "Enter Reset Code",
            onPress: () => router.push({
              pathname: '/authentication/reset-password-verification',
              params: { email }
            })
          }
        ]
      );
    } catch (error) {
      console.error('Password reset error:', error);
      let errorMessage = "An error occurred. Please try again.";
      
      if (error.errors) {
        const firstError = error.errors[0];
        switch (firstError.code) {
          case 'form_identifier_not_found':
            errorMessage = "No account found with this email address.";
            break;
          case 'form_param_format_invalid':
            errorMessage = "Please enter a valid email address.";
            break;
          default:
            errorMessage = firstError.message || errorMessage;
        }
      }
      
      Alert.alert("Error", errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const navigateToSignIn = () => {
    router.replace('/authentication/signin');
  };

  return (
    <KeyboardAvoidingView 
      style={styles.keyboardAvoidingView}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView 
        contentContainerStyle={styles.scrollContainer}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.container}>
          {/* Logo Section */}
          <View style={styles.logoContainer}>
            <Image 
              source={require('../../assets/NTU_Logo.webp')} 
              style={styles.logo}
              resizeMode="contain"
            />
            <Text style={styles.appName}>NTU Campus Pilot</Text>
          </View>

          {/* Title */}
          <Text style={styles.title}>Reset Password</Text>
          <Text style={styles.subtitle}>
            Enter your NTU email address and we'll send you instructions to reset your password.
          </Text>

          {/* Email Input */}
          <TextInput
            style={styles.input}
            placeholder="Enter your NTU email"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            editable={!loading}
          />

          {/* Reset Button */}
          <TouchableOpacity 
            style={[styles.button, loading && styles.buttonDisabled]} 
            onPress={handleResetPassword}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={styles.buttonText}>Send Reset Instructions</Text>
            )}
          </TouchableOpacity>

          {/* Back to Sign In */}
          <TouchableOpacity onPress={navigateToSignIn} disabled={loading}>
            <Text style={styles.switchText}>Remember your password? Sign In</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  keyboardAvoidingView: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  container: {
    width: '100%',
    alignItems: 'center',
    backgroundColor: '#f5f5f5'
  },
  logoContainer: {
    alignItems: 'center',
    marginTop: -80,
    marginBottom: 40
  },
  logo: {
    width: 250,
    height: 250,
    marginBottom: 10
  },
  appName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center'
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
    textAlign: 'center'
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 30,
    paddingHorizontal: 20,
    lineHeight: 22
  },
  input: {
    width: '100%',
    height: 50,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 15,
    marginBottom: 15,
    backgroundColor: 'white',
    fontSize: 16
  },
  button: {
    width: '100%',
    height: 50,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20
  },
  buttonDisabled: {
    backgroundColor: '#ccc'
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold'
  },
  switchText: {
    color: '#007AFF',
    fontSize: 14,
    textAlign: 'center'
  }
});
