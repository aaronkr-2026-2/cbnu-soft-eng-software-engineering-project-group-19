import { allowScreenCaptureAsync, preventScreenCaptureAsync } from "expo-screen-capture";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { ActivityIndicator, Platform, Text } from "react-native";
import { useTranslate } from "./localization";
import { color, styles } from "./styles";
import { Button, Content } from "./ui";

let nextCaptureKey = 0;

export function LessonCaptureGuard({
  children,
  onBack,
}: {
  children: ReactNode;
  onBack: () => void;
}) {
  const t = useTranslate();
  const native = Platform.OS === "android" || Platform.OS === "ios";
  const [attempt, setAttempt] = useState(0);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    if (!native) return;
    let mounted = true;
    const key = `scholward-lesson-${++nextCaptureKey}`;
    const protection = preventScreenCaptureAsync(key);
    void protection.then(
      () => {
        if (mounted) setStatus("ready");
      },
      () => {
        if (mounted) setStatus("error");
      },
    );
    return () => {
      mounted = false;
      // Release only after this request finishes, even if the learner left while it was pending.
      void protection.then(() => allowScreenCaptureAsync(key)).catch(() => {});
    };
  }, [attempt, native]);

  if (!native || status === "ready") return children;
  return (
    <Content>
      <Button title={t("backToLessons")} onPress={onBack} secondary />
      {status === "loading" ? (
        <ActivityIndicator color={color.leaf} accessibilityLabel={t("lessonProtectionLoading")} />
      ) : (
        <>
          <Text accessibilityRole="alert" style={styles.error}>
            {t("lessonProtectionUnavailable")}
          </Text>
          <Button
            title={t("retry")}
            onPress={() => {
              setStatus("loading");
              setAttempt((previous) => previous + 1);
            }}
          />
        </>
      )}
    </Content>
  );
}
