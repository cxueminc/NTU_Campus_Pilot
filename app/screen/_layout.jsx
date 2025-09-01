import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function ScreenLayout() {
    return (
        <Tabs screenOptions={{ headerShown: false }}>

            <Tabs.Screen 
                name="map" 
                options={{
                    title: "Map", 
                    tabBarIcon: ({color, size}) => (
                        <Ionicons name="map-outline" size={size} color={color} />
                    ),
                }} 
            />

            <Tabs.Screen
                name="profile"
                options={{
                    title: "Profile",
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="person-outline" size={size} color={color} />
                    ),
                }}
            />
        </Tabs>
    );
}
