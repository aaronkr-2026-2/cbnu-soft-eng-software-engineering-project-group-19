import { useEffect, useRef, useState } from "react";
import { BackHandler, KeyboardAvoidingView, Platform, Text, View } from "react-native";
import { ApiError, changePassword } from "./api";
import { useTranslate } from "./localization";
import type { MessageKey } from "./localization";
import { styles } from "./styles";
import { Button, Content, ErrorNotice, PasswordInput } from "./ui";

const MIN_PASSWORD_LENGTH = 8;
const MAX_PASSWORD_LENGTH = 128;

export function ChangePassword({
  token,
  onChanged,
  onExpired,
  onBack,
}: {
  token: string;
  onChanged: () => Promise<void>;
  onExpired: () => void;
  onBack: () => void;
}) {
  const t = useTranslate();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [saving, setSaving] = useState(false);
  const [validation, setValidation] = useState<MessageKey>();
  const [error, setError] = useState<unknown>();
  const submitting = useRef(false);

  useEffect(() => {
    const back = BackHandler.addEventListener("hardwareBackPress", () => {
      if (!submitting.current) onBack();
      return true;
    });
    return () => back.remove();
  }, [onBack]);

  async function submit() {
    if (submitting.current || !current || !next || !confirmation) return;
    setError(undefined);
    const length = Array.from(next).length;
    if (length < MIN_PASSWORD_LENGTH || length > MAX_PASSWORD_LENGTH) {
      setValidation("passwordLength");
      return;
    }
    if (next !== confirmation) {
      setValidation("passwordMismatch");
      return;
    }

    setValidation(undefined);
    submitting.current = true;
    setSaving(true);
    try {
      await changePassword(token, current, next);
      await onChanged();
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 401) onExpired();
      else setError(failure);
    } finally {
      submitting.current = false;
      setSaving(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.fill}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <Content>
        <Text accessibilityRole="header" style={styles.title}>
          {t("changePassword")}
        </Text>
        <Text style={styles.muted}>
          {t("passwordLength", { min: MIN_PASSWORD_LENGTH, max: MAX_PASSWORD_LENGTH })}
        </Text>
        <View style={[styles.card, styles.cardBody]}>
          {(
            [
              ["currentPassword", "current-password", current, setCurrent],
              ["newPassword", "new-password", next, setNext],
              ["confirmNewPassword", "off", confirmation, setConfirmation],
            ] as const
          ).map(([label, autoComplete, value, setValue]) => (
            <View key={label} style={styles.passwordField}>
              <Text style={styles.listTitle}>{t(label)}</Text>
              <PasswordInput
                label={t(label)}
                autoComplete={autoComplete}
                editable={!saving}
                value={value}
                onChangeText={(text) => {
                  setValue(text);
                  setValidation(undefined);
                  setError(undefined);
                }}
                onSubmitEditing={label === "confirmNewPassword" ? submit : undefined}
              />
            </View>
          ))}
          {validation && (
            <Text accessibilityRole="alert" style={styles.error}>
              {t(validation, { min: MIN_PASSWORD_LENGTH, max: MAX_PASSWORD_LENGTH })}
            </Text>
          )}
          {error !== undefined && <ErrorNotice error={error} />}
          <Button
            title={t(saving ? "refreshing" : "changePassword")}
            onPress={submit}
            disabled={saving || !current || !next || !confirmation}
          />
        </View>
        <Button title={t("back")} onPress={onBack} disabled={saving} secondary />
      </Content>
    </KeyboardAvoidingView>
  );
}
