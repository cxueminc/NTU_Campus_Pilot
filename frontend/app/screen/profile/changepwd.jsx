  import { useState } from 'react';
  import { KeyboardAvoidingView, Platform, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView } from 'react-native';
  import { useRouter } from 'expo-router';
  import { auth } from '../../../lib/firebase_config';
  import { EmailAuthProvider, reauthenticateWithCredential, updatePassword} from 'firebase/auth';

  export default function ChangePwdScreen() {
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    let errorName = "Request Failed"; 

    const handleChangePassword = async () => {

      if (!currentPassword || !newPassword || !confirmPassword) {
        Alert.alert(errorName, 'Please fill in all fields.');
        return;
      }
      if (newPassword !== confirmPassword) {
        Alert.alert(errorName, 'New passwords do not match.');
        return;
      }

      if (newPassword.length < 6) {
        Alert.alert(errorName, 'New password must be at least 6 characters long.');
        return;
      }

      const user = auth.currentUser;
      if (!user || !user.email) {
        Alert.alert(errorName, 'You must be signed in to change your password.');
        return;
      }

      // Implement password change logic with your auth provider
      try {
        setLoading(true);

        const credential = EmailAuthProvider.credential(user.email, currentPassword);
        await reauthenticateWithCredential(user, credential);
        
        await updatePassword(user, newPassword);

        Alert.alert('Success', 'Password changed successfully!');
        router.back();
      }
      catch (error) {

        console.log('changePassword ERR:', error?.code, error?.message);

        let errorMessage = "Something went wrong. Please try again.";
        
        switch (error.code) {
          case 'auth/invalid-credential':
            errorMessage = "Current password is incorrect.";
            break;
          case 'auth/weak-password':
            errorMessage = "New password is too weak (min 6 characters).";
            break;
          case 'auth/too-many-requests':
            msg = 'Too many attempts. Please wait and try again.'; 
            break;
          case 'auth/requires-recent-login':
            errorMessage = "You need to re-authenticate to change your password.";
            break;
        }

        Alert.alert(errorName, errorMessage);
      }
      finally {
        setLoading(false);
      }
    };

    return (
      <KeyboardAvoidingView 
        style={{ flex: 1 }} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
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
            
            <TouchableOpacity style={styles.button} onPress={handleChangePassword}>
                <Text style={styles.buttonText}>Change Password</Text>
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
