import * as SecureStore from "expo-secure-store";
import { StatusBar } from "expo-status-bar";
import { useCallback, useEffect, useState } from "react";
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
import type { CourseLanguage, Lesson, Selection, Session } from "./api";
import { color, styles } from "./styles";
import { Button, Content, ErrorNotice, useResource } from "./ui";
import { CertificatesScreen, CourseCompletion, QuizScreen } from "./Assessments";

const SESSION_KEY = "studyflow-learner-token";

function Catalog({
  language,
  changeLanguage,
  openCourse,
}: {
  language: CourseLanguage;
  changeLanguage: (value: CourseLanguage) => void;
  openCourse: (selection: Selection) => void;
}) {
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
        Kurslar katalogi
      </Text>
      <TextInput
        style={styles.input}
        accessibilityLabel="Kurs qidirish"
        placeholder="Kurs qidirish"
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
        <Text style={styles.muted}>Mos kurs topilmadi.</Text>
      )}
      {matches.map((course) => {
        const banner = course.banner_url && resourceUrl(course.banner_url);
        return (
          <View key={course.id} style={styles.card}>
            {banner ? (
              <Image
                accessibilityIgnoresInvertColors
                source={{ uri: banner }}
                style={styles.banner}
              />
            ) : null}
            <View style={styles.cardBody}>
              <Text style={styles.category}>{course.category}</Text>
              <Text accessibilityRole="header" style={styles.cardTitle}>
                {course.title}
              </Text>
              {course.description && <Text style={styles.body}>{course.description}</Text>}
              <Text style={styles.category}>
                {course.price_uzs > 0 ? `${course.price_uzs.toLocaleString("uz")} so‘m` : "Bepul"}
              </Text>
              <Button
                title="Kursni ochish"
                onPress={() =>
                  openCourse({ id: course.id, title: course.title, price: course.price_uzs })
                }
              />
            </View>
          </View>
        );
      })}
    </Content>
  );
}

