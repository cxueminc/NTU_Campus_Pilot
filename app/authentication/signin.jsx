import { StyleSheet, Text, View, TextInput, TouchableOpacity, Alert, Image, ScrollView, KeyboardAvoidingView, Platform } from "react-native"
import { useState, useEffect } from "react"
import { useAuth } from "../../hooks/useAuth"
import { useRouter } from 'expo-router'
import { sendPasswordResetEmail } from "firebase/auth";
import { auth } from '../../lib/firebase_config';

export default function SignInScreen() {
    const { user, loading, signIn } = useAuth()
    const router = useRouter()
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")

    // Clear form when user logs out
    useEffect(() => {
        if (!user) {
            setEmail("")
            setPassword("")
        }
    }, [user])

    const handleSignIn = async () => {
        try {
            await signIn(email, password)
            router.replace('/screen/map/map')
        } catch (error) {
            let errorMessage = "An error occurred. Please try again."
            let errorTitle = "Error"
            
            // Handle specific Firebase Auth errors
            switch (error.code) {
                case 'auth/missing-email':
                    errorTitle = "Missing Email"
                    errorMessage = "Please enter your email."
                    break
                case 'auth/missing-password':
                    errorTitle = "Missing Password"
                    errorMessage = "Please enter your password."
                    break
                case 'auth/user-not-found':
                    errorTitle = "Account Not Found"
                    errorMessage = "Please check your email or create a new account."
                    break
                case 'auth/wrong-password':
                    errorTitle = "Incorrect Password"
                    errorMessage = "Please try again."
                    break
                case 'auth/invalid-credential':
                    errorTitle = "Invalid Email/Password"
                    errorMessage = "Please check your credentials and try again."
                    break
                case 'auth/invalid-email':
                    errorTitle = "Invalid Email"
                    errorMessage = "Please enter a valid email."
                    break
                case 'auth/too-many-requests':
                    errorTitle = "Too Many Requests"
                    errorMessage = "Too many failed attempts. Please try again later."
                    break
                case 'auth/network-request-failed':
                    errorTitle = "Network Error"
                    errorMessage = "Please check your internet connection."
                    break
                default:
                    errorMessage = error.message || "An error occurred. Please try again."
            }
            
            Alert.alert(errorTitle, errorMessage)
        }
    }

    const navigateToSignUp = () => {
        router.push('/authentication/signup')
    }

    const handleForgotPassword = async () => {
        if (!email) {
            Alert.alert("Error", "Please enter your email to reset your password.")
            return
        }
        try {
            await sendPasswordResetEmail(auth, email)
            Alert.alert("Success", "Password reset email sent. Please check your inbox.")
        } catch (error) {
            let errorMessage = "An error occurred. Please try again."
            switch (error.code) {
                case 'auth/user-not-found':
                    errorMessage = "No account found with this email."
                    break
                case 'auth/invalid-email':
                    errorMessage = "Please enter a valid email address."
                    break
                default:
                    errorMessage = error.message || "An error occurred. Please try again."
            }
            Alert.alert("Error", errorMessage)
        }
    }

    useEffect(() => {
        // If user is logged in, redirect to map screen
        if (user) {
            router.replace('/screen/map/map')
        }
    }, [user])

    if (loading) {
        return (
            <View style={styles.container}>
                <Text>Loading...</Text>
            </View>
        )
    }

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
                    
                    <Text style={styles.title}>Sign In</Text>
                    
                    <TextInput
                        style={styles.input}
                        placeholder="Email"
                        value={email}
                        onChangeText={setEmail}
                        keyboardType="email-address"
                        autoCapitalize="none"
                    />
                    
                    <TextInput
                        style={styles.input}
                        placeholder="Password"
                        value={password}
                        onChangeText={setPassword}
                        secureTextEntry
                    />
                    
                    <TouchableOpacity style={[styles.button, { marginBottom: 25}]} onPress={handleSignIn}>
                        <Text style={styles.buttonText}>Sign In</Text>
                    </TouchableOpacity>
                    
                    <TouchableOpacity onPress={navigateToSignUp}>
                        <Text style={[styles.switchText, { marginBottom: 15 }]}>
                            Need an account? Sign Up
                        </Text>
                    </TouchableOpacity>

                    <TouchableOpacity onPress={() => router.push("/authentication/forgotpwd")}>
  <                     Text style={{ color: "#007AFF", marginBottom: 15 }}>
                            Forgot password?
                        </Text>
                    </TouchableOpacity>
                </View>
            </ScrollView>
        </KeyboardAvoidingView>
    )
}

const styles = StyleSheet.create({
    keyboardAvoidingView: {
        flex: 1,
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
        marginBottom: 30,
        color: '#333'
    },
    input: {
        width: '100%',
        height: 50,
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        paddingHorizontal: 15,
        marginBottom: 15,
        backgroundColor: 'white'
    },
    button: {
        width: '100%',
        height: 50,
        backgroundColor: '#007AFF',
        borderRadius: 8,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 15
    },
    buttonText: {
        color: 'white',
        fontSize: 16,
        fontWeight: 'bold'
    },
    switchText: {
        color: '#007AFF',
        fontSize: 14
    }
})
