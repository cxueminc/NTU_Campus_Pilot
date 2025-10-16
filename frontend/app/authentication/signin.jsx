import { StyleSheet, Text, View, TextInput, TouchableOpacity, Alert, Image, ScrollView, KeyboardAvoidingView, Platform } from "react-native"
import { useState, useEffect } from "react"
import { useAuth } from "../../hooks/useClerkAuth"
import { useRouter } from 'expo-router'

export default function SignInScreen() {
    const { user, loading, signIn } = useAuth();
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    // Clear form when user logs out
    useEffect(() => {
        if (!user) {
            setEmail("");
            setPassword("");
        }
    }, [user]);

    const handleSignIn = async () => {
        try {
            const result = await signIn(email.trim(), password);
            router.replace('/screen/chat/chat');
        } 
        catch (error) {
            console.error("Sign-in error:", error);

            let errorMessage = error.message || "An error occurred. Please try again.";
            let errorTitle = "Error";
            
            // Handle email verification error specifically
            if (errorMessage.includes('verify your email')) {
                errorTitle = "Please Verify Your Email First";
                errorMessage = "Check your NTU inbox for the verification email and complete verification before signing in.";
            }
            else if (errorMessage.includes('Incorrect password')){
                errorTitle = "Incorrect Password";
            }
            else if (errorMessage.includes('No account found')){
                errorTitle = "No Account Found";
            }
            
            Alert.alert(errorTitle, errorMessage);
        }
    }

    const navigateToSignUp = () => {
        router.push('/authentication/signup');
    }


    useEffect(() => {
        // If user is logged in, redirect to map screen
        if (user) {
            router.replace('/screen/chat/chat');
        }
    }, [user]);

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
                        <Text style={{ color: "#007AFF", marginBottom: 15 }}>
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
