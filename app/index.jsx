import { useEffect } from 'react';
import { useRouter } from 'expo-router';
import { useAuth } from '../hooks/useAuth';

export default function Index() {
    const { user, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        console.log('Index: loading =', loading, 'user =', user ? 'logged in' : 'not logged in');
        
        if (!loading) {
            if (user) {
                console.log('Index: Redirecting to chat screen');
                router.replace('/screen/chat/chat');
            } else {
                console.log('Index: Redirecting to sign in screen');
                router.replace('/authentication/signin');
            }
        }
    }, [user, loading, router]);

    // Show loading screen while checking auth state
    if (loading) {
        return null;
    }

    return null; // This component doesn't render anything
}