import { Image as CourseImage } from "expo-image";
import * as SecureStore from "expo-secure-store";
import { StatusBar } from "expo-status-bar";
import { useCallback, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  ActivityIndicator,
  BackHandler,
  Image,
  KeyboardAvoidingView,
  Linking,
  Platform,
  Pressable,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import {
  ApiError,
  WEB_APP,
  completeLesson,
  courseWebLink,
  getCatalog,
  getEnrollments,
  getVideoProgress,
  languages,
  loadCourse,
  loadProgress,
  loadSession,
  requestPasswordReset,
  resourceUrl,
  signIn,
} from "./api";
import type { Course, CourseLanguage, Lesson, Selection, Session, VideoProgress } from "./api";
import { color, styles } from "./styles";
import { Button, Content, ErrorNotice, PasswordInput, useRefreshOnReturn, useResource } from "./ui";
import { CertificatesScreen, CourseCompletion, QuizScreen } from "./Assessments";
import { ChangePassword } from "./ChangePassword";
import { LessonVideo } from "./LessonVideo";
import { LessonNote } from "./LessonNote";
import { LocaleContext, useTranslate } from "./localization";

const SESSION_KEY = "studyflow-learner-token";
const LANGUAGE_KEY = "studyflow-mobile-language";
const FOUNDER_PHOTO = { uri: WEB_APP + "founder.webp?v=portrait-2" };
const RESUME_KEY_PREFIX = "studyflow-resume-";
const ID_PATTERN = /^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i;
type ResumeLesson = { id: string; title: string; lessonId: string; lessonTitle: string };

function ResumeCard({ lesson, open }: { lesson: ResumeLesson; open: () => void }) {
  const t = useTranslate();
  return (
    <View style={styles.resumeCard}>
      <Text style={styles.category}>{lesson.title}</Text>
      <Text style={styles.listTitle}>{lesson.lessonTitle}</Text>
      <Button title={t("resumeLearning")} onPress={open} />
    </View>
  );
}

function FounderProfile() {
  const t = useTranslate();
  const [photoAvailable, setPhotoAvailable] = useState(true);
  return (
    <View style={styles.founderCard}>
      <View style={styles.founderHeader}>
        <View
          style={styles.founderPhoto}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        >
          <Text style={styles.founderInitials}>MY</Text>
          {photoAvailable && (
            <Image
              source={FOUNDER_PHOTO}
              style={styles.founderImage}
              onError={() => setPhotoAvailable(false)}
            />
          )}
        </View>
        <View
          style={styles.founderIdentity}
          accessible
          accessibilityRole="header"
          accessibilityLabel={`MUKHAMMADAZIZ YULDOSHBOEV, ${t("founderRole")}`}
        >
          <View style={styles.founderRoleChip}>
            <Text style={styles.founderRole}>{t("founderRole")}</Text>
          </View>
          <View>
            <Text
              style={styles.founderName}
              numberOfLines={1}
              adjustsFontSizeToFit
              minimumFontScale={0.62}
            >
              MUKHAMMADAZIZ
            </Text>
            <Text
              style={styles.founderName}
              numberOfLines={1}
              adjustsFontSizeToFit
              minimumFontScale={0.62}
            >
              YULDOSHBOEV
            </Text>
          </View>
        </View>
      </View>
      <Text style={styles.founderBio}>{t("founderBio")}</Text>
    </View>
  );
}

const aboutFeatures = [
  ["aboutNameTitle", "aboutNameBody"],
  ["aboutCoursesTitle", "aboutCoursesBody"],
  ["aboutAssessmentTitle", "aboutAssessmentBody"],
  ["aboutProgressTitle", "aboutProgressBody"],
] as const;

function AboutScreen() {
  const t = useTranslate();
  return (
    <Content>
      <View style={styles.aboutHero}>
        <Text accessibilityRole="header" style={styles.aboutTitle}>
          {t("aboutTitle")}
        </Text>
        <Text style={styles.aboutLead}>{t("aboutIntro")}</Text>
      </View>
      {aboutFeatures.map(([title, body]) => (
        <View key={title} style={styles.aboutFeature}>
          <Text accessibilityRole="header" style={styles.listTitle}>
            {t(title)}
          </Text>
          <Text style={styles.muted}>{t(body)}</Text>
        </View>
      ))}
      <FounderProfile />
    </Content>
  );
}

function CatalogCover({ course }: { course: Course }) {
  const [failed, setFailed] = useState(false);
  const uri = course.banner_url && resourceUrl(course.banner_url);
  return (
    <View
      style={styles.banner}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {uri && !failed ? (
        <CourseImage
          source={uri}
          contentFit="cover"
          cachePolicy="memory-disk"
          style={styles.fill}
          onError={() => setFailed(true)}
        />
      ) : (
        <Text style={styles.bannerMark}>
          {Array.from(course.title.trim())[0]?.toUpperCase() || "S"}
        </Text>
      )}
    </View>
  );
}

function Catalog({
  language,
  changeLanguage,
  openCourse,
  resumeCard,
}: {
  language: CourseLanguage;
  changeLanguage: (value: CourseLanguage) => void;
  openCourse: (selection: Selection) => void;
  resumeCard: ReactNode;
}) {
  const t = useTranslate();
  const load = useCallback((signal: AbortSignal) => getCatalog(language, signal), [language]);
  const { value, loading, error, refresh } = useResource(load);
  const [query, setQuery] = useState("");
  const matches = (value ?? []).filter((course) =>
    `${course.title} ${course.category} ${course.description ?? ""}`
      .toLocaleLowerCase(language)
      .includes(query.trim().toLocaleLowerCase(language)),
  );

  return (
    <Content refreshing={loading} refresh={refresh}>
      <Text accessibilityRole="header" style={styles.title}>
        {t("catalogTitle")}
      </Text>
      {resumeCard}
      <TextInput
        style={styles.input}
        accessibilityLabel={t("searchCourses")}
        placeholder={t("searchCourses")}
        placeholderTextColor={color.muted}
        value={query}
        onChangeText={setQuery}
        clearButtonMode="while-editing"
      />
      <View style={styles.filters}>
        {(Object.keys(languages) as CourseLanguage[]).map((key) => (
          <Pressable
            key={key}
            accessibilityRole="button"
            accessibilityState={{ selected: language === key }}
            onPress={() => changeLanguage(key)}
            style={[styles.filter, key === language && styles.selectedFilter]}
          >
            <Text style={styles.filterText}>{languages[key]}</Text>
          </Pressable>
        ))}
      </View>
      {error !== undefined && <ErrorNotice error={error} retry={refresh} />}
      {!loading && value && matches.length === 0 && (
        <Text style={styles.muted}>{t("noMatchingCourses")}</Text>
      )}
      {matches.map((course) => (
        <View key={course.id} style={styles.card}>
          <CatalogCover key={course.banner_url ?? ""} course={course} />
          <View style={styles.cardBody}>
            <Text style={styles.category}>{course.category}</Text>
            <Text accessibilityRole="header" style={styles.cardTitle}>
              {course.title}
            </Text>
            {course.description && <Text style={styles.body}>{course.description}</Text>}
            <Text style={styles.category}>
              {course.price_uzs > 0
                ? new Intl.NumberFormat(language, { style: "currency", currency: "UZS" }).format(
                    course.price_uzs,
                  )
                : t("free")}
            </Text>
            <Button
              title={t("openCourse")}
              onPress={() =>
                openCourse({ id: course.id, title: course.title, price: course.price_uzs })
              }
            />
          </View>
        </View>
      ))}
    </Content>
  );
}

function Login({
  onLogin,
  cancel,
  passwordChanged,
}: {
  onLogin: (value: Session) => void;
  cancel: () => void;
  passwordChanged: boolean;
}) {
  const t = useTranslate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>();
  const [resetMode, setResetMode] = useState(false);
  const [resetSent, setResetSent] = useState(false);
  const submitting = useRef(false);

  const switchResetMode = useCallback((value: boolean) => {
    if (submitting.current) return;
    setError(undefined);
    setPassword("");
    setResetMode(value);
    setResetSent(false);
  }, []);

  useEffect(() => {
    if (!resetMode) return;
    const subscription = BackHandler.addEventListener("hardwareBackPress", () => {
      switchResetMode(false);
      return true;
    });
    return () => subscription.remove();
  }, [resetMode, switchResetMode]);

  async function submit() {
    const address = email.trim();
    if (submitting.current || !address || (resetMode ? resetSent : !password)) return;
    submitting.current = true;
    setPending(true);
    setError(undefined);
    try {
      if (resetMode) {
        await requestPasswordReset(address);
        setResetSent(true);
      } else {
        const session = await signIn(address, password);
        await SecureStore.setItemAsync(SESSION_KEY, session.token);
        onLogin(session);
      }
    } catch (failure) {
      setError(failure);
    } finally {
      submitting.current = false;
      setPending(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.fill}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <Content>
        <Text accessibilityRole="header" style={styles.title}>
          {t(resetMode ? "resetPassword" : "learnerAccount")}
        </Text>
        {!resetSent && (
          <Text style={styles.body}>{t(resetMode ? "resetPasswordHelp" : "loginHelp")}</Text>
        )}
        {passwordChanged && !resetMode && (
          <View style={styles.passwordSuccess}>
            <Text accessibilityRole="alert" style={styles.body}>
              {t("passwordChanged")}
            </Text>
          </View>
        )}
        {resetSent ? (
          <View style={styles.passwordSuccess}>
            <Text accessibilityRole="alert" style={styles.body}>
              {t("resetLinkSent")}
            </Text>
          </View>
        ) : (
          <TextInput
            style={styles.input}
            accessibilityLabel={t("email")}
            placeholder={t("email")}
            placeholderTextColor={color.muted}
            autoComplete="email"
            autoCapitalize="none"
            keyboardType="email-address"
            editable={!pending}
            value={email}
            onChangeText={setEmail}
            onSubmitEditing={resetMode ? submit : undefined}
          />
        )}
        {!resetMode && (
          <PasswordInput
            label={t("password")}
            autoComplete="current-password"
            editable={!pending}
            value={password}
            onChangeText={setPassword}
            onSubmitEditing={submit}
          />
        )}
        {error !== undefined && <ErrorNotice error={error} />}
        {!resetSent && (
          <Button
            title={t(
              resetMode
                ? pending
                  ? "sendingResetLink"
                  : "sendResetLink"
                : pending
                  ? "signingIn"
                  : "signIn",
            )}
            onPress={submit}
            disabled={pending || !email.trim() || (!resetMode && !password)}
          />
        )}
        {resetMode ? (
          <Button
            title={t("backToSignIn")}
            onPress={() => switchResetMode(false)}
            disabled={pending}
            secondary
          />
        ) : (
          <>
            <Button
              title={t("forgotPassword")}
              onPress={() => switchResetMode(true)}
              disabled={pending}
              secondary
            />
            <Button title={t("backToCatalog")} onPress={cancel} disabled={pending} secondary />
          </>
        )}
      </Content>
    </KeyboardAvoidingView>
  );
}

function MyCourses({
  session,
  language,
  openCourse,
  onSignOut,
  onExpired,
  onChangePassword,
  resumeCard,
}: {
  session: Session;
  language: CourseLanguage;
  openCourse: (selection: Selection) => void;
  onSignOut: () => void;
  onExpired: () => void;
  onChangePassword: () => void;
  resumeCard: ReactNode;
}) {
  const t = useTranslate();
  const load = useCallback(
    (signal: AbortSignal) => getEnrollments(session.token, language, signal),
    [session.token, language],
  );
  const { value, loading, error, refresh } = useResource(load);
  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) onExpired();
  }, [error, onExpired]);
  return (
    <Content refreshing={loading} refresh={refresh}>
      <Text accessibilityRole="header" style={styles.title}>
        {t("myCourses")}
      </Text>
      <Text style={styles.muted}>{session.name}</Text>
      {resumeCard}
      <Button title={t("changePassword")} onPress={onChangePassword} secondary />
      {error !== undefined && <ErrorNotice error={error} retry={refresh} />}
      {!loading && value?.length === 0 && <Text style={styles.body}>{t("noEnrollments")}</Text>}
      {value?.map((course) => (
        <Pressable
          key={course.course_id}
          accessibilityRole="button"
          onPress={() => openCourse({ id: course.course_id, title: course.course_title })}
          style={styles.listItem}
        >
          <Text style={[styles.listTitle, styles.fill]}>{course.course_title}</Text>
          <Text style={styles.category} accessibilityElementsHidden>
            →
          </Text>
        </Pressable>
      ))}
      <Button title={t("signOut")} onPress={onSignOut} secondary />
    </Content>
  );
}

