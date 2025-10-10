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
  //const API_BASE = "http://10.91.144.60:8000";
  const API_BASE = "http://192.168.1.51:8000";

  // Default chat messages
  const [messages, setMessages] = useState([
    { id: "2", text: "Ask me anything!"},
    { id: "1", text: "Welcome 👋" },
  ]);
  const [draft, setDraft] = useState("");
  const listRef = useRef(null);

  const headerHeight = useHeaderHeight();
  const tabBarHeight = useBottomTabBarHeight?.() ?? 0;

  function extractConstraints(userQ){
    const userQueryLC = userQ.toLowerCase();
    const queryConstraints = {attributes: {}};

    if(userQueryLC.includes("study area") || userQueryLC.includes("study"))
      queryConstraints.type = ["study_area"];


    if(userQueryLC.includes("canteen") || userQueryLC.includes("food") || userQueryLC.includes("eat"))
      queryConstraints.type = ["food"];

    if(userQueryLC.includes("north spine") || userQueryLC.includes("ns"))
      queryConstraints.building = ["North Spine"];

    if(userQueryLC.includes("south spine") || userQueryLC.includes("ss"))
      queryConstraints.building = ["South Spine"];

    return queryConstraints;
  }

  const send = async () => {
    console.log("🚀 SEND FUNCTION CALLED!");
    console.log("Draft content:", draft);

    if (!draft.trim()) {
      console.log("❌ Empty draft, returning early");
      return;
    }

    // keep a copy before clearing input
    const userQuery = draft;

    const userMsgId = Date.now().toString();
    const loadingMsgId = userMsgId + "-loading";
    const m = { id: userMsgId, text: draft, mine: true };
    const loadingMsg = { id: loadingMsgId, text: "Loading Reply...", mine: false };
    setMessages(prev => [loadingMsg, m, ...prev]);
    
    // clear input and scroll
    setDraft("");
    requestAnimationFrame(() =>
      listRef.current?.scrollToOffset({ offset: 0, animated: true })
    );

    // call FastAPI /recommend endpoint
    try {
      const requestPayload = {
        query: userQuery,
        constraints: extractConstraints(userQuery),
        top_k: 5,
      };
      
      console.log("=== SENDING TO BACKEND ===");
      console.log("Query:", userQuery);
      console.log("Request payload:", JSON.stringify(requestPayload, null, 2));
      console.log("API endpoint:", `${API_BASE}/recommend`);
      
      const response = await fetch(`${API_BASE}/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestPayload),
      });

      // Debug: Check response status and content type
      console.log("=== BACKEND RESPONSE ===");
      console.log("Response status:", response.status);
      console.log("Response headers:", response.headers.get('content-type'));
      
      // Get raw text first to see what the server is actually returning
      const rawText = await response.text();
      console.log("Raw response:", rawText);
      console.log("========================");
      
      // Try to parse as JSON
      let data;
      try {
        data = JSON.parse(rawText);
        console.log("Parsed JSON data:", data);
      } catch (jsonError) {
        console.error("JSON parse error:", jsonError);
        console.log("First 200 chars of response:", rawText.substring(0, 200));
        
        // Show the raw response in chat for debugging
        setMessages(prev => prev.map(msg =>
          msg.id === loadingMsgId
            ? { ...msg, text: `Backend error: ${rawText.substring(0, 200)}` }
            : msg
        ));
        return;
      }

      // Format a readable reply from results
      let chatbotReply = "";
      console.log("=== PROCESSING RESPONSE ===");
      console.log("Full backend data:", JSON.stringify(data, null, 2));
      
      if (data && data.answer && data.answer.trim().length > 0) {
        chatbotReply = data.answer;
        console.log("Using data.answer:", data.answer);
      }
      else
      {
        chatbotReply = "Sorry, I couldn't find a facility that matches your requirement...";
        console.log("No valid answer found, using default message");
      }
      
      console.log("Final chatbot reply:", chatbotReply);
      console.log("===========================");

      // replace loading message with API response
      setMessages(prev => 
        prev.map(msg =>
          msg.id === loadingMsgId ? { ...msg, text: chatbotReply } : msg
        )
      );
    }
    catch (error) {
      console.error("API call failed:", error);
      setMessages(prev => prev.map(msg =>
        msg.id === loadingMsgId
          ? { ...msg, text: "API error: " + error.message }
          : msg
      ));
    }
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={headerHeight + tabBarHeight}
    >
      {/* Press anywhere blank to dismiss keyboard */}
      <Pressable style={{ flex: 1 }} onPress={Keyboard.dismiss}>
        <FlatList
          ref={listRef}
          data={messages}
          inverted
          keyExtractor={(m) => m.id}
          style={{ flex: 1 }}
          contentContainerStyle={{ padding: 16, paddingBottom: 8 }}
          keyboardShouldPersistTaps="handled"
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
      </Pressable>

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
        />
        <Text onPress={send} style={styles.send}>
          Send
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
  },
});
