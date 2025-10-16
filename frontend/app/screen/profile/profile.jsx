import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useAuth } from '../../../hooks/useClerkAuth';
import { useUser } from '@clerk/clerk-expo';
import { useRouter } from 'expo-router';
import { ActivityIndicator } from 'react-native';

export default function ProfileScreen() {

    const { logout } = useAuth();
    const { user, isLoaded } = useUser();
    const router = useRouter();

    // Debug: Log Clerk loaded state
    console.log('Clerk loaded:', isLoaded);
    // Debug: Log session persistence (user object)
    if (isLoaded) {
        if (user) {
            console.log('Session is persistent. User is signed in.');
            console.log('Logged in user info:', {
                id: user.id,
                firstName: user.firstName,
                lastName: user.lastName,
                email: user.primaryEmailAddress?.emailAddress,
                emailVerified: user.primaryEmailAddress?.verification?.status,
            });
        } else {
            console.log('No user is signed in. Session is not persistent or user is logged out.');
        }
    } else {
        console.log('Clerk is still loading.');
    }

    // Show loading if Clerk hasn't loaded yet
    if (!isLoaded) {
        return (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                <ActivityIndicator size="large" color="#007AFF" />
                <Text style={{ marginTop: 16, fontSize: 18 }}>Loading...</Text>
            </View>
        );
    }

    const handleLogout = async () => {
        try {
            if(Clerk.session) {
                await Clerk.session.end();
            }

            await logout();

            router.replace('/authentication/signin');
        }
        catch (error) {
            console.error('Logout error:', error);
        }
    };

    const goToChangePwd = () => {
        router.push('/screen/profile/changepwd');
    };

    // Get user information directly from Clerk with better fallbacks
    const firstName = user?.firstName || '';
    const lastName = user?.lastName || '';
    const displayName = firstName && lastName ? `${firstName} ${lastName}` : (firstName || lastName || 'Name not set');
    const email = user?.primaryEmailAddress?.emailAddress || user?.emailAddresses?.[0]?.emailAddress || 'Email not available';
    const emailVerified = user?.primaryEmailAddress?.verification?.status === 'verified' || 
                         user?.emailAddresses?.[0]?.verification?.status === 'verified';
    const userId = user?.id || 'User ID not available';

    return (
        <ScrollView style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.subtitle}>
                    Welcome! {displayName.toUpperCase()}
                </Text>
            </View>

            <View style={styles.profileSection}>
                <Text style={styles.sectionTitle}>Account Information</Text>
                <View style={styles.infoRow}>
                    <Text style={styles.label}>Email:</Text>
                    <Text style={styles.value}>{email}</Text>
                </View>
                <View style={styles.infoRow}>
                    <Text style={styles.label}>Display Name:</Text>
                    <Text style={styles.value}>{displayName}</Text>
                </View>
                <View style={styles.infoRow}>
                    <Text style={styles.label}>Email Verified:</Text>
                    <Text style={[styles.value, { color: emailVerified ? '#4CAF50' : '#FF5722' }]}>
                        {emailVerified ? 'Yes ✅' : 'No ❌'}
                    </Text>
                </View>
                <View style={styles.infoRow}>
                    <Text style={styles.label}>User ID:</Text>
                    <Text style={styles.value}>{userId}</Text>
                </View>
            </View>

            <View style={styles.settingsSection}>
                <Text style={styles.sectionTitle}>Settings</Text>
                
                <TouchableOpacity style={styles.settingButton}>
                    <Text style={styles.settingButtonText}>Edit Profile</Text>
                </TouchableOpacity>
                
                <TouchableOpacity style={styles.settingButton} onPress={goToChangePwd}>
                    <Text style={styles.settingButtonText}>Change Password</Text>
                </TouchableOpacity>
                
                <TouchableOpacity style={styles.settingButton}>
                    <Text style={styles.settingButtonText}>Privacy Settings</Text>
                </TouchableOpacity>
                
                <TouchableOpacity style={styles.settingButton}>
                    <Text style={styles.settingButtonText}>Help & Support</Text>
                </TouchableOpacity>
            </View>

            <View style={styles.buttonContainer}>
                <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
                    <Text style={styles.logoutButtonText}>Logout</Text>
                </TouchableOpacity>
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5'
    },
    header: {
        backgroundColor: '#007AFF',
        padding: 20,
        alignItems: 'center'
    },
    title: {
        fontSize: 28,
        fontWeight: 'bold',
        color: 'white',
        marginBottom: 10
    },
    subtitle: {
        fontSize: 18,
        color: 'white',
        opacity: 0.9
    },
    profileSection: {
        backgroundColor: 'white',
        margin: 20,
        padding: 20,
        borderRadius: 10,
        shadowColor: '#000',
        shadowOffset: {
            width: 0,
            height: 2,
        },
        shadowOpacity: 0.1,
        shadowRadius: 3.84,
        elevation: 5,
    },
    settingsSection: {
        backgroundColor: 'white',
        margin: 20,
        padding: 20,
        borderRadius: 10,
        shadowColor: '#000',
        shadowOffset: {
            width: 0,
            height: 2,
        },
        shadowOpacity: 0.1,
        shadowRadius: 3.84,
        elevation: 5,
    },
    sectionTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#333',
        marginBottom: 15
    },
    infoRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        paddingVertical: 10,
        borderBottomWidth: 1,
        borderBottomColor: '#f0f0f0'
    },
    label: {
        fontSize: 16,
        color: '#666',
        fontWeight: '500'
    },
    value: {
        fontSize: 16,
        color: '#333',
        fontWeight: '400'
    },
    settingButton: {
        backgroundColor: '#f8f9fa',
        padding: 15,
        borderRadius: 8,
        marginBottom: 10
    },
    settingButtonText: {
        fontSize: 16,
        color: '#333',
        fontWeight: '500'
    },
    buttonContainer: {
        margin: 20,
        gap: 15
    },
    logoutButton: {
        backgroundColor: '#FF3B30',
        padding: 15,
        borderRadius: 8,
        alignItems: 'center'
    },
    logoutButtonText: {
        color: 'white',
        fontSize: 16,
        fontWeight: 'bold'
    }
});
