import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Pressable, RefreshControl, ScrollView, Text, View } from "react-native";
import { styles } from "./styles";

function messageFor(error: unknown) {
  return error instanceof Error ? error.message : "Xato yuz berdi. Qayta urinib ko‘ring.";
}

export function useResource<T>(load: (signal: AbortSignal) => Promise<T>) {
  const [state, setState] = useState<{ value?: T; error?: unknown; loading: boolean }>({
    loading: true,
  });
  const [version, setVersion] = useState(0);
  const refresh = useCallback(() => setVersion((current) => current + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setState((previous) => ({ value: previous.value, loading: true }));
    load(controller.signal).then(
      (value) => {
        if (!controller.signal.aborted) setState({ value, loading: false });
      },
      (error: unknown) => {
        if (!controller.signal.aborted) setState({ error, loading: false });
      },
    );
    return () => controller.abort();
  }, [load, version]);

  return { ...state, refresh };
}

export function Button({
  title,
  onPress,
  secondary = false,
  disabled = false,
}: {
  title: string;
  onPress: () => void;
  secondary?: boolean;
  disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        secondary && styles.secondary,
        (pressed || disabled) && styles.dimmed,
      ]}
    >
      <Text style={[styles.buttonText, secondary && styles.secondaryText]}>{title}</Text>
    </Pressable>
  );
}

export function ErrorNotice({ error, retry }: { error: unknown; retry?: () => void }) {
  return (
    <View style={styles.notice}>
      <Text accessibilityRole="alert" style={styles.error}>
        {messageFor(error)}
      </Text>
      {retry && <Button title="Qayta urinish" onPress={retry} secondary />}
    </View>
  );
}

export function Content({
  children,
  refreshing = false,
  refresh,
}: {
  children: ReactNode;
  refreshing?: boolean;
  refresh?: () => void;
}) {
  return (
    <ScrollView
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
      refreshControl={
        refresh ? <RefreshControl refreshing={refreshing} onRefresh={refresh} /> : undefined
      }
    >
      {children}
    </ScrollView>
  );
}
