import { useEffect, useMemo, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { WebView } from "react-native-webview";
import { ApiError, WEB_APP, reportVideoProgress } from "./api";
import type { CourseLanguage, Lesson, PlaybackSample, VideoProgress } from "./api";
import { lessonVideoSource, playerDocument } from "./playerDocument";
import { color, styles } from "./styles";
import { Button } from "./ui";

function validSample(value: unknown): value is PlaybackSample {
  if (!value || typeof value !== "object") return false;
  const sample = value as Partial<PlaybackSample>;
  const {
    position_seconds: position,
    duration_seconds: duration,
    item_index: index,
    item_count: count,
    playback_rate: rate,
    ended,
  } = sample;
  return (
    typeof position === "number" &&
    Number.isFinite(position) &&
    position >= 0 &&
    typeof duration === "number" &&
    duration > 0 &&
    duration <= 86400 &&
    position <= duration &&
    typeof index === "number" &&
    Number.isInteger(index) &&
    typeof count === "number" &&
    Number.isInteger(count) &&
    index >= 0 &&
    index < count &&
    count <= 500 &&
    typeof rate === "number" &&
    rate >= 0.25 &&
    rate <= 2 &&
    typeof ended === "boolean"
  );
}

export function LessonVideo({
  course,
  lesson,
  token,
  language,
  onProgress,
  onExpired,
}: {
  course: string;
  lesson: Lesson;
  token: string;
  language: CourseLanguage;
  onProgress: (progress: VideoProgress) => void;
  onExpired: () => void;
}) {
  const source = useMemo(() => {
    const video = lessonVideoSource(lesson, language);
    return video ? { html: playerDocument(video), baseUrl: WEB_APP } : null;
  }, [lesson, language]);
  const [ready, setReady] = useState(false);
  const [playerError, setPlayerError] = useState("");
  const [trackingError, setTrackingError] = useState(false);
  const [reload, setReload] = useState(0);
  const pending = useRef<PlaybackSample[]>([]);
  const sending = useRef(false);
  const connection = useRef<AbortController | null>(null);

  useEffect(() => {
    const request = new AbortController();
    connection.current = request;
    return () => {
      request.abort();
      pending.current = [];
    };
  }, [course, lesson.id, token]);

  useEffect(() => {
    if (!source || ready || playerError) return;
    const timeout = setTimeout(
      () => setPlayerError("Video yuklanmadi. Qayta urinib ko‘ring."),
      20_000,
    );
    return () => clearTimeout(timeout);
  }, [source, ready, playerError, reload]);

  async function record(sample: PlaybackSample) {
    const request = connection.current;
    if (!request || request.signal.aborted) return;
    const previous = pending.current.at(-1);
    if (previous && !previous.ended && previous.item_index === sample.item_index)
      pending.current.pop();
    pending.current.push(sample);
    if (sending.current) return;

    sending.current = true;
    try {
      while (!request.signal.aborted) {
        const next = pending.current.shift();
        if (!next) break;
        try {
          const progress = await reportVideoProgress(
            token,
            course,
            lesson.id,
            next,
            request.signal,
          );
          if (!request.signal.aborted) {
            setTrackingError(false);
            onProgress(progress);
          }
        } catch (error) {
          if (request.signal.aborted) break;
          if (error instanceof ApiError && error.status === 401) {
            onExpired();
            break;
          }
          setTrackingError(true);
        }
      }
    } finally {
      sending.current = false;
    }
  }

  if (!source) return <Text style={styles.error}>Video manzili ilovada ochilmadi.</Text>;

  return (
    <View style={playerStyles.section}>
      <View style={playerStyles.frame}>
        <WebView
          key={reload}
          source={source}
          originWhitelist={["*"]}
          onShouldStartLoadWithRequest={({ url, isTopFrame }) =>
            isTopFrame === false
              ? url.startsWith("https:") || url === "about:blank"
              : url === WEB_APP || url === "about:blank"
          }
          onMessage={({ nativeEvent: { url, data } }) => {
            if (url && url !== WEB_APP && url !== "about:blank") return;
            try {
              const message = JSON.parse(data);
              if (message.type === "ready") {
                setReady(true);
                setPlayerError("");
              } else if (message.type === "progress" && validSample(message.sample)) {
                void record(message.sample);
              } else if (message.type === "error") {
                setPlayerError(
                  [100, 101, 150].includes(message.code)
                    ? "YouTube bu videoni ilova ichida ochishga ruxsat bermadi."
                    : "Videoni ijro qilib bo‘lmadi. Qayta urinib ko‘ring.",
                );
              }
            } catch {
              // Other WebView messages do not describe a playback event.
            }
          }}
          onError={() => setPlayerError("Video yuklanmadi. Qayta urinib ko‘ring.")}
          onHttpError={() => setPlayerError("Video serveri javob bermadi.")}
          allowsInlineMediaPlayback
          allowsFullscreenVideo
          mediaPlaybackRequiresUserAction
          scrollEnabled={false}
          style={playerStyles.web}
          containerStyle={playerStyles.web}
          setSupportMultipleWindows={false}
        />
      </View>
      {!ready && !playerError && (
        <ActivityIndicator accessibilityLabel="Video yuklanmoqda" color={color.leaf} />
      )}
      {!!playerError && (
        <>
          <Text accessibilityRole="alert" style={styles.error}>
            {playerError}
          </Text>
          <Button
            title="Videoni qayta yuklash"
            onPress={() => {
              setPlayerError("");
              setReady(false);
              setReload((value) => value + 1);
            }}
            secondary
          />
        </>
      )}
      {trackingError && (
        <Text accessibilityRole="alert" style={styles.error}>
          Video progressini saqlab bo‘lmadi. Internet aloqasini tekshiring.
        </Text>
      )}
    </View>
  );
}

const playerStyles = StyleSheet.create({
  section: { gap: 10 },
  frame: {
    width: "100%",
    minHeight: 200,
    aspectRatio: 16 / 9,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: "#111",
  },
  web: { flex: 1, backgroundColor: "#111" },
});
