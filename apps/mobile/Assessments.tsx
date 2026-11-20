import { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, AppState, Linking, Pressable, Text, View } from "react-native";
import {
  ApiError,
  certificateWebLink,
  courseWebLink,
  getCertificates,
  getCourseCompletion,
  getQuiz,
  getQuizAttempts,
  submitQuiz,
} from "./api";
import type { Certificate, CourseLanguage, QuizAttempt } from "./api";
import { color, styles } from "./styles";
import { Button, Content, ErrorNotice, useResource } from "./ui";

type CourseProps = {
  token: string;
  course: string;
  language: CourseLanguage;
  onExpired: () => void;
};

function useSessionFailure(error: unknown, onExpired: () => void) {
  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) onExpired();
  }, [error, onExpired]);
}

function useRefreshOnReturn(refresh: () => void) {
  useEffect(() => {
    const subscription = AppState.addEventListener("change", (state) => {
      if (state === "active") refresh();
    });
    return () => subscription.remove();
  }, [refresh]);
}

function attemptText(attempt: QuizAttempt) {
  return `${attempt.passed ? "O‘tdingiz" : "O‘tmadingiz"} · ${attempt.score_percent}% · ${attempt.correct_count}/${attempt.total_questions} to‘g‘ri`;
}

export function QuizScreen({
  token,
  course,
  lesson,
  language,
  onExpired,
  back,
  onSubmitting,
}: CourseProps & { lesson: string; back: () => void; onSubmitting: (value: boolean) => void }) {
  const loadQuiz = useCallback(
    (signal: AbortSignal) => getQuiz(token, course, lesson, language, signal),
    [token, course, lesson, language],
  );
  const loadHistory = useCallback(
    (signal: AbortSignal) => getQuizAttempts(token, course, lesson, signal),
    [token, course, lesson],
  );
  const quiz = useResource(loadQuiz);
  const history = useResource(loadHistory);
  const [selected, setSelected] = useState<Record<string, number>>({});
  const [result, setResult] = useState<QuizAttempt | null>(null);
  const [submitError, setSubmitError] = useState<unknown>();
  const [sending, setSending] = useState(false);
  const inFlight = useRef(false);
  const missing = quiz.error instanceof ApiError && quiz.error.status === 404;
  const quizData = quiz.value;
  const canSubmit =
    !!quizData?.questions.length &&
    quizData.questions.every(({ id }) => selected[id] !== undefined);
  const attemptHistory = history.value?.filter((attempt) => attempt.id !== result?.id);
  useSessionFailure(quiz.error ?? history.error ?? submitError, onExpired);

  async function submit() {
    if (!quizData || !canSubmit || inFlight.current) return;
    inFlight.current = true;
    setSending(true);
    onSubmitting(true);
    setSubmitError(undefined);
    try {
      const answers = quizData.questions.map(({ id }) => ({
        question_id: id,
        selected_index: selected[id],
      }));
      setResult(await submitQuiz(token, course, lesson, answers));
      history.refresh();
    } catch (error) {
      setSubmitError(error);
    } finally {
      inFlight.current = false;
      setSending(false);
      onSubmitting(false);
    }
  }

  return (
    <Content>
      <Button title="Darsga qaytish" onPress={back} disabled={sending} secondary />
      {quiz.loading && !quizData && (
        <ActivityIndicator accessibilityLabel="Quiz yuklanmoqda" color={color.leaf} />
      )}
      {missing && <Text style={styles.muted}>Bu darsda hali quiz yo‘q.</Text>}
      {quiz.error !== undefined && !missing && (
        <ErrorNotice error={quiz.error} retry={quiz.refresh} />
      )}
      {quizData && (
        <>
          <Text accessibilityRole="header" style={styles.title}>
            {quizData.title}
          </Text>
          <Text style={styles.muted}>O‘tish bali {quizData.passing_score}%</Text>
          {quizData.questions.map((question, number) => (
            <View key={question.id} style={styles.notice}>
              <Text style={styles.listTitle}>
                {number + 1}. {question.prompt}
              </Text>
              {question.choices.map((choice, index) => {
                const checked = selected[question.id] === index;
                return (
                  <Pressable
                    key={index}
                    accessibilityRole="radio"
                    accessibilityState={{ checked, disabled: sending || !!result }}
                    disabled={sending || !!result}
                    onPress={() =>
                      setSelected((previous) => ({ ...previous, [question.id]: index }))
                    }
                    style={[styles.listItem, checked && styles.selectedFilter]}
                  >
                    <Text style={styles.category}>{String.fromCharCode(65 + index)}.</Text>
                    <Text style={[styles.body, styles.fill]}>{choice}</Text>
                  </Pressable>
                );
              })}
            </View>
          ))}
          {submitError !== undefined && <ErrorNotice error={submitError} />}
          {result ? (
            <View style={styles.notice}>
              <Text
                accessibilityLiveRegion="polite"
                style={result.passed ? styles.category : styles.error}
              >
                {attemptText(result)}
              </Text>
              <Button
                title="Qayta ishlash"
                onPress={() => {
                  setResult(null);
                  setSelected({});
                }}
                secondary
              />
            </View>
          ) : (
            <Button
              title={sending ? "Yuborilmoqda…" : "Javoblarni yuborish"}
              disabled={!canSubmit || sending}
              onPress={submit}
            />
          )}
          {history.error !== undefined && (
            <ErrorNotice error={history.error} retry={history.refresh} />
          )}
          {!!attemptHistory?.length && (
            <View style={styles.notice}>
              <Text accessibilityRole="header" style={styles.listTitle}>
                Avvalgi urinishlar
              </Text>
              {attemptHistory.map((attempt) => (
                <Text key={attempt.id} style={styles.body}>
                  {attemptText(attempt)} · {new Date(attempt.submitted_at).toLocaleDateString("uz")}
                </Text>
              ))}
            </View>
          )}
        </>
      )}
    </Content>
  );
}

