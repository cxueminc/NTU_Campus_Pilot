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
  const [messages, setMessages] = useState([
    { id: "2", text: "Ask me anything!"},
    { id: "1", text: "Welcome 👋" },
  ]);
  const [draft, setDraft] = useState("");
  const listRef = useRef(null);

  const headerHeight = useHeaderHeight();
  const tabBarHeight = useBottomTabBarHeight?.() ?? 0;

  const send = () => {
    if (!draft.trim()) return;
    const m = { id: Date.now().toString(), text: draft, mine: true };
    setMessages(prev => [m, ...prev]);
    setDraft("");
    requestAnimationFrame(() =>
      listRef.current?.scrollToOffset({ offset: 0, animated: true })
    );
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