function CourseScreen({
  session,
  selection,
  language,
  onExpired,
  back,
  rememberLesson,
  clearResume,
}: {
  session: Session;
  selection: Selection;
  language: CourseLanguage;
  onExpired: () => void;
  back: () => void;
  rememberLesson: (lesson: Lesson, course: Selection) => void;
  clearResume: (courseId: string, lessonId: string) => void;
}) {
  const t = useTranslate();
  const { token } = session;
  const { id } = selection;
  const load = useCallback(
    (signal: AbortSignal) => loadCourse(token, selection, language, signal),
    [token, selection, language],
  );
  const { value, loading, error, refresh } = useResource(load);
  const [openedLessonId, setOpenedLessonId] = useState(selection.lessonId);
  const lesson = value?.lessons.find(({ id }) => id === openedLessonId);
  const initialResume = useRef(selection.lessonId);
  const [quizOpen, setQuizOpen] = useState(false);
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [actionError, setActionError] = useState<unknown>();
  const [working, setWorking] = useState(false);
  const [video, setVideo] = useState<VideoProgress>();
  const [updatedProgress, setUpdatedProgress] = useState(value?.progress);
  const pendingWebLesson = useRef<string | null>(null);
  const progressBusy = useRef(false);
  const lessonId = lesson?.id;
  const progress = updatedProgress ?? value?.progress;
  const requireVideo =
    lesson?.resource_type === "video" && Boolean(lesson.resource_url || lesson.external_video_url);
  const done = Boolean(lesson && progress?.completed_lesson_ids.includes(lesson.id));

  useEffect(() => {
    const failure = actionError ?? error;
    if (failure instanceof ApiError && failure.status === 401) onExpired();
  }, [actionError, error, onExpired]);

  useEffect(() => {
    const savedId = initialResume.current;
    if (!savedId) return;
    const unavailable = error instanceof ApiError && [403, 404].includes(error.status);
    if (unavailable || (value && !value.lessons.some(({ id }) => id === savedId))) {
      initialResume.current = undefined;
      clearResume(id, savedId);
      setOpenedLessonId((current) => (current === savedId ? undefined : current));
    }
  }, [clearResume, error, id, value]);

  useEffect(() => {
    const subscription = BackHandler.addEventListener("hardwareBackPress", () => {
      if (!working && !quizSubmitting) {
        if (quizOpen) setQuizOpen(false);
        else if (lesson) setOpenedLessonId(undefined);
        else back();
      }
      return true;
    });
    return () => subscription.remove();
  }, [back, lesson, quizOpen, quizSubmitting, working]);

  async function openWeb(url: string, webLessonId?: string) {
    if (webLessonId) pendingWebLesson.current = webLessonId;
    setActionError(undefined);
    try {
      await Linking.openURL(url);
    } catch (failure) {
      if (webLessonId && pendingWebLesson.current === webLessonId) pendingWebLesson.current = null;
      setActionError(failure);
    }
  }

  const updateProgress = useCallback(async () => {
    if (progressBusy.current) return;
    progressBusy.current = true;
    setWorking(true);
    setActionError(undefined);
    try {
      const [latestProgress, videoProgress] = await Promise.all([
        loadProgress(token, id),
        requireVideo && lessonId ? getVideoProgress(token, id, lessonId) : undefined,
      ]);
      setUpdatedProgress(latestProgress);
      setVideo(videoProgress);
    } catch (failure) {
      setActionError(failure);
    } finally {
      progressBusy.current = false;
      setWorking(false);
    }
  }, [id, lessonId, requireVideo, token]);

  const refreshAfterWebVideo = useCallback(() => {
    if (!lessonId || pendingWebLesson.current !== lessonId) return;
    pendingWebLesson.current = null;
    void updateProgress();
  }, [lessonId, updateProgress]);

  useRefreshOnReturn(refreshAfterWebVideo);

  async function markDone() {
    if (!lesson || progressBusy.current) return;
    progressBusy.current = true;
    setWorking(true);
    setActionError(undefined);
    try {
      await completeLesson(token, id, lesson.id);
      setUpdatedProgress(await loadProgress(token, id));
    } catch (failure) {
      setActionError(failure);
    } finally {
      progressBusy.current = false;
      setWorking(false);
    }
  }

  if (lesson && quizOpen) {
    return (
      <QuizScreen
        token={token}
        course={id}
        lesson={lesson.id}
        language={language}
        onExpired={onExpired}
        back={() => setQuizOpen(false)}
        onSubmitting={setQuizSubmitting}
      />
    );
  }

  if (lesson) {
    const media =
      lesson.resource_type !== "video" && lesson.resource_url && resourceUrl(lesson.resource_url);
    return (
      <KeyboardAvoidingView
        key={lesson.id}
        style={styles.fill}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <Content>
          <Button
            title={t("backToLessons")}
            secondary
            disabled={working}
            onPress={() => setOpenedLessonId(undefined)}
          />
          <Text accessibilityRole="header" style={styles.title}>
            {lesson.title}
          </Text>
          {media ? (
            <Button
              title={t("openMaterial")}
              secondary
              onPress={() => {
                void Linking.openURL(media).catch(setActionError);
              }}
            />
          ) : null}
          {requireVideo && (
            <View style={styles.notice}>
              <LessonVideo
                course={id}
                lesson={lesson}
                token={token}
                language={language}
                onProgress={setVideo}
                onExpired={onExpired}
              />
              {video && (
                <Text accessibilityLiveRegion="polite" style={styles.muted}>
                  {t("videoProgress", { progress: Math.floor(video.completion_percent) })}
                </Text>
              )}
              <Button
                title={t("openBrowser")}
                onPress={() => openWeb(courseWebLink(id, { lesson: lesson.id }), lesson.id)}
                disabled={working}
                secondary
              />
              <Button
                title={t("refreshVideo")}
                onPress={updateProgress}
                disabled={working}
                secondary
              />
            </View>
          )}
          <Text style={styles.body}>{lesson.content}</Text>
          {!!lesson.materials?.length && (
            <View style={styles.notice}>
              <Text accessibilityRole="header" style={styles.listTitle}>
                {t("supplementalMaterials")}
              </Text>
              {lesson.materials.map((material) => (
                <Button
                  key={material.id}
                  title={material.title}
                  onPress={() => {
                    const url = resourceUrl(material.resource_url);
                    if (url) void openWeb(url);
                  }}
                  secondary
                />
              ))}
            </View>
          )}
          <Button
            title={t("takeQuiz")}
            onPress={() => setQuizOpen(true)}
            disabled={working}
            secondary
          />
          {actionError !== undefined && <ErrorNotice error={actionError} />}
          {done ? (
            <Text accessibilityRole="text" style={styles.category}>
              {t("lessonDone")}
            </Text>
          ) : (
            <Button
              title={working ? t("refreshing") : t("markComplete")}
              onPress={markDone}
              disabled={working || (requireVideo && !video?.can_complete)}
            />
          )}
          <LessonNote accountId={session.id} lessonId={lesson.id} />
        </Content>
      </KeyboardAvoidingView>
    );
  }

  return (
    <Content
      refreshing={loading}
      refresh={() => {
        setUpdatedProgress(undefined);
        refresh();
      }}
    >
      <Button title={t("back")} onPress={back} secondary />
      <Text accessibilityRole="header" style={styles.title}>
        {selection.title}
      </Text>
      {error !== undefined &&
        (error instanceof ApiError && error.status === 402 ? (
          <View style={styles.notice}>
            <Text style={styles.body}>{t("paidWeb")}</Text>
            <Button title={t("openWebsite")} onPress={() => openWeb(WEB_APP + "#courses")} />
          </View>
        ) : (
          <ErrorNotice error={error} retry={refresh} />
        ))}
      {actionError !== undefined && <ErrorNotice error={actionError} />}
      {progress && (
        <View style={styles.progressCard}>
          <Text style={styles.category}>
            {t("lessonsDone", { done: progress.completed_lessons, total: progress.total_lessons })}
          </Text>
          <Text style={styles.percent}>{progress.progress_percent.toLocaleString(language)}%</Text>
          <View
            style={styles.track}
            accessibilityLabel={t("courseProgress", { progress: progress.progress_percent })}
          >
            <View style={[styles.trackFill, { width: `${progress.progress_percent}%` }]} />
          </View>
        </View>
      )}
      {value?.lessons.length === 0 && <Text style={styles.muted}>{t("noLessons")}</Text>}
      {value?.lessons.map((item) => {
        const completed = progress?.completed_lesson_ids.includes(item.id);
        return (
          <Pressable
            key={item.id}
            accessibilityRole="button"
            accessibilityLabel={
              completed ? t("completedLessonLabel", { title: item.title }) : item.title
            }
            style={styles.listItem}
            onPress={() => {
              setVideo(undefined);
              setActionError(undefined);
              setOpenedLessonId(item.id);
              rememberLesson(item, selection);
            }}
          >
            <Text style={styles.step}>{completed ? "✓" : item.position}</Text>
            <Text style={[styles.listTitle, styles.fill]}>{item.title}</Text>
            <Text style={styles.category} accessibilityElementsHidden>
              →
            </Text>
          </Pressable>
        );
      })}
      {progress &&
        progress.total_lessons > 0 &&
        (progress.completed_lessons === progress.total_lessons ? (
          <CourseCompletion
            token={token}
            course={id}
            language={language}
            onExpired={onExpired}
            onOpen={openWeb}
          />
        ) : (
          <Text style={styles.muted}>{t("examLocked")}</Text>
        ))}
    </Content>
  );
}

