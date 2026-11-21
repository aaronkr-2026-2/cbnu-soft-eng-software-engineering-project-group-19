const aboutCopy = {
  uz: {
    aboutTitle: "Dastur haqida",
    aboutIntro:
      "StudyFlow — veb-sayt va mobil ilova orqali o‘z maromingizda o‘rganish platformasi. Ikkalasida ham bitta hisob bilan kurslaringizni ochib, o‘qishni davom ettirishingiz mumkin.",
    aboutCoursesTitle: "Kurslar va video darslar",
    aboutCoursesBody:
      "O‘zbek, ingliz, rus yoki koreys tilidagi kursni tanlang. Video darslarni ilova ichida ko‘ring va saqlangan joydan davom eting.",
    aboutAssessmentTitle: "Quiz va yakuniy imtihon",
    aboutAssessmentBody:
      "Dars quizlari bilan bilimingizni tekshiring. Barcha darslar tugagach, yakuniy imtihon ochiladi.",
    aboutProgressTitle: "Progress va sertifikat",
    aboutProgressBody:
      "Bajarilgan darslar va natijalaringizni kuzating. Yakuniy imtihondan o‘tgach, sertifikatingizni olib, uni havola orqali tekshirishingiz mumkin.",
    founderRole: "StudyFlow asoschisi",
    founderBio:
      "Uning loyiha tajribasi web va mobil ilova, kurs va darslar, testlar hamda sertifikat olish oqimini bir platformaga birlashtirishni qamrab oladi.",
    backHome: "Bosh sahifaga qaytish",
    chooseLanguage: "Tilni tanlang",
  },
  en: {
    aboutTitle: "About StudyFlow",
    aboutIntro:
      "StudyFlow is a learning platform for studying at your own pace on the web and on your phone. Use the same account on both to open your courses and continue where you left off.",
    aboutCoursesTitle: "Courses and video lessons",
    aboutCoursesBody:
      "Choose a course in Uzbek, English, Russian, or Korean. Watch video lessons in the app and resume from your saved position.",
    aboutAssessmentTitle: "Quizzes and final exams",
    aboutAssessmentBody:
      "Check what you’ve learned with lesson quizzes. The final exam opens after you complete every lesson.",
    aboutProgressTitle: "Progress and certificates",
    aboutProgressBody:
      "Track your completed lessons and results. After passing the final exam, you can claim your certificate and verify it via its link.",
    founderRole: "Founder of StudyFlow",
    founderBio:
      "His project experience includes bringing web and mobile apps, courses and lessons, assessments, and certificate issuance together in one platform.",
    backHome: "Back to home",
    chooseLanguage: "Choose a language",
  },
  ru: {
    aboutTitle: "О StudyFlow",
    aboutIntro:
      "StudyFlow — платформа для самостоятельного обучения на сайте и в мобильном приложении. Ваши курсы и прогресс доступны на обоих устройствах через один аккаунт.",
    aboutCoursesTitle: "Курсы и видеоуроки",
    aboutCoursesBody:
      "Выбирайте курсы на узбекском, английском, русском или корейском языке. Смотрите видеоуроки в приложении и продолжайте с сохранённого места.",
    aboutAssessmentTitle: "Тесты и итоговые экзамены",
    aboutAssessmentBody:
      "Проверяйте знания с помощью тестов к урокам. Итоговый экзамен доступен после завершения всех уроков.",
    aboutProgressTitle: "Прогресс и сертификаты",
    aboutProgressBody:
      "Следите за завершёнными уроками и результатами. Сдав итоговый экзамен, вы сможете получить сертификат и проверить его по ссылке.",
    founderRole: "Основатель StudyFlow",
    founderBio:
      "Его опыт работы над проектом охватывает объединение сайта и мобильного приложения, курсов и уроков, тестов и выдачи сертификатов в одной платформе.",
    backHome: "На главную",
    chooseLanguage: "Выберите язык",
  },
  ko: {
    aboutTitle: "StudyFlow 소개",
    aboutIntro:
      "StudyFlow는 웹과 모바일에서 자신의 속도로 공부할 수 있는 학습 플랫폼입니다. 같은 계정으로 강의를 열고 학습을 이어갈 수 있습니다.",
    aboutCoursesTitle: "강의와 동영상 수업",
    aboutCoursesBody:
      "우즈베크어, 영어, 러시아어, 한국어 강의를 선택하세요. 앱에서 동영상 수업을 시청하고 저장된 위치에서 이어보세요.",
    aboutAssessmentTitle: "퀴즈와 최종 시험",
    aboutAssessmentBody:
      "수업 퀴즈로 배운 내용을 확인하세요. 모든 수업을 완료하면 최종 시험이 열립니다.",
    aboutProgressTitle: "학습 진도와 수료증",
    aboutProgressBody:
      "완료한 수업과 결과를 확인하세요. 최종 시험에 통과하면 수료증을 발급받고 링크로 확인할 수 있습니다.",
    founderRole: "StudyFlow 설립자",
    founderBio:
      "웹과 모바일 앱, 강의와 수업, 평가, 수료증 발급을 하나의 플랫폼으로 통합한 프로젝트 경험이 있습니다.",
    backHome: "홈으로 돌아가기",
    chooseLanguage: "언어 선택",
  },
};

const aboutLanguage = document.getElementById("aboutLanguage");

function updateAboutLanguage(language) {
  const code = Object.hasOwn(aboutCopy, language) ? language : "uz";
  const messages = aboutCopy[code];
  document.documentElement.lang = code;
  document.title = messages.aboutTitle + " · StudyFlow";
  aboutLanguage.value = code;
  aboutLanguage.setAttribute("aria-label", messages.chooseLanguage);
  document.querySelectorAll("[data-about-copy]").forEach((element) => {
    element.textContent = messages[element.dataset.aboutCopy];
  });
}

updateAboutLanguage(localStorage.getItem("studyflow-language"));
aboutLanguage.addEventListener("change", () => {
  localStorage.setItem("studyflow-language", aboutLanguage.value);
  updateAboutLanguage(aboutLanguage.value);
});
