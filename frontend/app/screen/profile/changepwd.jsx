import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { useUser, useSignIn } from '@clerk/clerk-expo';

export default function ChangePwdScreen() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { user } = useUser();
  const { signIn } = useSignIn();

  let errorName = "Request Failed";

  // Button should be disabled unless all fields are filled, passwords match, and length >= 8
  const isButtonDisabled =
    loading ||
    !currentPassword ||
    !newPassword ||
    !confirmPassword ||
    newPassword !== confirmPassword ||
    newPassword.length < 8;

  const handleChangePassword = async () => {

    try {
      setLoading(true);

      await user.updatePassword({
        currentPassword,
        newPassword,
      });

      Alert.alert("Success", "Password changed successfully!");
      router.back();

    } catch (error) {
      console.log("changePassword ERR:", error);
      let errorMessage = "Something went wrong. Please try again.";

      if (error.errors && error.errors.length > 0) {
        errorMessage = error.errors[0].message;
      }

      Alert.alert("Request Failed", errorMessage);
    } finally {
      setLoading(false);
    }
  };


  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView keyboardShouldPersistTaps="always" contentContainerStyle={styles.container}>
        <Text style={styles.title}>Change Password</Text>
        <TextInput
          style={styles.input}
          placeholder="Current Password"
          secureTextEntry
          value={currentPassword}
          onChangeText={setCurrentPassword}
        />
        <TextInput
          style={styles.input}
          placeholder="New Password"
          secureTextEntry
          value={newPassword}
          onChangeText={setNewPassword}
        />
        <TextInput
          style={styles.input}
          placeholder="Confirm New Password"
          secureTextEntry
          value={confirmPassword}
          onChangeText={setConfirmPassword}
        />
        <TouchableOpacity
          style={[styles.button, isButtonDisabled ? { backgroundColor: '#cccccc' } : { backgroundColor: '#007AFF' }]
          }
          onPress={handleChangePassword}
          disabled={isButtonDisabled}
        >
          <Text style={styles.buttonText}>{loading ? 'Changing...' : 'Change Password'}</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  backButton: {
    position: 'absolute',
    top: 40,
    left: 20,
    zIndex:1,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 30,
    color: '#333',
  },
  input: {
    width: '100%',
    height: 50,
    borderColor: '#ccc',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 15,
    marginBottom: 20,
    backgroundColor: '#fff',
  },
  button: {
    backgroundColor: '#007AFF',
    paddingVertical: 15,
    paddingHorizontal: 40,
    borderRadius: 8,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
