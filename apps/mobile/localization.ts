import { createContext, useContext } from "react";
import type { CourseLanguage } from "./api";

const languageIndex: Record<CourseLanguage, number> = { uz: 0, en: 1, ru: 2, ko: 3 };

const messages = {
  catalogTitle: ["Kurslar katalogi", "Course catalog", "Каталог курсов", "강의 카탈로그"],
  searchCourses: ["Kurs qidirish", "Search courses", "Поиск курсов", "강의 검색"],
  noMatchingCourses: [
    "Mos kurs topilmadi.",
    "No matching courses.",
    "Подходящих курсов не найдено.",
    "검색 결과가 없습니다.",
  ],
  free: ["Bepul", "Free", "Бесплатно", "무료"],
  openCourse: ["Kursni ochish", "Open course", "Открыть курс", "강의 열기"],
  learnerAccount: ["O‘quvchi hisobi", "Learner account", "Аккаунт учащегося", "학습자 계정"],
  loginHelp: [
    "StudyFlow’da ishlatgan emailingiz va parolingiz bilan kiring.",
    "Sign in with your StudyFlow email and password.",
    "Войдите с адресом почты и паролем от StudyFlow.",
    "StudyFlow에서 사용한 이메일과 비밀번호로 로그인하세요.",
  ],
  email: ["Email", "Email", "Электронная почта", "이메일"],
  password: ["Parol", "Password", "Пароль", "비밀번호"],
  signingIn: ["Kirilmoqda…", "Signing in…", "Выполняется вход…", "로그인 중…"],
  signIn: ["Kirish", "Sign in", "Войти", "로그인"],
  backToCatalog: [
    "Katalogga qaytish",
    "Back to catalog",
    "Вернуться в каталог",
    "카탈로그로 돌아가기",
  ],
  catalog: ["Katalog", "Catalog", "Каталог", "카탈로그"],
  myCourses: ["Kurslarim", "My courses", "Мои курсы", "내 강의"],
  noEnrollments: [
    "Hali kursga yozilmagansiz.",
    "You haven’t enrolled in any courses yet.",
    "Вы пока не записались ни на один курс.",
    "아직 등록한 강의가 없습니다.",
  ],
  signOut: ["Hisobdan chiqish", "Sign out", "Выйти", "로그아웃"],
  accountLoading: ["Hisob yuklanmoqda", "Loading account", "Загрузка аккаунта", "계정 불러오는 중"],
  backToLessons: [
    "Darslar ro‘yxatiga qaytish",
    "Back to lessons",
    "К списку уроков",
    "수업 목록으로 돌아가기",
  ],
  openMaterial: [
    "Dars materialini ochish",
    "Open lesson material",
    "Открыть материал урока",
    "수업 자료 열기",
  ],
  videoProgress: [
    "Video progressi {progress}%",
    "Video progress {progress}%",
    "Просмотрено {progress}% видео",
    "동영상 시청률 {progress}%",
  ],
  openBrowser: ["Brauzerda ochish", "Open in browser", "Открыть в браузере", "브라우저에서 열기"],
  refreshVideo: [
    "Video progressini yangilash",
    "Refresh video progress",
    "Обновить ход просмотра",
    "동영상 진행률 새로고침",
  ],
  takeQuiz: ["Dars quizini ishlash", "Take lesson quiz", "Пройти тест урока", "수업 퀴즈 풀기"],
  lessonDone: ["✓ Dars tugallangan", "✓ Lesson completed", "✓ Урок завершён", "✓ 수업 완료"],
  refreshing: ["Yangilanmoqda…", "Updating…", "Обновление…", "업데이트 중…"],
  markComplete: ["Tugatdim", "Mark complete", "Отметить как завершённый", "수업 완료하기"],
  back: ["Orqaga", "Back", "Назад", "뒤로"],
  paidWeb: [
    "Pulli kursga StudyFlow veb-sayti orqali yozilish mumkin.",
    "Enroll in paid courses on the StudyFlow website.",
    "Записаться на платный курс можно на сайте StudyFlow.",
    "유료 강의는 StudyFlow 웹사이트에서 등록할 수 있습니다.",
  ],
  openWebsite: [
    "StudyFlow veb-saytini ochish",
    "Open the StudyFlow website",
    "Открыть сайт StudyFlow",
    "StudyFlow 웹사이트 열기",
  ],
  lessonsDone: [
    "{done}/{total} dars bajarildi",
    "{done}/{total} lessons completed",
    "Завершено уроков: {done}/{total}",
    "수업 {done}/{total}개 완료",
  ],
  courseProgress: [
    "Kurs progressi {progress}%",
    "Course progress {progress}%",
    "Прогресс курса {progress}%",
    "강의 진행률 {progress}%",
  ],
  noLessons: [
    "Bu kursda hali dars yo‘q.",
    "This course has no lessons yet.",
    "В этом курсе пока нет уроков.",
    "이 강의에는 아직 수업이 없습니다.",
  ],
  completedLessonLabel: [
    "{title}, tugallangan",
    "{title}, completed",
    "{title}, завершён",
    "{title}, 완료",
  ],
  examLocked: [
    "Yakuniy imtihon barcha darslar tugagach ochiladi.",
    "Complete all lessons to unlock the final exam.",
    "Завершите все уроки, чтобы открыть итоговый экзамен.",
    "모든 수업을 완료하면 최종 시험이 열립니다.",
  ],
  myCertificates: ["Sertifikatlarim", "My certificates", "Мои сертификаты", "내 수료증"],
  retry: ["Qayta urinish", "Try again", "Повторить", "다시 시도"],
  genericError: [
    "Xato yuz berdi. Qayta urinib ko‘ring.",
    "Something went wrong. Try again.",
    "Произошла ошибка. Попробуйте ещё раз.",
    "오류가 발생했습니다. 다시 시도하세요.",
  ],
  connectionError: [
    "Serverga ulanib bo‘lmadi. Internetni tekshiring va qayta urining.",
    "Couldn't reach the server. Check your connection and try again.",
    "Не удалось связаться с сервером. Проверьте интернет и повторите попытку.",
    "서버에 연결할 수 없습니다. 인터넷 연결을 확인하고 다시 시도하세요.",
  ],
  invalidCredentials: [
    "O‘quvchi hisobining email manzili va parolini tekshiring.",
    "Check your learner account email and password.",
    "Проверьте почту и пароль аккаунта учащегося.",
    "학습자 계정의 이메일과 비밀번호를 확인하세요.",
  ],
  learnerRequired: [
    "StudyFlow o‘quvchi hisobi bilan kiring.",
    "Sign in with a StudyFlow learner account.",
    "Войдите в аккаунт учащегося StudyFlow.",
    "StudyFlow 학습자 계정으로 로그인하세요.",
  ],
  signInAgain: [
    "Davom etish uchun qayta kiring.",
    "Sign in again to continue.",
    "Войдите снова, чтобы продолжить.",
    "계속하려면 다시 로그인하세요.",
  ],
  accessDenied: [
    "Bu amal uchun ruxsatingiz yo‘q.",
    "You don’t have access to this action.",
    "У вас нет доступа к этому действию.",
    "이 작업을 수행할 권한이 없습니다.",
  ],
  notFound: [
    "So‘ralgan ma’lumot topilmadi.",
    "The requested item was not found.",
    "Запрошенные данные не найдены.",
    "요청한 항목을 찾을 수 없습니다.",
  ],
  tooManyRequests: [
    "So‘rovlar juda ko‘p. Biroz kutib, qayta urining.",
    "Too many requests. Wait a moment and try again.",
    "Слишком много запросов. Подождите и попробуйте снова.",
    "요청이 너무 많습니다. 잠시 후 다시 시도하세요.",
  ],
  videoRequired: [
    "Darsni tugatish uchun videoni oxirigacha ko‘ring.",
    "Watch the video to the end to complete this lesson.",
    "Досмотрите видео до конца, чтобы завершить урок.",
    "수업을 완료하려면 동영상을 끝까지 시청하세요.",
  ],
  saveLanguageError: [
    "Til sozlamasini saqlab bo‘lmadi.",
    "Couldn't save your language preference.",
    "Не удалось сохранить выбранный язык.",
    "언어 설정을 저장할 수 없습니다.",
  ],
  passed: ["O‘tdingiz", "Passed", "Зачёт", "통과"],
  failed: ["O‘tmadingiz", "Not passed", "Не зачтено", "미통과"],
  quizResult: [
    "{status} · {score}% · {correct}/{total} to‘g‘ri",
    "{status} · {score}% · {correct}/{total} correct",
    "{status} · {score}% · верных ответов {correct}/{total}",
    "{status} · {score}% · 정답 {correct}/{total}",
  ],
  backToLesson: ["Darsga qaytish", "Back to lesson", "Вернуться к уроку", "수업으로 돌아가기"],
  quizLoading: ["Quiz yuklanmoqda", "Loading quiz", "Загрузка теста", "퀴즈 불러오는 중"],
  noQuiz: [
    "Bu darsda hali quiz yo‘q.",
    "This lesson has no quiz yet.",
    "В этом уроке пока нет теста.",
    "이 수업에는 아직 퀴즈가 없습니다.",
  ],
  passingScore: [
    "O‘tish bali {score}%",
    "Passing score {score}%",
    "Проходной балл {score}%",
    "통과 기준 {score}%",
  ],
  retakeQuiz: ["Qayta ishlash", "Retake quiz", "Пройти тест снова", "퀴즈 다시 풀기"],
  submitting: ["Yuborilmoqda…", "Submitting…", "Отправка…", "제출 중…"],
  submitAnswers: ["Javoblarni yuborish", "Submit answers", "Отправить ответы", "답안 제출"],
  previousAttempts: [
    "Avvalgi urinishlar",
    "Previous attempts",
    "Предыдущие попытки",
    "이전 응시 기록",
  ],
  viewCertificate: [
    "Sertifikatni ko‘rish",
    "View certificate",
    "Посмотреть сертификат",
    "수료증 보기",
  ],
  examLoading: [
    "Imtihon holati yuklanmoqda",
    "Loading exam status",
    "Загрузка статуса экзамена",
    "시험 상태 불러오는 중",
  ],
  finalExam: ["Yakuniy imtihon", "Final exam", "Итоговый экзамен", "최종 시험"],
  examPassed: [
    "Imtihondan o‘tdingiz.",
    "You passed the exam.",
    "Вы сдали экзамен.",
    "시험을 통과했습니다.",
  ],
  latestScore: [
    "Oxirgi natija {score}%.",
    "Latest score {score}%.",
    "Последний результат {score}%.",
    "최근 점수 {score}%.",
  ],
  confirmPasskey: [
    "Brauzerda shu hisob bilan kiring va passkey bilan tasdiqlang.",
    "In your browser, sign in with the same account and verify with your passkey.",
    "В браузере войдите в тот же аккаунт и подтвердите действие ключом доступа.",
    "브라우저에서 같은 계정으로 로그인하고 패스키로 인증하세요.",
  ],
  getCertificate: ["Sertifikat olish", "Get certificate", "Получить сертификат", "수료증 받기"],
  openExam: [
    "Imtihonni brauzerda ochish",
    "Open exam in browser",
    "Открыть экзамен в браузере",
    "브라우저에서 시험 열기",
  ],
  noExam: [
    "Bu kursning yakuniy imtihoni hali tayyor emas.",
    "This course’s final exam isn’t available yet.",
    "Итоговый экзамен для этого курса пока недоступен.",
    "이 강의의 최종 시험은 아직 준비되지 않았습니다.",
  ],
  refreshStatus: ["Holatni yangilash", "Refresh status", "Обновить статус", "상태 새로고침"],
  noCertificates: [
    "Hali sertifikat berilmagan.",
    "You don’t have a certificate yet.",
    "У вас пока нет сертификатов.",
    "아직 발급된 수료증이 없습니다.",
  ],
  videoLoadError: [
    "Video yuklanmadi. Qayta urinib ko‘ring.",
    "Video couldn’t load. Try again.",
    "Не удалось загрузить видео. Повторите попытку.",
    "동영상을 불러올 수 없습니다. 다시 시도하세요.",
  ],
  videoSourceError: [
    "Video manzili ilovada ochilmadi.",
    "This video link couldn’t open in the app.",
    "Не удалось открыть ссылку на видео в приложении.",
    "앱에서 이 동영상 링크를 열 수 없습니다.",
  ],
  loadingSavedPosition: [
    "Saqlangan joy yuklanmoqda",
    "Loading saved position",
    "Загрузка сохранённой позиции",
    "저장된 위치 불러오는 중",
  ],
  openFromStart: [
    "Videoni boshidan ochish",
    "Open video from the beginning",
    "Открыть видео с начала",
    "동영상을 처음부터 열기",
  ],
  youtubeRestricted: [
    "YouTube bu videoni ilova ichida ochishga ruxsat bermadi.",
    "YouTube doesn’t allow this video to play in the app.",
    "YouTube не разрешает воспроизводить это видео в приложении.",
    "YouTube에서 이 동영상의 앱 내 재생을 허용하지 않습니다.",
  ],
  videoPlaybackError: [
    "Videoni ijro qilib bo‘lmadi. Qayta urinib ko‘ring.",
    "Video couldn’t play. Try again.",
    "Не удалось воспроизвести видео. Повторите попытку.",
    "동영상을 재생할 수 없습니다. 다시 시도하세요.",
  ],
  videoServerError: [
    "Video serveri javob bermadi.",
    "The video server didn’t respond.",
    "Видеосервер не ответил.",
    "동영상 서버가 응답하지 않습니다.",
  ],
  resumePosition: [
    "Davom etish nuqtasi {time}",
    "Resume at {time}",
    "Продолжить с {time}",
    "{time}부터 이어보기",
  ],
  resumePlaylist: [
    "Davom etish nuqtasi {item}-video, {time}",
    "Resume at video {item}, {time}",
    "Продолжить с видео {item}, {time}",
    "{item}번째 동영상 {time}부터 이어보기",
  ],
  restartVideo: [
    "Boshidan ko‘rish",
    "Watch from the beginning",
    "Смотреть с начала",
    "처음부터 보기",
  ],
  videoLoading: ["Video yuklanmoqda", "Loading video", "Загрузка видео", "동영상 불러오는 중"],
  reloadVideo: [
    "Videoni qayta yuklash",
    "Reload video",
    "Перезагрузить видео",
    "동영상 다시 불러오기",
  ],
  videoTrackingError: [
    "Video progressini saqlab bo‘lmadi. Internet aloqasini tekshiring.",
    "Couldn’t save video progress. Check your connection.",
    "Не удалось сохранить прогресс просмотра. Проверьте интернет.",
    "동영상 진행률을 저장하지 못했습니다. 인터넷 연결을 확인하세요.",
  ],
  youtubeVideo: ["YouTube videosi", "YouTube video", "Видео YouTube", "YouTube 동영상"],
} satisfies Record<string, [string, string, string, string]>;

export type MessageKey = keyof typeof messages;
export const LocaleContext = createContext<CourseLanguage>("uz");

export function useLocale() {
  return useContext(LocaleContext);
}

type Values = Record<string, string | number>;

export function translate(language: CourseLanguage, key: MessageKey, values: Values = {}) {
  return messages[key][languageIndex[language]].replace(/\{(\w+)\}/g, (_, field: string) => {
    const value = values[field];
    return typeof value === "number" ? value.toLocaleString(language) : (value ?? "");
  });
}

export function useTranslate() {
  const language = useLocale();
  return (key: MessageKey, values?: Values) => translate(language, key, values);
}
