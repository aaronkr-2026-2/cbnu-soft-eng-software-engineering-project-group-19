import { useEffect, useMemo, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { WebView } from "react-native-webview";
import { ApiError, WEB_APP, getVideoProgress, reportVideoProgress } from "./api";
import type { CourseLanguage, Lesson, PlaybackSample, VideoProgress } from "./api";
import { lessonVideoSource, playbackStart, playerDocument } from "./playerDocument";
import type { PlaybackStart } from "./playerDocument";
import { color, styles } from "./styles";
import { useTranslate } from "./localization";
import type { MessageKey } from "./localization";
import { Button } from "./ui";

const START_FROM_BEGINNING = { item: 0, seconds: 0 };

function displayTime(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${String(seconds % 60).padStart(2, "0")}`;
}

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
  const t = useTranslate();
  const [start, setStart] = useState<PlaybackStart | null>(null);
  const video = useMemo(() => lessonVideoSource(lesson, language), [lesson, language]);
  const source = useMemo(
    () =>
      video && start ? { html: playerDocument(video, start, language), baseUrl: WEB_APP } : null,
    [video, start, language],
  );
  const [ready, setReady] = useState(false);
  const [playerError, setPlayerError] = useState<MessageKey | null>(null);
  const [trackingError, setTrackingError] = useState(false);
  const [reload, setReload] = useState(0);
  const pending = useRef<PlaybackSample[]>([]);
  const sending = useRef(false);
  const connection = useRef<AbortController | null>(null);

  useEffect(() => {
    const request = new AbortController();
    connection.current = request;
    if (video) {
      getVideoProgress(token, course, lesson.id, request.signal).then(
        (progress) => {
          if (request.signal.aborted) return;
          onProgress(progress);
          setStart((current) => current ?? playbackStart(progress));
        },
        (error: unknown) => {
          if (request.signal.aborted) return;
          if (error instanceof ApiError && error.status === 401) onExpired();
          else setStart((current) => current ?? START_FROM_BEGINNING);
        },
      );
    }
    return () => {
      request.abort();
      pending.current = [];
    };
  }, [course, lesson.id, token, video, onExpired, onProgress]);

  useEffect(() => {
    if (!source || ready || playerError) return;
    const timeout = setTimeout(() => setPlayerError("videoLoadError"), 20_000);
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

  if (!video) return <Text style={styles.error}>{t("videoSourceError")}</Text>;
  if (!source || !start) {
    return (
      <View style={playerStyles.section}>
        <ActivityIndicator accessibilityLabel={t("loadingSavedPosition")} color={color.leaf} />
        <Button
          title={t("openFromStart")}
          onPress={() => setStart(START_FROM_BEGINNING)}
          secondary
        />
      </View>
    );
  }

  function restart() {
    setStart(START_FROM_BEGINNING);
    setReady(false);
    setPlayerError(null);
    setReload((value) => value + 1);
  }

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
                setPlayerError(null);
              } else if (message.type === "progress" && validSample(message.sample)) {
                void record(message.sample);
              } else if (message.type === "error") {
                setPlayerError(
                  [100, 101, 150].includes(message.code)
                    ? "youtubeRestricted"
                    : "videoPlaybackError",
                );
              }
            } catch {
              // Other WebView messages do not describe a playback event.
            }
          }}
          onError={() => setPlayerError("videoLoadError")}
          onHttpError={() => setPlayerError("videoServerError")}
          allowsInlineMediaPlayback
          allowsFullscreenVideo
          mediaPlaybackRequiresUserAction
          scrollEnabled={false}
          style={playerStyles.web}
          containerStyle={playerStyles.web}
          setSupportMultipleWindows={false}
        />
      </View>
      {(start.item > 0 || start.seconds > 0) && !playerError && (
        <>
          <Text style={styles.muted}>
            {video.playlist
              ? t("resumePlaylist", { item: start.item + 1, time: displayTime(start.seconds) })
              : t("resumePosition", { time: displayTime(start.seconds) })}
          </Text>
          <Button title={t("restartVideo")} onPress={restart} secondary />
        </>
      )}
      {!ready && !playerError && (
        <ActivityIndicator accessibilityLabel={t("videoLoading")} color={color.leaf} />
      )}
      {!!playerError && (
        <>
          <Text accessibilityRole="alert" style={styles.error}>
            {t(playerError)}
          </Text>
          <Button
            title={t("reloadVideo")}
            onPress={() => {
              setPlayerError(null);
              setReady(false);
              setReload((value) => value + 1);
            }}
            secondary
          />
        </>
      )}
      {trackingError && (
        <Text accessibilityRole="alert" style={styles.error}>
          {t("videoTrackingError")}
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
