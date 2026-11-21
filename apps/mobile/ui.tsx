import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  AppState,
  Pressable,
  RefreshControl,
  ScrollView,
  Text,
  TextInput,
  View,
} from "react-native";
import type { TextInputProps } from "react-native";
import { color, styles } from "./styles";
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

export function useRefreshOnReturn(refresh: () => void) {
  useEffect(() => {
    const subscription = AppState.addEventListener("change", (state) => {
      if (state === "active") refresh();
    });
    return () => subscription.remove();
  }, [refresh]);
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

export function PasswordInput({
  label,
  autoComplete,
  editable,
  value,
  onChangeText,
  onSubmitEditing,
}: Pick<
  TextInputProps,
  "autoComplete" | "editable" | "value" | "onChangeText" | "onSubmitEditing"
> & {
  label: string;
}) {
  const t = useTranslate();
  const [visible, setVisible] = useState(false);
  const action = t(visible ? "hidePasswordValue" : "showPasswordValue");

  useEffect(() => {
    if (!visible) return;
    const subscription = AppState.addEventListener("change", (state) => {
      if (state === "background") setVisible(false);
    });
    return () => subscription.remove();
  }, [visible]);

  return (
    <View style={styles.passwordInputRow}>
      <TextInput
        style={[styles.input, styles.passwordInput]}
        accessibilityLabel={label}
        placeholder={label}
        placeholderTextColor={color.muted}
        autoComplete={autoComplete}
        autoCapitalize="none"
        autoCorrect={false}
        spellCheck={false}
        secureTextEntry={!visible}
        editable={editable}
        value={value}
        onChangeText={onChangeText}
        onSubmitEditing={onSubmitEditing}
      />
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={t(visible ? "hidePasswordField" : "showPasswordField", {
          field: label,
        })}
        onPress={() => setVisible((current) => !current)}
        style={({ pressed }) => [styles.passwordToggle, pressed && styles.dimmed]}
      >
        <Text style={styles.passwordToggleText}>{action}</Text>
      </Pressable>
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