function Login({ onLogin, cancel }: { onLogin: (value: Session) => void; cancel: () => void }) {
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
          O‘quvchi hisobi
        </Text>
        <Text style={styles.body}>
          StudyFlow’da ishlatgan emailingiz va parolingiz bilan kiring.
        </Text>
        <TextInput
          style={styles.input}
          accessibilityLabel="Email"
          placeholder="Email"
          placeholderTextColor={color.muted}
          autoComplete="email"
          autoCapitalize="none"
          keyboardType="email-address"
          value={email}
          onChangeText={setEmail}
        />
        <TextInput
          style={styles.input}
          accessibilityLabel="Parol"
          placeholder="Parol"
          placeholderTextColor={color.muted}
          autoComplete="current-password"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
          onSubmitEditing={submit}
        />
        {error !== undefined && <ErrorNotice error={error} />}
        <Button
          title={pending ? "Kirilmoqda…" : "Kirish"}
          onPress={submit}
          disabled={pending || !email.trim() || !password}
        />
        <Button title="Katalogga qaytish" onPress={cancel} disabled={pending} secondary />
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
        Kurslarim
      </Text>
      <Text style={styles.muted}>{session.name}</Text>
      {error !== undefined && <ErrorNotice error={error} retry={refresh} />}
      {!loading && value?.length === 0 && (
        <Text style={styles.body}>Hali kursga yozilmagansiz.</Text>
      )}
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
      <Button title="Hisobdan chiqish" onPress={onSignOut} secondary />
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
  const [video, setVideo] = useState<{ completion_percent: number; can_complete: boolean }>();
  const [updatedProgress, setUpdatedProgress] = useState(value?.progress);
  const progress = updatedProgress ?? value?.progress;
  const lessonId = lesson?.id;
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

  useEffect(() => {
    if (!requireVideo || !lessonId) return;
    const controller = new AbortController();
    getVideoProgress(token, id, lessonId, controller.signal).then(
      (result) => {
        if (!controller.signal.aborted) setVideo(result);
      },
      (failure: unknown) => {
        if (!controller.signal.aborted) setActionError(failure);
      },
    );
    return () => controller.abort();
  }, [id, lessonId, requireVideo, token]);

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
          title="Darslar ro‘yxatiga qaytish"
          secondary
          disabled={working}
          onPress={() => setLesson(null)}
        />
        <Text accessibilityRole="header" style={styles.title}>
          {lesson.title}
        </Text>
        <Text style={styles.body}>{lesson.content}</Text>
        {media ? (
          <Button
            title="Dars materialini ochish"
            secondary
            onPress={() => {
              void Linking.openURL(media).catch(setActionError);
            }}
          />
        ) : null}
        {requireVideo && (
          <View style={styles.notice}>
            <Text style={styles.body}>
              Video brauzerda ochiladi. So‘ralsa, shu o‘quvchi hisobi bilan kiring.
            </Text>
            <Button
              title="Videoni webda ochish"
              onPress={() => openWeb(courseWebLink(id, { lesson: lesson.id }))}
            />
            <Button
              title="Video progressini yangilash"
              onPress={updateProgress}
              disabled={working}
              secondary
            />
            {video && (
              <Text style={styles.muted}>
                Video progressi {Math.floor(video.completion_percent)}%
              </Text>
            )}
          </View>
        )}
        <Button
          title="Dars quizini ishlash"
          onPress={() => setQuizOpen(true)}
          disabled={working}
          secondary
        />
        {actionError !== undefined && <ErrorNotice error={actionError} />}
        {done ? (
          <Text accessibilityRole="text" style={styles.category}>
            ✓ Dars tugallangan
          </Text>
        ) : (
          <Button
            title={working ? "Yangilanmoqda…" : "Tugatdim"}
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
      <Button title="Orqaga" onPress={back} secondary />
      <Text accessibilityRole="header" style={styles.title}>
        {selection.title}
      </Text>
      {error !== undefined &&
        (error instanceof ApiError && error.status === 402 ? (
          <View style={styles.notice}>
            <Text style={styles.body}>
              Pulli kursga StudyFlow veb-sayti orqali yozilish mumkin.
            </Text>
            <Button
              title="StudyFlow veb-saytini ochish"
              onPress={() => openWeb(WEB_APP + "#courses")}
            />
          </View>
        ) : (
          <ErrorNotice error={error} retry={refresh} />
        ))}
      {actionError !== undefined && <ErrorNotice error={actionError} />}
      {progress && (
        <View style={styles.progressCard}>
          <Text style={styles.category}>
            {progress.completed_lessons}/{progress.total_lessons} dars bajarildi
          </Text>
          <Text style={styles.percent}>{progress.progress_percent}%</Text>
          <View
            style={styles.track}
            accessibilityLabel={`Kurs progressi ${progress.progress_percent}%`}
          >
            <View style={[styles.trackFill, { width: `${progress.progress_percent}%` }]} />
          </View>
        </View>
      )}
      {value?.lessons.length === 0 && <Text style={styles.muted}>Bu kursda hali dars yo‘q.</Text>}
      {value?.lessons.map((item) => {
        const completed = progress?.completed_lesson_ids.includes(item.id);
        return (
          <Pressable
            key={item.id}
            accessibilityRole="button"
            accessibilityLabel={completed ? `${item.title}, tugallangan` : item.title}
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
          <Text style={styles.muted}>Yakuniy imtihon barcha darslar tugagach ochiladi.</Text>
        ))}
    </Content>
  );
}

function StudyFlow() {
  const [restoring, setRestoring] = useState(true);
  const [restoreError, setRestoreError] = useState<unknown>();
  const [session, setSession] = useState<Session | null>(null);
  const [language, setLanguage] = useState<CourseLanguage>("uz");
  const [tab, setTab] = useState<"catalog" | "mine" | "certificates">("catalog");
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
          <Button title="Kirish" onPress={() => setLogin(true)} secondary />
        )}
      </View>
      {restoreError !== undefined && (
        <ErrorNotice error={restoreError} retry={() => void restore()} />
      )}
      {restoring ? (
        <ActivityIndicator
          accessibilityLabel="Hisob yuklanmoqda"
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
          {tab === "certificates" && session ? (
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
              changeLanguage={setLanguage}
              openCourse={openCourse}
            />
          )}
          <View style={styles.tabBar}>
            <Pressable
              accessibilityRole="tab"
              accessibilityState={{ selected: tab === "catalog" }}
              style={[styles.tab, tab === "catalog" && styles.activeTab]}
              onPress={() => setTab("catalog")}
            >
              <Text style={styles.filterText}>Katalog</Text>
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
              <Text style={styles.filterText}>Kurslarim</Text>
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
              <Text style={styles.filterText}>Sertifikatlarim</Text>
            </Pressable>
          </View>
        </>
      )}
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <StudyFlow />
    </SafeAreaProvider>
  );
}
