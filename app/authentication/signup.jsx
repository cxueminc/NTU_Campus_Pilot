import { StyleSheet, Text, View, TextInput, TouchableOpacity, Alert, Image, ScrollView, KeyboardAvoidingView, Platform } from "react-native"
import { useState, useEffect } from "react"
import { useAuth } from "../../hooks/useAuth"
import { useRouter } from 'expo-router'

export default function SignUpScreen() {
    const { user, loading, signUp } = useAuth()
    const router = useRouter()
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [firstName, setFirstName] = useState("")
    const [lastName, setLastName] = useState("")

    // Clear form when user logs out
    useEffect(() => {
        if (!user) {
            setEmail("")
            setPassword("")
            setFirstName("")
            setLastName("")
        }
    }, [user])



    const handleSignUp = async () => {
        try {
            // Validate required fields for signup
            if (!firstName.trim() || !lastName.trim()) {
                Alert.alert("Missing Information", "Please enter your first name and last name.")
                return
            }
            await signUp(email, password, firstName, lastName)
            Alert.alert("Success", "Account created successfully!")
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
                case 'auth/invalid-email':
                    errorTitle = "Invalid Email"
                    errorMessage = "Please enter a valid email."
                    break
                case 'auth/weak-password':
                    errorTitle = "Weak Password"
                    errorMessage = "Please use at least 6 characters."
                    break
                case 'auth/email-already-in-use':
                    errorTitle = "Email Already In Use"
                    errorMessage = "An account with this email already exists. Please login instead."
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

    const navigateToSignIn = () => {
        router.push('/authentication/signin')
    }

    if (loading) {
        return (
            <View style={styles.container}>
                <Text>Loading...</Text>
            </View>
        )
    }

    // If user is logged in, redirect to map screen
    if (user) {
        router.replace('/screen/map/map')
        return null
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
                    
                    <Text style={styles.title}>Sign Up</Text>
                    
                    <TextInput
                        style={styles.input}
                        placeholder="First Name"
                        value={firstName}
                        onChangeText={setFirstName}
                        autoCapitalize="words"
                    />
                    
                    <TextInput
                        style={styles.input}
                        placeholder="Last Name"
                        value={lastName}
                        onChangeText={setLastName}
                        autoCapitalize="words"
                    />
                    
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
                    
                    <TouchableOpacity style={styles.button} onPress={handleSignUp}>
                        <Text style={styles.buttonText}>Sign Up</Text>
                    </TouchableOpacity>
                    
                    <TouchableOpacity onPress={navigateToSignIn}>
                        <Text style={styles.switchText}>
                            Have an account? Sign In
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
