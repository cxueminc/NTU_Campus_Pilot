import { View, Text, TextInput, KeyboardAvoidingView, Platform, ScrollView, StyleSheet } from "react-native";
import { useState } from "react";
import { useAuth } from "../../../hooks/useAuth";

export default function MapScreen() {

  const [search, setSearch] = useState("");

  const { user } = useAuth ? useAuth() : {};
  const displayName = user?.displayName || "Guest";

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"} // 👈 lifts screen on iOS
      keyboardVerticalOffset={80} // adjust if needed (depends on header height)
    >
      <ScrollView
        contentContainerStyle={{ flexGrow: 1 }}
        keyboardShouldPersistTaps="handled" // dismiss keyboard on tap outside
      >
        <View style={styles.container}>
          {/* Search Bar at the Top */}
          <View style={styles.searchContainer}>
            <TextInput
              style={styles.searchInput}
              placeholder="Search NTU..."
              value={search}
              onChangeText={setSearch}
            />
          </View>

          {/* 🔹 Centered Content */}
          <View style={styles.content}>
            <Text style={styles.title}>Map Screen</Text>
            <Text style={styles.welcomeText}>Welcome! {displayName}</Text>
            <Text style={styles.sectionTitle}>NTU Campus Pilot</Text>
            <Text style={styles.description}>
              Welcome to the NTU Campus Navigation App. This is your map screen
              where you can access all the features.
            </Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
  },
  searchContainer: {
    padding: 30,
    marginTop: 60, // pushes search bar below header
  },
  searchInput: {
    height: 40,
    borderColor: "#ccc",
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    backgroundColor: "white",
  },
  content: {
    flex: 1, // takes remaining space
    alignItems: "center",
    justifyContent: "center", // centers text vertically
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: "bold",
    color: "#333",
    marginBottom: 20,
  },
  welcomeText: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#007AFF",
    marginBottom: 20,
    textAlign: "center",
  },
  sectionTitle: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#333",
    marginBottom: 15,
  },
  description: {
    fontSize: 16,
    color: "#555",
    textAlign: "center",
    lineHeight: 24,
  },
});
