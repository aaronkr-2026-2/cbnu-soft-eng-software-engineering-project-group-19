import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Pressable, RefreshControl, ScrollView, Text, View } from "react-native";
import { styles } from "./styles";
import { ApiError } from "./api";
import { useTranslate } from "./localization";
import type { MessageKey } from "./localization";

function errorKey(error: unknown): MessageKey {
  if (!(error instanceof ApiError)) return "genericError";
  if (error.messageKey) return error.messageKey;
  if (error.status === 0 || error.status >= 500) return "connectionError";
  if (error.message === "Watch the video to the end before completing this lesson")
    return "videoRequired";
  if (error.status === 401) return "signInAgain";
  if (error.status === 403) return "accessDenied";
  if (error.status === 404) return "notFound";
  if (error.status === 429) return "tooManyRequests";
  return "genericError";
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
  const t = useTranslate();
  return (
    <View style={styles.notice}>
      <Text accessibilityRole="alert" style={styles.error}>
        {t(errorKey(error))}
      </Text>
      {retry && <Button title={t("retry")} onPress={retry} secondary />}
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
