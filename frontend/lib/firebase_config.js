// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { initializeAuth, getReactNativePersistence } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import AsyncStorage from '@react-native-async-storage/async-storage';
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBHTZO1o-Xn82d8ybj5erVi9aGom2dRuRU",
  authDomain: "ntu-navigation-application.firebaseapp.com",
  projectId: "ntu-navigation-application",
  storageBucket: "ntu-navigation-application.firebasestorage.app",
  messagingSenderId: "956939024809",
  appId: "1:956939024809:web:2f76f07cf363ce9cc62cb8"
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);

// Initialize Auth with AsyncStorage persistence for React Native
export const auth = initializeAuth(app, {
  persistence: getReactNativePersistence(AsyncStorage)
});

// Initialize Firestore
export const db = getFirestore(app);