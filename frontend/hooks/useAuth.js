import { useState, useEffect } from 'react';
import { 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged,
  updateProfile
} from 'firebase/auth';
import { doc, setDoc, getDoc } from 'firebase/firestore';
import { auth, db } from '../lib/firebase_config';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log('useAuth: Setting up auth state listener');
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      console.log('useAuth: Auth state changed, user =', user ? 'logged in' : 'not logged in');
      setUser(user);
      if (user) {
        // Fetch user profile data with better error handling
        try {
          // Add timeout to prevent hanging requests
          const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Request timeout')), 3000)
          );
          
          const userDocPromise = getDoc(doc(db, 'users', user.uid));
          const userDoc = await Promise.race([userDocPromise, timeoutPromise]);
          
          if (userDoc.exists()) {
            setUserProfile(userDoc.data());
          } 
          else {
            // If document doesn't exist, set userProfile to null
            setUserProfile(null);
          }
        }
        catch (error) {
          console.log('Firestore offline or timeout - continuing with basic auth data');
          // Don't fail the entire auth flow if Firestore is offline
          // User can still use the app with basic auth data
          setUserProfile(null);
        }
      }
      else {
        setUserProfile(null);
      }
      
      console.log('useAuth: Setting loading to false');
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const signIn = async (email, password) => {
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      return userCredential.user;
    } catch (error) {
      throw error;
    }
  };

  const signUp = async (email, password, firstName, lastName) => {
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      
      // Update display name in Firebase Auth
      await updateProfile(userCredential.user, {
        displayName: `${firstName} ${lastName}`
      });
      
      // Save user profile data to Firestore with error handling
      try {
        await setDoc(doc(db, 'users', userCredential.user.uid), {
          firstName,
          lastName,
          email,
          createdAt: new Date()
        });
      } catch (firestoreError) {
        console.error('Error saving to Firestore:', firestoreError);
        // Don't fail the signup if Firestore is offline
        // The user can still use the app with basic auth data
      }
      
      return userCredential.user;
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      await signOut(auth);
    } catch (error) {
      throw error;
    }
  };

  return {
    user,
    userProfile,
    loading,
    signIn,
    signUp,
    logout
  };
};
