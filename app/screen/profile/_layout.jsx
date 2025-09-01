import { Stack } from "expo-router";

export default function ProfileLayout() {
  return (
    <Stack>
      <Stack.Screen name="profile" options={{ title: "Profile" }} />
      <Stack.Screen name="changepwd" options={{ title: "Change Password" }} />
    </Stack>
  );
}