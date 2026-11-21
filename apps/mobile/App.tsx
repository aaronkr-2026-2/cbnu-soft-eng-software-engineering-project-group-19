import { Image as CourseImage } from "expo-image";
import * as SecureStore from "expo-secure-store";
import { StatusBar } from "expo-status-bar";
import { useCallback, useEffect, useRef, useState } from "react";
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
  resourceUrl,
  signIn,
} from "./api";
import type { Course, CourseLanguage, Lesson, Selection, Session, VideoProgress } from "./api";
import { color, styles } from "./styles";
import { Button, Content, ErrorNotice, useResource } from "./ui";
import { CertificatesScreen, CourseCompletion, QuizScreen } from "./Assessments";
import { LessonVideo } from "./LessonVideo";
import { LocaleContext, useTranslate } from "./localization";

const SESSION_KEY = "studyflow-learner-token";
const LANGUAGE_KEY = "studyflow-mobile-language";
const FOUNDER_PHOTO = { uri: WEB_APP + "founder.webp?v=portrait-2" };

function FounderProfile() {
  const t = useTranslate();
  const [photoAvailable, setPhotoAvailable] = useState(true);
  return (
    <View style={styles.founderCard}>
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
      <Text style={styles.category}>{t("founderRole")}</Text>
      <Text accessibilityRole="header" style={styles.founderName}>
        MUKHAMMADAZIZ YULDOSHBOEV
      </Text>
      <Text style={styles.body}>{t("founderBio")}</Text>
    </View>
  );
}

const aboutFeatures = [
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
}: {
  language: CourseLanguage;
  changeLanguage: (value: CourseLanguage) => void;
  openCourse: (selection: Selection) => void;
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

function Login({ onLogin, cancel }: { onLogin: (value: Session) => void; cancel: () => void }) {
  const t = useTranslate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>();

  async function submit() {
    if (pending || !email.trim() || !password) return;
    setPending(true);
    setError(undefined);
    try {
      const session = await signIn(email.trim(), password);
      await SecureStore.setItemAsync(SESSION_KEY, session.token);
      onLogin(session);
    } catch (failure) {
      setError(failure);
    } finally {
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
          {t("learnerAccount")}
        </Text>
        <Text style={styles.body}>{t("loginHelp")}</Text>
        <TextInput
          style={styles.input}
          accessibilityLabel={t("email")}
          placeholder={t("email")}
          placeholderTextColor={color.muted}
          autoComplete="email"
          autoCapitalize="none"
          keyboardType="email-address"
          value={email}
          onChangeText={setEmail}
        />
        <TextInput
          style={styles.input}
          accessibilityLabel={t("password")}
          placeholder={t("password")}
          placeholderTextColor={color.muted}
          autoComplete="current-password"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
          onSubmitEditing={submit}
        />
        {error !== undefined && <ErrorNotice error={error} />}
        <Button
          title={pending ? t("signingIn") : t("signIn")}
          onPress={submit}
          disabled={pending || !email.trim() || !password}
        />
        <Button title={t("backToCatalog")} onPress={cancel} disabled={pending} secondary />
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
}: {
  session: Session;
  language: CourseLanguage;
  openCourse: (selection: Selection) => void;
  onSignOut: () => void;
  onExpired: () => void;
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
}: {
  session: Session;
  selection: Selection;
  language: CourseLanguage;
  onExpired: () => void;
  back: () => void;
}) {
  const t = useTranslate();
  const { token } = session;
  const { id } = selection;
  const load = useCallback(
    (signal: AbortSignal) => loadCourse(token, selection, language, signal),
    [token, selection, language],
  );
  const { value, loading, error, refresh } = useResource(load);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [quizOpen, setQuizOpen] = useState(false);
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [actionError, setActionError] = useState<unknown>();
  const [working, setWorking] = useState(false);
  const [video, setVideo] = useState<VideoProgress>();
  const [updatedProgress, setUpdatedProgress] = useState(value?.progress);
  const progress = updatedProgress ?? value?.progress;
  const requireVideo =
    lesson?.resource_type === "video" && Boolean(lesson.resource_url || lesson.external_video_url);
  const done = Boolean(lesson && progress?.completed_lesson_ids.includes(lesson.id));

  useEffect(() => {
    const failure = actionError ?? error;
    if (failure instanceof ApiError && failure.status === 401) onExpired();
  }, [actionError, error, onExpired]);

  useEffect(() => {
    const subscription = BackHandler.addEventListener("hardwareBackPress", () => {
      if (!working && !quizSubmitting) {
        if (quizOpen) setQuizOpen(false);
        else if (lesson) setLesson(null);
        else back();
      }
      return true;
    });
    return () => subscription.remove();
  }, [back, lesson, quizOpen, quizSubmitting, working]);

  async function openWeb(url: string) {
    setActionError(undefined);
    try {
      await Linking.openURL(url);
    } catch (failure) {
      setActionError(failure);
    }
  }

  async function updateProgress() {
    setWorking(true);
    setActionError(undefined);
    try {
      const [latestProgress, videoProgress] = await Promise.all([
        loadProgress(token, id),
        requireVideo && lesson ? getVideoProgress(token, id, lesson.id) : undefined,
      ]);
      setUpdatedProgress(latestProgress);
      setVideo(videoProgress);
    } catch (failure) {
      setActionError(failure);
    } finally {
      setWorking(false);
    }
  }

  async function markDone() {
    if (!lesson || working) return;
    setWorking(true);
    setActionError(undefined);
    try {
      await completeLesson(token, id, lesson.id);
      setUpdatedProgress(await loadProgress(token, id));
    } catch (failure) {
      setActionError(failure);
    } finally {
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
      <Content key={lesson.id}>
        <Button
          title={t("backToLessons")}
          secondary
          disabled={working}
          onPress={() => setLesson(null)}
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
              onPress={() => openWeb(courseWebLink(id, { lesson: lesson.id }))}
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
      </Content>
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
              setLesson(item);
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
  const [selection, setSelection] = useState<Selection | null>(null);

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
    setSession(null);
    setLogin(true);
    void SecureStore.deleteItemAsync(SESSION_KEY).catch(setRestoreError);
  }, []);

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
          <Text style={styles.wordmark}>
            studyflow<Text style={styles.brandAccent}>.ai</Text>
          </Text>
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
          onLogin={(account) => {
            setSession(account);
            setLogin(false);
          }}
          cancel={cancelLogin}
        />
      ) : selection && session ? (
        <CourseScreen
          key={selection.id}
          session={session}
          selection={selection}
          language={language}
          onExpired={expireSession}
          back={() => setSelection(null)}
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
            />
          ) : (
            <Catalog
              key={language}
              language={language}
              changeLanguage={changeLanguage}
              openCourse={openCourse}
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
              <Text style={styles.filterText}>{t("catalog")}</Text>
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
              <Text style={styles.filterText}>{t("myCourses")}</Text>
            </Pressable>
            <Pressable
              accessibilityRole="tab"
              accessibilityState={{ selected: tab === "certificates" }}
              style={[styles.tab, tab === "certificates" && styles.activeTab]}
              onPress={() => {
                setTab("certificates");
                if (!session) setLogin(true);
              }}
            >
              <Text style={styles.filterText}>{t("myCertificates")}</Text>
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
              <Text style={styles.filterText}>{t("aboutTab")}</Text>
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
