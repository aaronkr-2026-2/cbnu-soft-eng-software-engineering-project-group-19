import * as SecureStore from "expo-secure-store";
import { useCallback, useRef, useState } from "react";
import { Text, TextInput, View } from "react-native";
import { useTranslate } from "./localization";
import { color, styles } from "./styles";
import { Button, useResource } from "./ui";

const MAX_NOTE_LENGTH = 500;
let pendingNoteWrite = Promise.resolve();

export function LessonNote({ accountId, lessonId }: { accountId: string; lessonId: string }) {
  const t = useTranslate();
  const key = `studyflow-note-${accountId}-${lessonId}`;
  const load = useCallback(() => pendingNoteWrite.then(() => SecureStore.getItemAsync(key)), [key]);
  const { value: stored, error, loading, refresh } = useResource(load);
  const [saved, setSaved] = useState<string>();
  const [draft, setDraft] = useState<string>();
  const [status, setStatus] = useState<"noteSaved" | "noteSaveError">();
  const [saving, setSaving] = useState(false);
  const busy = useRef(false);
  const savedValue = saved ?? stored ?? "";
  const value = draft ?? savedValue;

  async function save() {
    if (busy.current || value === savedValue) return;
    busy.current = true;
    setSaving(true);
    setStatus(undefined);
    const note = value.trim();
    const write = pendingNoteWrite.then(() =>
      note ? SecureStore.setItemAsync(key, note) : SecureStore.deleteItemAsync(key),
    );
    pendingNoteWrite = write.catch(() => {});
    try {
      await write;
      setSaved(note);
      setDraft(note);
      setStatus("noteSaved");
    } catch {
      setStatus("noteSaveError");
    } finally {
      busy.current = false;
      setSaving(false);
    }
  }

  return (
    <View style={styles.notice}>
      <Text accessibilityRole="header" style={styles.listTitle}>
        {t("lessonNote")}
      </Text>
      {error !== undefined ? (
        <>
          <Text accessibilityRole="alert" style={styles.error}>
            {t("noteLoadError")}
          </Text>
          <Button title={t("retry")} onPress={refresh} secondary />
        </>
      ) : (
        <>
          <Text style={styles.muted}>{t("noteHint", { max: MAX_NOTE_LENGTH })}</Text>
          <TextInput
            style={[styles.input, styles.noteInput]}
            accessibilityLabel={t("lessonNote")}
            placeholder={t("notePlaceholder")}
            placeholderTextColor={color.muted}
            multiline
            maxLength={MAX_NOTE_LENGTH}
            editable={!loading && !saving}
            value={value}
            onChangeText={(text) => {
              setDraft(text);
              setStatus(undefined);
            }}
          />
          <Button
            title={t(saving ? "savingNote" : "saveNote")}
            onPress={save}
            disabled={loading || saving || value === savedValue}
            secondary
          />
          {status && (
            <Text
              accessibilityRole="alert"
              style={status === "noteSaved" ? styles.muted : styles.error}
            >
              {t(status)}
            </Text>
          )}
        </>
      )}
    </View>
  );
}
