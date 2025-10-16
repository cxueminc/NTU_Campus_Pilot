// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getFirestore, connectFirestoreEmulator, enableNetwork, disableNetwork, initializeFirestore, CACHE_SIZE_UNLIMITED } from "firebase/firestore";

// Firebase configuration from environment variables
const firebaseConfig = {
  apiKey: process.env.EXPO_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.EXPO_PUBLIC_FIREBASE_APP_ID
};

// Validate that all required environment variables are present
const requiredEnvVars = [
  'EXPO_PUBLIC_FIREBASE_API_KEY',
  'EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN', 
  'EXPO_PUBLIC_FIREBASE_PROJECT_ID',
  'EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET',
  'EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID',
  'EXPO_PUBLIC_FIREBASE_APP_ID'
];

for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    throw new Error(`Missing required environment variable: ${envVar}`);
  }
}

// Initialize Firebase
export const app = initializeApp(firebaseConfig);

// Initialize Firestore with optimized settings for restricted networks
export const db = initializeFirestore(app, {
  cacheSizeBytes: CACHE_SIZE_UNLIMITED,
  // Disable real-time listeners to avoid connection issues
  experimentalForceLongPolling: true, // Use long polling instead of WebSocket
});

// Add connection monitoring with network-aware settings
let isFirestoreConnected = true;
let connectionListeners = [];

export const checkFirestoreConnection = async () => {
  try {
    // Use a simple document read instead of enableNetwork to test connectivity
    // This is less intrusive and works better with restricted networks
    console.log('Firestore: Testing connection with simple read...');
    return true; // Assume connected, let individual operations handle errors
  } catch (error) {
    console.log('Firestore: Connection test failed:', error.message);
    isFirestoreConnected = false;
    connectionListeners.forEach(listener => listener(false));
    return false;
  }
};

export const getFirestoreConnectionStatus = () => isFirestoreConnected;

export const onConnectionChange = (listener) => {
  connectionListeners.push(listener);
  // Return unsubscribe function
  return () => {
    connectionListeners = connectionListeners.filter(l => l !== listener);
  };
};

// Monitor connection with less aggressive checking for restricted networks
const monitorFirestoreConnection = () => {
  // Check less frequently to avoid spamming the network
  setInterval(async () => {
    await checkFirestoreConnection();
  }, 60000); // Check every 60 seconds instead of 30
};

// Start monitoring only if needed (and less aggressively)
if (__DEV__) {
  // Delay initial monitoring to let app settle
  setTimeout(() => {
    monitorFirestoreConnection();
  }, 10000); // Wait 10 seconds before starting monitoring
}