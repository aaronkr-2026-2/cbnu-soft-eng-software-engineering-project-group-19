export const API_ORIGIN = (
  process.env.EXPO_PUBLIC_STUDYFLOW_API_URL || "https://studyflow-web-1hab.vercel.app"
).replace(/\/$/, "");
export const WEB_APP = "https://studyflow-web-1hab.vercel.app/app/";

export const languages = { uz: "O‘zbekcha", en: "English", ru: "Русский", ko: "한국어" };
export type CourseLanguage = keyof typeof languages;

export type Course = {
  id: string;
  title: string;
  description: string | null;
  category: string;
  price_uzs: number;
  banner_url: string | null;
};

export type Enrollment = { course_id: string; course_title: string };
export type Selection = { id: string; title: string; price?: number };
export type Lesson = {
  id: string;
  title: string;
  content: string;
  position: number;
  resource_type: "text" | "video" | "audio" | "pdf";
  resource_url: string | null;
  external_video_url: string | null;
};
export type Progress = {
  completed_lessons: number;
  completed_lesson_ids: string[];
  total_lessons: number;
  progress_percent: number;
};
export type Session = { token: string; name: string };

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(
  path: string,
  options: { signal?: AbortSignal; body?: object; token?: string; method?: "POST" } = {},
): Promise<T> {
  const controller = new AbortController();
  const cancel = () => controller.abort();
  options.signal?.addEventListener("abort", cancel, { once: true });
  if (options.signal?.aborted) cancel();
  const timer = setTimeout(cancel, 45_000);
  try {
    const response = await fetch(API_ORIGIN + path, {
      method: options.method ?? "GET",
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
        ...(options.body ? { "Content-Type": "application/json" } : {}),
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = payload?.detail;
      throw new ApiError(
        response.status,
        typeof detail === "string" ? detail : "So‘rovni bajarib bo‘lmadi.",
      );
    }
    if (payload === null) throw new Error("Serverdan javobni o‘qib bo‘lmadi.");
    return payload;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (options.signal?.aborted) throw error;
    if (controller.signal.aborted || error instanceof TypeError)
      throw new Error("Serverga ulanib bo‘lmadi. Internetni tekshirib, qayta urining.");
    throw error;
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", cancel);
  }
}

export async function loadSession(token: string): Promise<Session> {
  const profile = await request<{ full_name: string; account_type: string }>("/auth/me", { token });
  if (profile.account_type !== "learner")
    throw new ApiError(403, "StudyFlow o‘quvchi hisobi bilan kiring.");
  return { token, name: profile.full_name };
}

export async function signIn(email: string, password: string): Promise<Session> {
  try {
    const { access_token } = await request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: { email, password, account_type: "learner" },
    });
    return await loadSession(access_token);
  } catch (error) {
    if (error instanceof ApiError && [401, 403, 422].includes(error.status))
      throw new Error("O‘quvchi hisobining email manzili va parolini tekshiring.");
    throw error;
  }
}

export function getCatalog(language: CourseLanguage, signal: AbortSignal) {
  return request<Course[]>(`/courses/catalog?language=${language}`, { signal });
}

export function getEnrollments(token: string, language: CourseLanguage, signal: AbortSignal) {
  return request<Enrollment[]>(`/enrollments/me?language=${language}`, { token, signal });
}

export function loadProgress(token: string, courseId: string, signal?: AbortSignal) {
  return request<Progress>(`/courses/${courseId}/progress/me`, { token, signal });
}

export async function loadCourse(
  token: string,
  selection: Selection,
  language: CourseLanguage,
  signal: AbortSignal,
) {
  const course = `/courses/${selection.id}`;
  if (selection.price !== undefined) {
    try {
      await request<Enrollment>(course + "/enroll", { method: "POST", token, signal });
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 409)) throw error;
    }
  }
  const [lessons, progress] = await Promise.all([
    request<Lesson[]>(course + `/lessons?language=${language}`, { token, signal }),
    loadProgress(token, selection.id, signal),
  ]);
  return { lessons, progress };
}

export function completeLesson(token: string, courseId: string, lessonId: string) {
  return request<{ lesson_id: string }>(
    `/courses/${courseId}/progress/lessons/${lessonId}/complete`,
    { method: "POST", token },
  );
}