function StudyFlow({
  language,
  changeLanguage,
  languageError,
}: {
  language: CourseLanguage;
  changeLanguage: (language: CourseLanguage) => void;
  languageError: boolean;
}) {
  const t = useTranslate();
  const [restoring, setRestoring] = useState(true);
  const [restoreError, setRestoreError] = useState<unknown>();
  const [session, setSession] = useState<Session | null>(null);
  const [tab, setTab] = useState<"catalog" | "mine" | "certificates" | "about">("catalog");
  const lastLearnerTab = useRef<"catalog" | "mine" | "certificates">("catalog");
  const [login, setLogin] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [passwordChanged, setPasswordChanged] = useState(false);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [resume, setResume] = useState<{ accountId: string; lesson: ResumeLesson | null }>();
  const savingResume = useRef(Promise.resolve());
  const accountId = session?.id;

  useEffect(() => {
    if (!accountId) return;
    let current = true;
    void savingResume.current
      .then(() => SecureStore.getItemAsync(RESUME_KEY_PREFIX + accountId))
      .then((raw) => {
        if (!current || !raw) return;
        const saved = JSON.parse(raw);
        if (
          typeof saved?.id !== "string" ||
          !ID_PATTERN.test(saved.id) ||
          typeof saved.lessonId !== "string" ||
          !ID_PATTERN.test(saved.lessonId) ||
          typeof saved.title !== "string" ||
          typeof saved.lessonTitle !== "string"
        )
          return;
        const { id, title, lessonId, lessonTitle } = saved;
        setResume((previous) =>
          previous?.accountId === accountId
            ? previous
            : { accountId, lesson: { id, title, lessonId, lessonTitle } },
        );
      })
      .catch(() => {
        // Continue to show lessons when device storage is unavailable.
      });
    return () => {
      current = false;
    };
  }, [accountId]);

  const saveResume = useCallback(
    (lesson: ResumeLesson | null) => {
      if (!accountId) return;
      setResume({ accountId, lesson });
      const key = RESUME_KEY_PREFIX + accountId;
      savingResume.current = savingResume.current
        .then(() =>
          lesson
            ? SecureStore.setItemAsync(key, JSON.stringify(lesson))
            : SecureStore.deleteItemAsync(key),
        )
        .catch(() => {
          // The shortcut remains available in the current session.
        });
    },
    [accountId],
  );

  const savedLesson = resume?.accountId === accountId ? resume?.lesson : null;
  const clearResume = useCallback(
    (courseId: string, lessonId: string) => {
      if (savedLesson?.id === courseId && savedLesson.lessonId === lessonId) saveResume(null);
    },
    [saveResume, savedLesson],
  );

  function rememberLesson(lesson: Lesson, course: Selection) {
    saveResume({
      id: course.id,
      title: course.title,
      lessonId: lesson.id,
      lessonTitle: lesson.title,
    });
  }

  const resumeCard = savedLesson && (
    <ResumeCard lesson={savedLesson} open={() => setSelection(savedLesson)} />
  );

  const restore = useCallback(async () => {
    setRestoring(true);
    setRestoreError(undefined);
    try {
      const token = await SecureStore.getItemAsync(SESSION_KEY);
      if (token) setSession(await loadSession(token));
    } catch (error) {
      if (error instanceof ApiError && [401, 403].includes(error.status)) {
        await SecureStore.deleteItemAsync(SESSION_KEY).catch(setRestoreError);
      } else setRestoreError(error);
    } finally {
      setRestoring(false);
    }
  }, []);

  useEffect(() => {
    void restore();
  }, [restore]);

  useEffect(() => {
    if (tab !== "about" || login) return;
    const subscription = BackHandler.addEventListener("hardwareBackPress", () => {
      setTab(lastLearnerTab.current);
      return true;
    });
    return () => subscription.remove();
  }, [login, tab]);

  const expireSession = useCallback(() => {
    setChangingPassword(false);
    setSession(null);
    setLogin(true);
    void SecureStore.deleteItemAsync(SESSION_KEY).catch(setRestoreError);
  }, []);

  async function finishPasswordChange() {
    await SecureStore.deleteItemAsync(SESSION_KEY).catch(setRestoreError);
    setPasswordChanged(true);
    setChangingPassword(false);
    setSession(null);
    setLogin(true);
  }

  function openCourse(course: Selection) {
    setSelection(course);
    if (!session) setLogin(true);
  }

  async function logOut() {
    try {
      await SecureStore.deleteItemAsync(SESSION_KEY);
      setSession(null);
      setSelection(null);
      setTab("catalog");
    } catch (error) {
      setRestoreError(error);
    }
  }

  function cancelLogin() {
    setPasswordChanged(false);
    setLogin(false);
    setSelection(null);
    setTab("catalog");
  }

  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar style="dark" />
      <View style={styles.header}>
        <View style={styles.brand}>
          <Text style={styles.logo}>S</Text>
          <View style={styles.wordmarkGroup}>
            <Text style={styles.wordmark}>SCHOLWARD</Text>
            <Text style={styles.brandAccent}>Academy</Text>
          </View>
        </View>
        {!session && !login && !restoring && (
          <Button title={t("signIn")} onPress={() => setLogin(true)} secondary />
        )}
      </View>
      {languageError && (
        <Text accessibilityRole="alert" style={styles.error}>
          {t("saveLanguageError")}
        </Text>
      )}
      {restoreError !== undefined && (
        <ErrorNotice error={restoreError} retry={() => void restore()} />
      )}
      {restoring ? (
        <ActivityIndicator
          accessibilityLabel={t("accountLoading")}
          style={styles.fill}
          color={color.ink}
        />
      ) : login ? (
        <Login
          passwordChanged={passwordChanged}
          onLogin={(account) => {
            setPasswordChanged(false);
            setSession(account);
            setLogin(false);
          }}
          cancel={cancelLogin}
        />
      ) : changingPassword && session ? (
        <ChangePassword
          token={session.token}
          onChanged={finishPasswordChange}
          onExpired={expireSession}
          onBack={() => setChangingPassword(false)}
        />
      ) : selection && session ? (
        <CourseScreen
          key={selection.id}
          session={session}
          selection={selection}
          language={language}
          onExpired={expireSession}
          back={() => setSelection(null)}
          rememberLesson={rememberLesson}
          clearResume={clearResume}
        />
      ) : (
        <>
          {tab === "about" ? (
            <AboutScreen />
          ) : tab === "certificates" && session ? (
            <CertificatesScreen
              token={session.token}
              language={language}
              onExpired={expireSession}
            />
          ) : tab === "mine" && session ? (
            <MyCourses
              session={session}
              language={language}
              openCourse={openCourse}
              onSignOut={logOut}
              onExpired={expireSession}
              onChangePassword={() => setChangingPassword(true)}
              resumeCard={resumeCard}
            />
          ) : (
            <Catalog
              key={language}
              language={language}
              changeLanguage={changeLanguage}
              openCourse={openCourse}
              resumeCard={resumeCard}
            />
          )}
          <View style={styles.tabBar}>
            <Pressable
              accessibilityRole="tab"
              accessibilityState={{ selected: tab === "catalog" }}
              style={[styles.tab, tab === "catalog" && styles.activeTab]}
              onPress={() => {
                setTab("catalog");
              }}
            >
              <Text
                style={styles.tabLabel}
                numberOfLines={1}
                adjustsFontSizeToFit
                minimumFontScale={0.8}
              >
                {t("catalog")}
              </Text>
            </Pressable>
            <Pressable
              accessibilityRole="tab"
              accessibilityState={{ selected: tab === "mine" }}
              style={[styles.tab, tab === "mine" && styles.activeTab]}
              onPress={() => {
                setTab("mine");
                if (!session) setLogin(true);
              }}
            >
              <Text
                style={styles.tabLabel}
                numberOfLines={1}
                adjustsFontSizeToFit
                minimumFontScale={0.8}
              >
                {t("myCourses")}
              </Text>
            </Pressable>
            <Pressable
              accessibilityRole="tab"
              accessibilityLabel={t("myCertificates")}
              accessibilityState={{ selected: tab === "certificates" }}
              style={[styles.tab, tab === "certificates" && styles.activeTab]}
              onPress={() => {
                setTab("certificates");
                if (!session) setLogin(true);
              }}
            >
              <Text
                style={styles.tabLabel}
                numberOfLines={1}
                adjustsFontSizeToFit
                minimumFontScale={0.8}
              >
                {t("certificatesTab")}
              </Text>
            </Pressable>
            <Pressable
              accessibilityRole="tab"
              accessibilityLabel={t("aboutTitle")}
              accessibilityState={{ selected: tab === "about" }}
              style={[styles.tab, tab === "about" && styles.activeTab]}
              onPress={() => {
                if (tab !== "about") lastLearnerTab.current = tab;
                setTab("about");
              }}
            >
              <Text
                style={styles.tabLabel}
                numberOfLines={1}
                adjustsFontSizeToFit
                minimumFontScale={0.8}
              >
                {t("aboutTab")}
              </Text>
            </Pressable>
          </View>
        </>
      )}
    </SafeAreaView>
  );
}

export default function App() {
  const [language, setLanguage] = useState<CourseLanguage | null>(null);
  const [languageError, setLanguageError] = useState(false);
  const savingLanguage = useRef(Promise.resolve());

  useEffect(() => {
    SecureStore.getItemAsync(LANGUAGE_KEY).then(
      (value) =>
        setLanguage(value && Object.hasOwn(languages, value) ? (value as CourseLanguage) : "uz"),
      () => setLanguage("uz"),
    );
  }, []);

  function changeLanguage(value: CourseLanguage) {
    setLanguage(value);
    setLanguageError(false);
    savingLanguage.current = savingLanguage.current
      .then(() => SecureStore.setItemAsync(LANGUAGE_KEY, value))
      .then(
        () => setLanguageError(false),
        () => setLanguageError(true),
      );
  }

  return (
    <SafeAreaProvider>
      {language ? (
        <LocaleContext.Provider value={language}>
          <StudyFlow
            language={language}
            changeLanguage={changeLanguage}
            languageError={languageError}
          />
        </LocaleContext.Provider>
      ) : (
        <ActivityIndicator color={color.ink} style={styles.fill} />
      )}
    </SafeAreaProvider>
  );
}
