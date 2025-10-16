import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Alert,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from "react-native";
import { useRouter, useLocalSearchParams } from "expo-router";
import { useSignIn, useClerk } from "@clerk/clerk-expo";

export default function ResetPasswordVerificationScreen() {
  const router = useRouter();
  const { email } = useLocalSearchParams(); // comes from forgotpwd.jsx
  const { signIn, isLoaded } = useSignIn();
  const { setActive } = useClerk();

  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);

  const handleVerifyAndReset = async () => {
    if (!code.trim() || !newPassword.trim()) {
      Alert.alert("Missing Info", "Please enter the code and a new password.");
      return;
    }
    if (newPassword.length < 8) {
      Alert.alert("Weak Password", "Password must be at least 8 characters.");
      return;
    }
    if (!isLoaded) return;

    setLoading(true);
    try {
      // Step 1: verify the code
      const attempt = await signIn.attemptFirstFactor({
        strategy: "reset_password_email_code",
        code,
      });

      if (attempt.status !== "needs_new_password") {
        throw new Error("Invalid or expired code.");
      }

      // Step 2: set the new password
      const result = await signIn.resetPassword({ password: newPassword });

      if (result.status === "complete") {
        // Step 3: optionally auto-sign-in the user
        await setActive({ session: result.createdSessionId });
        Alert.alert("Success", "Your password has been reset!");
        router.replace("/authentication/signin");
      } else {
        throw new Error("Password reset not completed. Try again.");
      }
    } catch (error) {
      console.error("Reset verification error:", error);
      let msg = error.message || "Failed to reset password. Try again.";
      if (error.errors && error.errors[0]) msg = error.errors[0].message;
      Alert.alert("Error", msg);
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (!email) {
      Alert.alert("Error", "Email is missing.");
      return;
    }
    if (!isLoaded) return;
    setResending(true);
    try {
      await signIn.create({ strategy: "reset_password_email_code", identifier: email });
      Alert.alert("Success", "A new verification code has been sent to your email.");
    } catch (error) {
      Alert.alert("Error", error.message || "Failed to resend code.");
    } finally {
      setResending(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.keyboardAvoidingView}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContainer}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.container}>
          <Text style={styles.title}>Enter Verification Code</Text>
          <Text style={styles.subtitle}>
            A 6-digit code was sent to {email || "your NTU email"}.
          </Text>

          <TextInput
            style={styles.input}
            placeholder="6-digit code"
            keyboardType="number-pad"
            value={code}
            onChangeText={setCode}
            maxLength={6}
          />

          <TextInput
            style={styles.input}
            placeholder="New Password"
            secureTextEntry
            value={newPassword}
            onChangeText={setNewPassword}
          />

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleVerifyAndReset}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={styles.buttonText}>Reset Password</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, { backgroundColor: "#FF9800", marginTop: 10 }]}
            onPress={handleResendCode}
            disabled={resending}
          >
            {resending ? (
              <Text style={styles.buttonText}>Resending...</Text>
            ) : (
              <Text style={styles.buttonText}>Resend Code</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity onPress={() => router.replace("/authentication/signin")}>
            <Text style={styles.linkText}>Back to Sign In</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  keyboardAvoidingView: { flex: 1, backgroundColor: "#f5f5f5" },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  container: { width: "100%", alignItems: "center" },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#333",
    marginBottom: 10,
    textAlign: "center",
  },
  subtitle: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
    marginBottom: 25,
  },
  input: {
    width: "100%",
    height: 50,
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    paddingHorizontal: 15,
    marginBottom: 15,
    backgroundColor: "white",
  },
  button: {
    width: "100%",
    height: 50,
    backgroundColor: "#007AFF",
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 15,
  },
  buttonDisabled: { backgroundColor: "#ccc" },
  buttonText: { color: "white", fontSize: 16, fontWeight: "bold" },
  linkText: { color: "#007AFF", fontSize: 14 },
});
