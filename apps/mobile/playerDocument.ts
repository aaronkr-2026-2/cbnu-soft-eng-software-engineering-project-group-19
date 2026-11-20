import { WEB_APP, resourceUrl } from "./api";
import type { CourseLanguage, Lesson } from "./api";

const playerOrigin = new URL(WEB_APP).origin;

export type VideoSource = { uri: string; youtube: boolean };

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
          return { uri: embed.toString(), youtube: true };
        }
      }
    } catch {
      // An invalid external URL can still have a playable uploaded version.
    }
  }
  const uri = lesson.resource_url && resourceUrl(lesson.resource_url);
  return uri ? { uri, youtube: false } : null;
}

export function playerDocument(source: VideoSource) {
  const attributes = source.uri
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
    const count = Math.max(1, player.getPlaylist?.()?.length || 0);
    const index = Math.max(0, player.getPlaylistIndex?.() ?? 0);
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
  media.addEventListener("loadedmetadata", () => send({ type: "ready" }));
  media.addEventListener("play", () => report(true));
  media.addEventListener("pause", () => { if (!media.ended) report(true); });
  media.addEventListener("seeked", () => report(true));
  media.addEventListener("timeupdate", () => { if (!media.paused && !media.seeking) report(false); });
  media.addEventListener("ended", () => report(true, true));
  media.addEventListener("error", () => send({ type: "error" }));
}
</script></body></html>`;
}
