import { ApiError } from "./api";
import type { PlaybackSample, VideoProgress } from "./api";

const FIRST_RETRY_MS = 1_000;
const MAX_RETRY_MS = 30_000;

export function createPlaybackProgressQueue({
  signal,
  send,
  onSaved,
  onError,
  onExpired,
}: {
  signal: AbortSignal;
  send: (sample: PlaybackSample) => Promise<VideoProgress>;
  onSaved: (progress: VideoProgress) => void;
  onError: () => void;
  onExpired: () => void;
}) {
  const pending: PlaybackSample[] = [];
  let sending = false;
  let stopped = false;
  let retry: ReturnType<typeof setTimeout> | undefined;
  let retryMs = FIRST_RETRY_MS;

  function stop() {
    stopped = true;
    if (retry !== undefined) clearTimeout(retry);
    pending.length = 0;
  }

  signal.addEventListener("abort", stop, { once: true });

  async function flush() {
    if (sending || retry !== undefined || stopped || signal.aborted) return;
    sending = true;
    try {
      while (!signal.aborted) {
        const sample = pending.shift();
        if (!sample) break;
        let progress: VideoProgress;
        try {
          progress = await send(sample);
        } catch (error) {
          if (signal.aborted) break;
          if (error instanceof ApiError && error.status === 401) {
            stop();
            onExpired();
            break;
          }
          onError();
          if (
            error instanceof ApiError &&
            (error.status === 0 ||
              error.status === 408 ||
              error.status === 429 ||
              error.status >= 500)
          ) {
            const next = pending[0];
            if (sample.ended || next?.item_index !== sample.item_index) pending.unshift(sample);
            retry = setTimeout(() => {
              retry = undefined;
              void flush();
            }, retryMs);
            retryMs = Math.min(retryMs * 2, MAX_RETRY_MS);
            break;
          }
          continue;
        }
        if (signal.aborted) break;
        retryMs = FIRST_RETRY_MS;
        onSaved(progress);
      }
    } finally {
      sending = false;
    }
  }

  return (sample: PlaybackSample) => {
    if (stopped || signal.aborted) return;
    const previous = pending.at(-1);
    if (previous && !previous.ended && previous.item_index === sample.item_index) pending.pop();
    pending.push(sample);
    void flush();
  };
}