export function getVideoProgress(
  token: string,
  courseId: string,
  lessonId: string,
  signal?: AbortSignal,
) {
  return request<VideoProgress>(`/courses/${courseId}/progress/lessons/${lessonId}/video-watch`, {
    token,
    signal,
  });
}

export type VideoProgress = { completion_percent: number; can_complete: boolean };
export type PlaybackSample = {
  position_seconds: number;
  duration_seconds: number;
  item_index: number;
  item_count: number;
  playback_rate: number;
  ended: boolean;
};

export function reportVideoProgress(
  token: string,
  courseId: string,
  lessonId: string,
  sample: PlaybackSample,
  signal: AbortSignal,
) {
  return request<VideoProgress>(`/courses/${courseId}/progress/lessons/${lessonId}/video-watch`, {
    token,
    signal,
    method: "POST",
    body: sample,
  });
}

export function resourceUrl(value: string) {
  try {
    const url = new URL(value, API_ORIGIN);
    return url.protocol === "https:" || url.origin === API_ORIGIN ? url.toString() : null;
  } catch {
    return null;
  }
}

export type Answer = { question_id: string; selected_index: number };
export type Quiz = {
  id: string;
  title: string;
  passing_score: number;
  questions: { id: string; prompt: string; choices: string[] }[];
};
export type QuizAttempt = {
  id: string;
  correct_count: number;
  total_questions: number;
  score_percent: number;
  passed: boolean;
  submitted_at: string;
};
export type Certificate = {
  certificate_code: string;
  course_title: string;
  recipient_name: string;
  score_percent: number;
  issued_at: string;
};
type Exam = { title: string; passing_score: number; passed: boolean; latest_score: number | null };

export function getQuiz(
  token: string,
  course: string,
  lesson: string,
  language: CourseLanguage,
  signal: AbortSignal,
) {
  return request<Quiz>(`/courses/${course}/lessons/${lesson}/quiz?language=${language}`, {
    token,
    signal,
  });
}

export function getQuizAttempts(
  token: string,
  course: string,
  lesson: string,
  signal: AbortSignal,
) {
  return request<QuizAttempt[]>(`/courses/${course}/lessons/${lesson}/quiz/attempts/me`, {
    token,
    signal,
  });
}

export function submitQuiz(token: string, course: string, lesson: string, answers: Answer[]) {
  return request<QuizAttempt>(`/courses/${course}/lessons/${lesson}/quiz/attempts`, {
    token,
    method: "POST",
    body: { answers },
  });
}

function optionalResponse<T>(promise: Promise<T>, missingStatus: number) {
  return promise.catch((error: unknown) => {
    if (error instanceof ApiError && error.status === missingStatus) return null;
    throw error;
  });
}

function getCertificate(token: string, course: string, signal: AbortSignal) {
  return optionalResponse(
    request<Certificate>(`/courses/${course}/certificate/me`, { token, signal }),
    404,
  );
}

export async function getCourseCompletion(
  token: string,
  course: string,
  language: CourseLanguage,
  signal: AbortSignal,
) {
  const [exam, certificate] = await Promise.all([
    optionalResponse(
      request<Exam>(`/courses/${course}/final-exam?language=${language}`, { token, signal }),
      409,
    ),
    getCertificate(token, course, signal),
  ]);
  return { exam, certificate };
}

export async function getCertificates(
  token: string,
  language: CourseLanguage,
  signal: AbortSignal,
) {
  const enrollments = await getEnrollments(token, language, signal);
  const certificates = await Promise.all(
    enrollments.map(({ course_id }) => getCertificate(token, course_id, signal)),
  );
  return certificates
    .filter((certificate) => certificate !== null)
    .sort((first, second) => Date.parse(second.issued_at) - Date.parse(first.issued_at));
}

export function courseWebLink(course: string, destination: { lesson: string } | "completion") {
  const query =
    typeof destination === "string"
      ? "view=completion"
      : `lesson=${encodeURIComponent(destination.lesson)}`;
  return `${WEB_APP}?course=${encodeURIComponent(course)}&${query}`;
}

export function certificateWebLink(code: string) {
  return `${WEB_APP}verify.html?code=${encodeURIComponent(code)}`;
}
