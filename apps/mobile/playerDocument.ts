import { WEB_APP, resourceUrl } from "./api";
import type { CourseLanguage, Lesson, VideoProgress } from "./api";

const playerOrigin = new URL(WEB_APP).origin;

export type PlaybackStart = { item: number; seconds: number };
export type VideoSource = { uri: string; youtube: boolean; playlist?: string };

const RESUME_OVERLAP_SECONDS = 2;

export function playbackStart(progress: VideoProgress): PlaybackStart {
  if (progress.can_complete) return { item: 0, seconds: 0 };
  const item = progress.resume_item_index ?? 0;
  const seconds = progress.resume_position_seconds ?? progress.furthest_position_seconds;
  return {
    item: Number.isInteger(item) && item >= 0 && item < progress.item_count ? item : 0,
    seconds: Number.isFinite(seconds)
      ? Math.max(0, Math.floor(seconds - RESUME_OVERLAP_SECONDS))
      : 0,
  };
}

export function lessonVideoSource(lesson: Lesson, language: CourseLanguage): VideoSource | null {
  if (lesson.external_video_url) {
    try {
      const url = new URL(lesson.external_video_url);
      const youtubeHost = [
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "www.youtube-nocookie.com",
      ];
      if (url.protocol === "https:" && youtubeHost.includes(url.hostname)) {
        const parts = url.pathname.split("/").filter(Boolean);
        const video =
          url.searchParams.get("v") ??
          (url.hostname === "youtu.be" || ["embed", "shorts", "live"].includes(parts[0])
            ? parts[parts.length - 1]
            : null);
        const playlist = url.searchParams.get("list");
        const validVideo = video && /^[A-Za-z0-9_-]{11}$/.test(video);
        const validPlaylist = playlist && /^[A-Za-z0-9_-]{10,100}$/.test(playlist);
        if (validVideo || validPlaylist) {
          const embed = new URL(
            `https://www.youtube-nocookie.com/embed/${validVideo ? video : "videoseries"}`,
          );
          for (const [key, value] of Object.entries({
            enablejsapi: "1",
            origin: playerOrigin,
            playsinline: "1",
            rel: "0",
            hl: language,
          }))
            embed.searchParams.set(key, value);
          if (validPlaylist && playlist) embed.searchParams.set("list", playlist);
          return {
            uri: embed.toString(),
            youtube: true,
            playlist: validPlaylist ? playlist : undefined,
          };
        }
      }
    } catch {
      // An invalid external URL can still have a playable uploaded version.
    }
  }
  const uri = lesson.resource_url && resourceUrl(lesson.resource_url);
  return uri ? { uri, youtube: false } : null;
}

export function playerDocument(source: VideoSource, start: PlaybackStart) {
  const url = new URL(source.uri);
  if (source.youtube && !source.playlist && start.seconds > 0)
    url.searchParams.set("start", String(start.seconds));
  const attributes = url
    .toString()
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;");
  const media = source.youtube
    ? `<iframe id="video" src="${attributes}" title="YouTube video" allow="encrypted-media; picture-in-picture; fullscreen" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>`
    : `<video id="video" src="${attributes}" controls playsinline preload="metadata"></video>`;

  return `<!doctype html><html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="strict-origin-when-cross-origin">
<style>html,body{margin:0;height:100%;overflow:hidden;background:#111}#video{width:100%;height:100%;border:0;display:block}</style>
</head><body>${media}<script>
const media = document.getElementById("video");
const send = (message) => window.ReactNativeWebView?.postMessage(JSON.stringify(message));
const start = ${JSON.stringify(start)};
const playlist = ${JSON.stringify(source.playlist ?? null)};
let latest;
function sample(position, duration, index, count, rate, ended = false, force = false) {
  if (!Number.isFinite(duration) || duration <= 0 || !Number.isFinite(position)) return;
  const newItem = !latest || latest.index !== index || latest.count !== count;
  if (newItem && !ended && position <= 0.75) position = 0;
  if (!newItem && !force && Math.abs(latest.position - position) < 3) return;
  if (!newItem && latest.ended && ended) return;
  latest = { index, count, position, ended };
  send({
    type: "progress",
    sample: {
      position_seconds: Math.min(duration, Math.max(0, position)),
      duration_seconds: duration,
      item_index: index,
      item_count: count,
      playback_rate: Math.min(2, Math.max(0.25, rate || 1)),
      ended,
    },
  });
}

if (${source.youtube}) {
  let player, item, timer;
  function poll(force, ended) {
    const playing = player.getPlayerState() === 1;
    if (!playing && !force) return;
    const playlistSize = player.getPlaylist?.()?.length || 0;
    const index = playlist ? player.getPlaylistIndex() : 0;
    if (playlist && (!playlistSize || index < 0 || index >= playlistSize)) return;
    const count = playlist ? playlistSize : 1;
    const duration = player.getDuration();
    const position = player.getCurrentTime();
    const rate = player.getPlaybackRate();
    // Playlist advancement may change the current item before the end callback.
    if (ended && item && item.index !== index) {
      if (item.position >= item.duration - 2)
        sample(item.duration, item.duration, item.index, item.count, item.rate, true, true);
      return;
    }
    item = { position, duration, index, count, rate };
    sample(ended ? duration : position, duration, index, count, rate, ended, force);
  }
  window.onYouTubeIframeAPIReady = () => {
    new YT.Player(media, {
      events: {
        onReady: ({ target }) => {
          player = target;
          if (playlist && (start.item > 0 || start.seconds > 0)) {
            player.cuePlaylist({
              listType: "playlist",
              list: playlist,
              index: start.item,
              startSeconds: start.seconds,
            });
          }
          send({ type: "ready" });
          timer = setInterval(() => poll(false, false), 500);
        },
        onStateChange: ({ data }) => {
          if (!player) return;
          if (data === 0) poll(true, true);
          else if (data === 1 || data === 2) poll(true, false);
        },
        onError: ({ data }) => send({ type: "error", code: data }),
      },
    });
  };
  const script = document.createElement("script");
  script.src = "https://www.youtube.com/iframe_api";
  script.onerror = () => send({ type: "error" });
  document.head.append(script);
  addEventListener("pagehide", () => clearInterval(timer));
} else {
  const report = (force, ended = false) =>
    sample(media.currentTime, media.duration, 0, 1, media.playbackRate, ended, force);
  media.addEventListener("loadedmetadata", () => {
    if (start.seconds > 0 && start.seconds < media.duration) media.currentTime = start.seconds;
    send({ type: "ready" });
  });
  let played = false;
  media.addEventListener("play", () => { played = true; report(true); });
  media.addEventListener("pause", () => { if (!media.ended) report(true); });
  media.addEventListener("seeked", () => { if (played) report(true); });
  media.addEventListener("timeupdate", () => { if (!media.paused && !media.seeking) report(false); });
  media.addEventListener("ended", () => report(true, true));
  media.addEventListener("error", () => send({ type: "error" }));
}
</script></body></html>`;
}
