import { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, Alert, StyleSheet } from "react-native";
import { sendPasswordResetEmail } from "firebase/auth";
import { auth } from "../../lib/firebase_config";

export default function ForgotPasswordScreen() {
  const [email, setEmail] = useState("");

  const handleResetPassword = async () => {

    if (!email) {
      Alert.alert("Input Required", "Please enter your email address.");
      return;
    }

    try {
       console.log("Attempting to send reset email to:", email);
      await sendPasswordResetEmail(auth, email);
      console.log("Password reset email sent successfully to:", email);
      Alert.alert(
        "Check your email",
        `If an account exists for ${email}, you'll receive reset instructions.`
      );
    } 
    catch (error) {
      Alert.alert("Error", error.message);
    }

  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Forgot Password</Text>
      <TextInput
        style={styles.input}
        placeholder="Enter your email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
      />
      <TouchableOpacity style={styles.button} onPress={handleResetPassword}>
        <Text style={styles.buttonText}>Send Reset Email</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 20 },
  title: { fontSize: 24, fontWeight: "bold", marginBottom: 20 },
  input: { borderWidth: 1, padding: 12, borderRadius: 8, marginBottom: 15 },
  button: { backgroundColor: "#007AFF", padding: 15, borderRadius: 8 },
  buttonText: { color: "white", fontWeight: "bold", textAlign: "center" },
});
