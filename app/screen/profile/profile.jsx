import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useAuth } from '../../../hooks/useAuth';
import { useRouter } from 'expo-router';
import { ActivityIndicator } from 'react-native';

export default function ProfileScreen() {
    const { user, loading, logout } = useAuth();
    const router = useRouter();

    if (loading) {
        return (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                <ActivityIndicator size="large" color="#007AFF" />
                <Text style={{ marginTop: 16, fontSize: 18 }}>Loading...</Text>
            </View>
        );
    }

    const handleLogout = async () => {
        try {
            await logout();
            router.replace('/authentication/signin');
        } catch (error) {
            console.error('Logout error:', error);
        }
    };

    const goToChangePwd = () => {
        router.push('/screen/profile/changepwd');
    };

    return (
        <ScrollView style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.subtitle}>
                    Welcome! {(user?.displayName || '').toUpperCase()}
                </Text>
            </View>

            <View style={styles.profileSection}>
                <Text style={styles.sectionTitle}>Account Information</Text>
                
                <View style={styles.infoRow}>
                    <Text style={styles.label}>Email:</Text>
                    <Text style={styles.value}>{user?.email}</Text>
                </View>
                
                <View style={styles.infoRow}>
                    <Text style={styles.label}>Display Name:</Text>
                    <Text style={styles.value}>{user?.displayName || 'Not set'}</Text>
                </View>
                
                <View style={styles.infoRow}>
                    <Text style={styles.label}>Email Verified:</Text>
                    <Text style={styles.value}>{user?.emailVerified ? 'Yes' : 'No'}</Text>
                </View>
                
                <View style={styles.infoRow}>
                    <Text style={styles.label}>User ID:</Text>
                    <Text style={styles.value}>{user?.uid}</Text>
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
