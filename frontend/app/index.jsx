import { useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../hooks/useClerkAuth';

export default function Index() {
    const { user, loading, unverifiedUser } = useAuth();
    const router = useRouter();

    useEffect(() => {
        console.log('Index: loading =', loading, 'user =', user ? 'verified user' : 'no user', 'unverifiedUser =', unverifiedUser ? 'unverified user exists' : 'no unverified user');
        
        if (!loading) {
            // Use setTimeout to ensure navigation happens after render
            setTimeout(() => {
                if (user) {
                    console.log('Index: Redirecting verified user to chat screen');
                    router.replace('/screen/chat/chat');
                } else if (unverifiedUser) {
                    console.log('Index: Redirecting unverified user to Clerk verification screen');
                    router.replace('/authentication/clerk-email-verification');
                } else {
                    console.log('Index: Redirecting to sign in screen');
                    router.replace('/authentication/signin');
                }
            }, 100); // Small delay to ensure smooth navigation
        }
    }, [user, loading, unverifiedUser, router]);

    // Show loading screen while checking auth state
    if (loading) {
        return (
            <View style={styles.loadingContainer}>
                <Text style={styles.appTitle}>NTU Campus Pilot</Text>
                <ActivityIndicator size="large" color="#007AFF" style={styles.spinner} />
                <Text style={styles.loadingText}>Loading...</Text>
            </View>
        );
    }

    return null; // This component doesn't render anything
}

const styles = StyleSheet.create({
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f5f5f5',
        paddingHorizontal: 20,
    },
    appTitle: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#333',
        marginBottom: 30,
        textAlign: 'center',
    },
    spinner: {
        marginBottom: 20,
    },
    loadingText: {
        fontSize: 16,
        color: '#666',
        textAlign: 'center',
    },
});