import { useState, useEffect } from 'react';
import { useUser, useSignUp, useSignIn, useClerk } from '@clerk/clerk-expo';
import { doc, setDoc, getDoc } from 'firebase/firestore';
import { db, checkFirestoreConnection, onConnectionChange } from '../lib/firebase_config'; // Keep Firestore for user data
import * as SecureStore from 'expo-secure-store';

export const useAuth = () => {
  const { user, isLoaded: userLoaded } = useUser();
  const { signUp, isLoaded: signUpLoaded } = useSignUp();
  const { signIn, isLoaded: signInLoaded } = useSignIn();
  const { signOut, setActive } = useClerk();
  
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [unverifiedUser, setUnverifiedUser] = useState(null);

  // Add timeout to prevent infinite loading
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (loading) {
        console.log('Loading timeout reached, stopping loading state');
        setLoading(false);
      }
    }, 3000); // Force stop loading after 3 seconds max

    return () => clearTimeout(timeout);
  }, [loading]);

  // Sync offline data when connection is restored (simplified)
  const syncOfflineData = async () => {
    try {
      const pendingData = await SecureStore.getItemAsync('pendingFirestoreUser');
      if (!pendingData) return;

      const userData = JSON.parse(pendingData);
      console.log('Firestore: Attempting to sync offline user data...');

      // Check if this is recent data (within last 24 hours)
      const timeDiff = Date.now() - userData.timestamp;
      if (timeDiff > 24 * 60 * 60 * 1000) {
        console.log('Firestore: Offline data too old, discarding');
        await SecureStore.deleteItemAsync('pendingFirestoreUser');
        return;
      }

      // Try to sync the data (without aggressive connection checking)
      const userDocRef = doc(db, 'users', userData.clerkId);
      
      // Just try the operation - if it fails, it fails quietly
      await setDoc(userDocRef, {
        email: userData.email,
        emailVerified: true,
        emailVerifiedAt: new Date(userData.timestamp),
        createdAt: new Date(userData.timestamp),
        clerkId: userData.clerkId,
        verificationMethod: 'clerk',
        syncedAt: new Date(),
      });

      console.log('Firestore: Offline user data synced successfully');
      
      // Clean up offline data
      await SecureStore.deleteItemAsync('pendingFirestoreUser');
      await SecureStore.deleteItemAsync('pendingUserData');

    } catch (error) {
      // Don't log errors aggressively - just note that sync will be retried later
      console.log('Firestore: Sync postponed, will retry later');
    }
  };

  // Monitor connection changes and sync when online (simplified)
  useEffect(() => {
    // Only try to sync offline data once on mount, don't monitor continuously
    const initializeOfflineSync = async () => {
      try {
        const pendingData = await SecureStore.getItemAsync('pendingFirestoreUser');
        if (pendingData) {
          console.log('Firestore: Found offline data, attempting sync...');
          await syncOfflineData();
        }
      } catch (error) {
        console.log('Firestore: Could not check for offline data:', error.message);
      }
    };

    // Reduce delay to make app feel faster
    const timer = setTimeout(initializeOfflineSync, 2000);
    return () => clearTimeout(timer);
  }, []);

  // Background function to fetch user profile without blocking UI
  const fetchUserProfileInBackground = async (userId) => {
    try {
      console.log('Fetching user profile in background...');
      const userDocRef = doc(db, 'users', userId);
      const userDoc = await getDoc(userDocRef);
      
      if (userDoc.exists()) {
        console.log('User profile found and loaded');
        setUserProfile(userDoc.data());
      } else {
        console.log('No user profile found in Firestore - user needs to complete signup process');
        setUserProfile(null);
        // Do NOT sign out Clerk user if Firestore profile is missing
      }
    } catch (error) {
      console.log('Background profile fetch failed:', error.message);
      setUserProfile(null);
    }
  };

  useEffect(() => {
    const handleUserChange = async () => {
      if (!userLoaded || !signUpLoaded) return;

      console.log('Clerk: State check - userLoaded:', userLoaded, 'signUpLoaded:', signUpLoaded);

      try {
        // Check if there's an active signup session (user just signed up)
        if (signUp && signUp.status === 'missing_requirements') {
          console.log('Clerk: Signup session active, user needs verification');
          setUserProfile(null);
          setUnverifiedUser(signUp); // Use signUp object as unverified user
          setLoading(false); // Stop loading immediately for signup flow
        }
        // Check for verified user
        else if (user && user.emailAddresses[0]?.verification?.status === 'verified') {
          console.log('Clerk: User verified, will fetch profile in background');
          
          // Set loading to false immediately, fetch profile in background
          setLoading(false);
          
          // Fetch user profile from Firestore in background (don't block UI)
          fetchUserProfileInBackground(user.id);
        }
        else {
          console.log('Clerk: No authenticated user, showing auth screens');
          setUserProfile(null);
          setUnverifiedUser(null);
          setLoading(false); // Stop loading immediately
        }
      } catch (error) {
        console.error('Error in auth state change:', error);
        setLoading(false); // Always stop loading on error
      }
    };

    handleUserChange();
  }, [user, userLoaded, signUpLoaded, signUp]);

  const signUpUser = async (email, password, firstName, lastName) => {
    try {
      console.log('Clerk: Starting signup process');
      
      // If there's already a user signed in, sign them out first
      if (user) {
        console.log('Clerk: User already signed in, signing out first');
        await signOut();
        // Wait a moment for the sign out to complete
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      // Validate NTU email
      if (!email.endsWith('@e.ntu.edu.sg')) {
        throw new Error('Please use your NTU email address (@e.ntu.edu.sg)');
      }

      // Create account with Clerk
      const result = await signUp.create({
        emailAddress: email,
        password: password,
        firstName: firstName,
        lastName: lastName,
      });

      console.log('Clerk: Account created, preparing email verification');

      // Prepare email verification
      await signUp.prepareEmailAddressVerification({ strategy: 'email_code' });
      
      console.log('Clerk: Email verification sent');

      // Store pending user data for later database save
      // We'll save to Firestore only after email verification
      try {
        await SecureStore.setItemAsync('pendingUserData', JSON.stringify({
          firstName,
          lastName,
          email,
          clerkId: result.id,
          createdAt: new Date().toISOString(),
        }));
      } catch (error) {
        console.log('Could not store pending user data:', error);
      }

      return result;
    } catch (error) {
      console.error('Clerk signup error:', error);
      
      // Handle "already signed in" error specifically
      if (error.message.includes('already signed in')) {
        console.log('Clerk: Handling already signed in error - clearing session');
        try {
          await signOut();
          // Wait and retry
          await new Promise(resolve => setTimeout(resolve, 1000));
          // Retry the signup
          return await signUp.create({
            emailAddress: email,
            password: password,
            firstName: firstName,
            lastName: lastName,
          });
        } catch (retryError) {
          console.error('Retry signup failed:', retryError);
          throw new Error('Please try signing up again. If the problem persists, try restarting the app.');
        }
      }
      
      throw error;
    }
  };

  const signInUser = async (email, password) => {
    try {
      console.log('Clerk: Starting signin process');
      
      const result = await signIn.create({
        identifier: email,
        password: password,
      });

      if (result.status === 'complete') {
        console.log('Clerk: Signin successful');

        await setActive({ session: result.createdSessionId });

        return result;
      } 
      else {
        console.warn('Clerk: Signin incomplete, result:', result);
        throw new Error('Signin incomplete');
      }
    } 
    catch (error) {
      console.error('Clerk signin error:', error);

      // Transform Clerk errors to user-friendly messages
      let errorMessage = error.message;
      
      if (error.errors && error.errors.length > 0) {
        const clerkError = error.errors[0];
        
        if (clerkError.code === 'form_identifier_not_found') {
          errorMessage = 'No account found with this email address. Please sign up first.';
        } 
        else if (clerkError.code === 'form_password_incorrect') {
          errorMessage = 'Incorrect password. Please try again.';
        } 
        else if (clerkError.code === 'form_identifier_not_verified') {
          errorMessage = 'Please verify your email address before signing in. Check your inbox for the verification email.';
        }
      }
      
      throw new Error(errorMessage);
    }
  };

  const verifyEmail = async (code) => {
    try {
      console.log('Clerk: Verifying email with code');
      
      const result = await signUp.attemptEmailAddressVerification({ code });
      
      if (result.status === 'complete') {
        console.log('Clerk: Email verification successful');
        
        // Save user to Firestore in the background - don't wait for it
        // This prevents delays in the UI while still saving the user data
        savePendingUserToFirestore(result).catch(error => {
          console.error('Background save to Firestore failed:', error);
        });
        
        return result;
      } 
      else {
        throw new Error('Email verification incomplete');
      }
    } 
    catch (error) {
      console.error('Clerk email verification error:', error);
      throw error;
    }
  };

  // Background function to save user data - doesn't block verification completion
  const savePendingUserToFirestore = async (result) => {
    try {
      // Skip connection check - just try the operation and handle errors
      console.log('Firestore: Attempting to save user data...');

      let pendingData = {};
      try {
        const stored = await SecureStore.getItemAsync('pendingUserData');
        if (stored) {
          pendingData = JSON.parse(stored);
          await SecureStore.deleteItemAsync('pendingUserData');
        }
      } 
      catch (error) {
        console.log('Could not retrieve pending user data:', error);
      }

      const userDocRef = doc(db, 'users', result.createdUserId);
      await setDoc(userDocRef, {
        // Only store essential app-specific data, let Clerk handle the rest
        clerkId: result.createdUserId,
        email: result.emailAddress,
        emailVerifiedAt: new Date(),
        createdAt: new Date(pendingData.createdAt) || new Date(),
        verificationMethod: 'clerk',
        // App-specific fields for future features
        preferences: {
          chatHistory: [],
          favoriteLocations: [],
          theme: 'light'
        },
        lastActive: new Date()
      });
      
      console.log('Firestore: User saved successfully after verification');
      
      // Load user profile from Firestore
      try {
        const userDoc = await getDoc(userDocRef);
        if (userDoc.exists()) {
          setUserProfile(userDoc.data());
          console.log('Firestore: User profile loaded after verification');
        }
      } 
      catch (error) {
        console.log('Could not reload user profile, will retry later:', error.message);
      }

      // Clean up any pending sync data
      await SecureStore.deleteItemAsync('pendingFirestoreUser');
      
    } catch (firestoreError) {
      console.log('Firestore: Save failed, storing for later sync:', firestoreError.message);
      
      // Store for later retry if save failed (but don't spam logs)
      try {
        await SecureStore.setItemAsync('pendingFirestoreUser', JSON.stringify({
          clerkId: result.createdUserId,
          email: result.emailAddress,
          timestamp: Date.now()
        }));
      } 
      catch (storeError) {
        console.error('Could not store user data for later sync:', storeError);
      }
    }
  };

  const resendVerificationEmail = async () => {
    try {
      console.log('Clerk: Resending verification email');
      await signUp.prepareEmailAddressVerification({ strategy: 'email_code' });
      console.log('Clerk: Verification email resent');
      return true;
    } 
    catch (error) {
      console.error('Clerk resend error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      console.log('Clerk: Signing out and clearing all data');
      
      // Clear Clerk session
      await signOut();
      
      // Clear local state
      setUserProfile(null);
      setUnverifiedUser(null);
      
      // Clear all stored data
      try {
        await SecureStore.deleteItemAsync('pendingUserData');
        await SecureStore.deleteItemAsync('pendingFirestoreUser');
        console.log('Clerk: All local data cleared');
      } catch (error) {
        console.log('Could not clear local data:', error);
      }
    } 
    catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  };

  // Function to handle the "already signed in" state mismatch
  const resetAuthState = async () => {
    try {
      console.log('Resetting authentication state...');
      await signOut();
      setUserProfile(null);
      setUnverifiedUser(null);
      await SecureStore.deleteItemAsync('pendingUserData');
      await SecureStore.deleteItemAsync('pendingFirestoreUser');
      setLoading(false);
      console.log('Authentication state reset complete');
    } 
    catch (error) {
      console.error('Error resetting auth state:', error);
      setLoading(false);
    }
  };


  return {
  user: user && user.emailAddresses[0]?.verification?.status === 'verified' ? user : null,
    userProfile,
    loading: !userLoaded || !signUpLoaded || loading,
    unverifiedUser,
    signUp: signUpUser,
    signIn: signInUser,
    verifyEmail,
    resendVerificationEmail,
    logout,
    resetAuthState, // For handling auth state mismatches
    // Legacy compatibility
    verifyEmailWithCode: verifyEmail,
  };
};