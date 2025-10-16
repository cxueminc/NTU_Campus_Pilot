import React, { useRef, useState } from "react";
import {
  View,
  Text,
  TextInput,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
  Pressable,
  StyleSheet,
} from "react-native";
import { useHeaderHeight } from "@react-navigation/elements";
import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";

export default function ChatScreen() {
  // Backend API configuration from environment variables
  const API_BASE = Platform.OS === 'web' 
    ? process.env.EXPO_PUBLIC_API_BASE_WEB
    : process.env.EXPO_PUBLIC_API_BASE_MOBILE;

  console.log('Using API_BASE:', API_BASE); // Debug log
  
  // Default chat messages with unique IDs
  const [messages, setMessages] = useState([
    { id: `welcome-${Date.now()}`, text: "Ask me anything about NTU facilities! I can help you find study areas, food places, and more.", mine: false },
    { id: `greeting-${Date.now() - 1}`, text: "Welcome 👋", mine: false },
  ]);
  const [draft, setDraft] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  const listRef = useRef(null);

  const headerHeight = useHeaderHeight();
  const tabBarHeight = useBottomTabBarHeight?.() ?? 0;

  // Helper function to generate unique message IDs
  const generateUniqueId = () => `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Handle keyboard events for better scrolling
  React.useEffect(() => {
    const keyboardDidShowListener = Keyboard.addListener('keyboardDidShow', (e) => {
      setKeyboardHeight(e.endCoordinates.height);
    });
    
    const keyboardDidHideListener = Keyboard.addListener('keyboardDidHide', () => {
      setKeyboardHeight(0);
    });

    return () => {
      keyboardDidShowListener?.remove();
      keyboardDidHideListener?.remove();
    };
  }, []); // Empty dependency array to run only once

  // Test API connection on component mount (completely disabled to prevent key conflicts)
  React.useEffect(() => {
    const testConnection = async () => {
      try {
        console.log(`🧪 Testing backend connection to: ${API_BASE}`);
        console.log(`📱 Platform: ${Platform.OS}`);
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(`${API_BASE}/`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          const data = await response.json();
          console.log("✅ Backend connection successful:", data);
          if (data.semantic_search_available) {
            console.log("🤖 Semantic search is available");
          } else {
            console.log("⚠️ Semantic search not available");
          }
        } else {
          console.log("❌ Backend connection failed:", response.status);
        }
      } catch (error) {
        console.log("❌ Backend connection error:", error.message);
      }
    };
    
    // Only log connection status, don't update UI to prevent duplicate keys
    const timer = setTimeout(testConnection, 2000);
    return () => clearTimeout(timer);
  }, []);

  const send = async () => {
    console.log("🚀 SEND FUNCTION CALLED!");
    console.log("Draft content:", draft);

    if (!draft.trim()) {
      console.log("❌ Empty draft, returning early");
      return;
    }

    // Prevent multiple concurrent requests
    if (isLoading) {
      console.log("⏳ Already loading, ignoring send");
      return;
    }

    // Keep a copy before clearing input
    const userQuery = draft.trim();
    setIsLoading(true);

    const userMsgId = generateUniqueId();
    const loadingMsgId = generateUniqueId();
    const userMsg = { id: userMsgId, text: userQuery, mine: true };
    const loadingMsg = { id: loadingMsgId, text: "🤔 Thinking...", mine: false };
    
    setMessages(prev => [loadingMsg, userMsg, ...prev]);
    
    // Clear input and scroll
    setDraft("");
    requestAnimationFrame(() =>
      listRef.current?.scrollToOffset({ offset: 0, animated: true })
    );

    try {
      // Build conversation history for context
      const conversationHistory = messages
        .slice(0, -1) // Exclude the loading message we just added
        .map(msg => ({
          role: msg.mine ? "user" : "assistant",
          content: msg.text
        }))
        .slice(-10); // Keep last 10 messages for context (limit to prevent token overflow)

      // Backend expects: { message: string, conversation_history?: array, max_results?: number }
      const requestPayload = {
        message: userQuery,
        conversation_history: conversationHistory,
        max_results: 5
      };
      
      console.log("=== SENDING TO BACKEND ===");
      console.log("Query:", userQuery);
      console.log("Conversation history:", JSON.stringify(conversationHistory, null, 2));
      console.log("Request payload:", JSON.stringify(requestPayload, null, 2));
      console.log("API endpoint:", `${API_BASE}/chat`);
      
      // Add timeout to prevent hanging
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
      
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestPayload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      console.log("=== BACKEND RESPONSE ===");
      console.log("Response status:", response.status);
      console.log("Response headers:", response.headers.get('content-type'));
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      const data = await response.json();
      console.log("Parsed JSON data:", JSON.stringify(data, null, 2));

      // Extract the conversational response
      let chatbotReply = "";

      if (data.response) {
        chatbotReply = data.response;
        console.log("✅ Using backend AI response");
      } else {
        chatbotReply = "Sorry, I couldn't process your request. Please try again.";
        console.log("❌ No response field found in backend data");
      }
      
      console.log("Final chatbot reply:", chatbotReply);

      // Replace loading message with API response
      setMessages(prev => 
        prev.map(msg =>
          msg.id === loadingMsgId ? { ...msg, text: chatbotReply } : msg
        )
      );
      
    } catch (error) {
      console.error("❌ API call failed:", error);
      
      let errorMessage = "Sorry, I'm having trouble connecting to the server. ";
      
      if (error.name === 'AbortError') {
        errorMessage = "Request timed out. The server might be busy or not responding.";
      } else if (error.message.includes("Network request failed")) {
        errorMessage = `Cannot reach the backend server.\n\nTroubleshooting:\n• Backend URL: ${API_BASE}\n• Make sure backend is running\n• Check if IP address is correct\n• Try restarting the backend server`;
      } else if (error.message.includes("500")) {
        errorMessage = "The backend server encountered an error. Please check the server logs.";
      } else if (error.message.includes("404")) {
        errorMessage = "The chat endpoint was not found. Please check the backend API.";
      } else {
        errorMessage += `\n\nError details: ${error.message}`;
      }
      
      setMessages(prev => prev.map(msg =>
        msg.id === loadingMsgId
          ? { ...msg, text: errorMessage }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={Platform.OS === "ios" ? headerHeight : 0}
    >
      <View style={{ flex: 1 }}>
        <FlatList
          ref={listRef}
          data={messages}
          inverted
          keyExtractor={(m) => m.id}
          style={{ flex: 1 }}
          contentContainerStyle={{ 
            padding: 16, 
            paddingBottom: 8,
            flexGrow: 1 
          }}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="on-drag"
          showsVerticalScrollIndicator={true}
          scrollEnabled={true}
          removeClippedSubviews={false}
          onContentSizeChange={() => {
            // Auto-scroll to latest message when content changes (with debounce)
            if (messages.length > 0) {
              setTimeout(() => {
                listRef.current?.scrollToOffset({ offset: 0, animated: true });
              }, 100);
            }
          }}
          renderItem={({ item }) => (
            <View
              style={[
                styles.bubble,
                item.mine ? styles.bubbleMine : styles.bubbleOther,
              ]}
            >
              <Text style={styles.text}>{item.text}</Text>
            </View>
          )}
        />
      </View>

      {/* Input bar */}
      <View style={[styles.inputBar, { paddingBottom: 8 + tabBarHeight / 4 }]}>
        <TextInput
          value={draft}
          onChangeText={setDraft}
          placeholder="Type a query..."
          style={styles.input}
          multiline
          onSubmitEditing={send}
          submitBehavior="submit"
          returnKeyType="send"
          blurOnSubmit={false}
          scrollEnabled={true}
          onFocus={() => {
            // Scroll to top when focusing input
            setTimeout(() => {
              listRef.current?.scrollToOffset({ offset: 0, animated: true });
            }, 100);
          }}
        />
        <Text 
          onPress={send} 
          style={[
            styles.send,
            isLoading && styles.sendDisabled
          ]}
        >
          {isLoading ? "..." : "Send"}
        </Text>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  bubble: {
    maxWidth: "80%",
    padding: 10,
    borderRadius: 16,
    marginBottom: 10,
  },
  bubbleMine: {
    alignSelf: "flex-end",
    backgroundColor: "#DCF8C6",
    borderTopRightRadius: 4,
  },
  bubbleOther: {
    alignSelf: "flex-start",
    backgroundColor: "#eee",
    borderTopLeftRadius: 4,
  },
  text: { fontSize: 16 },
  inputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    paddingHorizontal: 12,
    paddingTop: 8,
    paddingBottom: 0,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "#ccc",
    backgroundColor: "white",
  },
  input: {
    flex: 1,
    fontSize: 16,
    maxHeight: 120,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  send: {
    marginLeft: 8,
    fontWeight: "600",
    paddingVertical: 10,
    color: "#007AFF",
  },
  sendDisabled: {
    color: "#999",
  },
});