function CertificateCard({
  certificate,
  onOpen,
}: {
  certificate: Certificate;
  onOpen: (url: string) => void;
}) {
  return (
    <View style={styles.notice}>
      <Text accessibilityRole="header" style={styles.listTitle}>
        {certificate.course_title}
      </Text>
      <Text style={styles.body}>
        {certificate.recipient_name} · {certificate.score_percent}%
      </Text>
      <Text style={styles.muted}>
        {certificate.certificate_code} · {new Date(certificate.issued_at).toLocaleDateString("uz")}
      </Text>
      <Button
        title="Sertifikatni ko‘rish"
        onPress={() => onOpen(certificateWebLink(certificate.certificate_code))}
        secondary
      />
    </View>
  );
}

export function CourseCompletion({
  token,
  course,
  language,
  onExpired,
  onOpen,
}: CourseProps & { onOpen: (url: string) => void }) {
  const load = useCallback(
    (signal: AbortSignal) => getCourseCompletion(token, course, language, signal),
    [token, course, language],
  );
  const { value, loading, error, refresh } = useResource(load);
  useRefreshOnReturn(refresh);
  useSessionFailure(error, onExpired);
  if (error !== undefined) return <ErrorNotice error={error} retry={refresh} />;
  if (loading && !value)
    return <ActivityIndicator accessibilityLabel="Imtihon holati yuklanmoqda" color={color.leaf} />;
  if (value?.certificate)
    return <CertificateCard certificate={value.certificate} onOpen={onOpen} />;
  const exam = value?.exam;
  return (
    <View style={styles.notice}>
      <Text accessibilityRole="header" style={styles.listTitle}>
        Yakuniy imtihon
      </Text>
      {exam ? (
        <>
          <Text style={styles.body}>
            {exam.passed ? "Imtihondan o‘tdingiz." : `O‘tish bali ${exam.passing_score}%.`}
            {exam.latest_score !== null ? ` Oxirgi natija ${exam.latest_score}%.` : ""}
          </Text>
          <Text style={styles.muted}>
            Brauzerda shu hisob bilan kiring va passkey bilan tasdiqlang.
          </Text>
          <Button
            title={exam.passed ? "Sertifikat olish" : "Webda imtihonni ochish"}
            onPress={() => onOpen(courseWebLink(course, "completion"))}
          />
        </>
      ) : (
        <Text style={styles.muted}>Bu kursning yakuniy imtihoni hali tayyor emas.</Text>
      )}
      <Button title="Holatni yangilash" onPress={refresh} disabled={loading} secondary />
    </View>
  );
}

export function CertificatesScreen({ token, language, onExpired }: Omit<CourseProps, "course">) {
  const load = useCallback(
    (signal: AbortSignal) => getCertificates(token, language, signal),
    [token, language],
  );
  const { value, loading, error, refresh } = useResource(load);
  const [linkError, setLinkError] = useState<unknown>();
  useRefreshOnReturn(refresh);
  useSessionFailure(error, onExpired);
  return (
    <Content refreshing={loading} refresh={refresh}>
      <Text accessibilityRole="header" style={styles.title}>
        Sertifikatlarim
      </Text>
      {error !== undefined && <ErrorNotice error={error} retry={refresh} />}
      {linkError !== undefined && <ErrorNotice error={linkError} />}
      {!loading && value?.length === 0 && (
        <Text style={styles.muted}>Hali sertifikat berilmagan.</Text>
      )}
      {value?.map((certificate) => (
        <CertificateCard
          key={certificate.certificate_code}
          certificate={certificate}
          onOpen={(url) => {
            setLinkError(undefined);
            void Linking.openURL(url).catch(setLinkError);
          }}
        />
      ))}
    </Content>
  );
}
