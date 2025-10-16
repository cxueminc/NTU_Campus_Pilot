import { ClerkProvider } from '@clerk/clerk-expo';

// You'll need to get this from your Clerk dashboard
// Go to https://clerk.com/docs/quickstarts/expo to set up
export const CLERK_PUBLISHABLE_KEY = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY;

// For now, we'll use a placeholder - you'll replace this with your actual key
// Make sure to add this to your .env file later
if (!CLERK_PUBLISHABLE_KEY) {
  throw new Error('Missing Clerk Publishable Key. Please add EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY to your environment variables.');
}

export { ClerkProvider };