const verifyCopy = {
  uz: { languageLabel:"Tilni tanlang",verifyEyebrow:"RASMIY TEKSHIRUV",verifyTitle:"Sertifikat haqiqiyligini tekshiring",verifyBody:"Sertifikatdagi noyob kodni kiriting. Natija StudyFlow AI rasmiy reyestridan olinadi.",certificateCodeLabel:"Sertifikat kodi",verifySubmit:"Tekshirish",validTitle:"Sertifikat haqiqiy",validRecipient:"Ism-familiya",validCourse:"Kurs",validDate:"Berilgan sana",achievementLevel:"Sertifikat darajasi",certificateScore:"Imtihon bali",grade_bronze:"Boshlang‘ich",grade_silver:"O‘rta",grade_gold:"Yuqori",invalid:"Bu kod bo‘yicha sertifikat topilmadi.",error:"Tekshiruv vaqtida xatolik yuz berdi. Qayta urinib ko‘ring." },
  en: { languageLabel:"Choose language",verifyEyebrow:"OFFICIAL VERIFICATION",verifyTitle:"Verify a certificate",verifyBody:"Enter the unique code printed on the certificate. Results come from the official StudyFlow AI registry.",certificateCodeLabel:"Certificate code",verifySubmit:"Verify",validTitle:"Certificate is valid",validRecipient:"Recipient",validCourse:"Course",validDate:"Issue date",achievementLevel:"Certificate level",certificateScore:"Exam score",grade_bronze:"Foundation",grade_silver:"Intermediate",grade_gold:"Advanced",invalid:"No certificate was found for this code.",error:"Verification failed. Please try again." },
  ru: { languageLabel:"Выберите язык",verifyEyebrow:"ОФИЦИАЛЬНАЯ ПРОВЕРКА",verifyTitle:"Проверить подлинность сертификата",verifyBody:"Введите уникальный код с сертификата. Результат проверяется по официальному реестру StudyFlow AI.",certificateCodeLabel:"Код сертификата",verifySubmit:"Проверить",validTitle:"Сертификат действителен",validRecipient:"Получатель",validCourse:"Курс",validDate:"Дата выдачи",achievementLevel:"Уровень сертификата",certificateScore:"Результат экзамена",grade_bronze:"Базовый",grade_silver:"Средний",grade_gold:"Продвинутый",invalid:"Сертификат с таким кодом не найден.",error:"Не удалось выполнить проверку. Попробуйте ещё раз." },
  ko: { languageLabel:"언어 선택",verifyEyebrow:"공식 인증",verifyTitle:"수료증 진위 확인",verifyBody:"수료증에 표시된 고유 코드를 입력하세요. 결과는 StudyFlow AI 공식 등록 정보에서 확인됩니다.",certificateCodeLabel:"수료증 코드",verifySubmit:"확인",validTitle:"유효한 수료증입니다",validRecipient:"수료자",validCourse:"강의",validDate:"발급일",achievementLevel:"수료증 등급",certificateScore:"시험 점수",grade_bronze:"기초",grade_silver:"중급",grade_gold:"고급",invalid:"해당 코드의 수료증을 찾을 수 없습니다.",error:"확인 중 오류가 발생했어요. 다시 시도해 주세요." }
};
const languageSelect = document.querySelector("#language");
const codeInput = document.querySelector("#certificateCode");
const resultBox = document.querySelector("#verificationResult");
let language = localStorage.getItem("studyflow-language") || "uz";
let verificationStatus = null;
let verifiedCertificate = null;
const labels = () => verifyCopy[language] || verifyCopy.uz;
function applyLanguage(code) {
  language = verifyCopy[code] ? code : "uz";
  localStorage.setItem("studyflow-language", language);
  document.documentElement.lang = language;
  languageSelect.value = language;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (labels()[key]) element.textContent = labels()[key];
  });
  if (verificationStatus === "valid" && verifiedCertificate) showResult(verifiedCertificate);
  else if (verificationStatus === "invalid") resultBox.textContent = labels().invalid;
  else if (verificationStatus === "error") resultBox.textContent = labels().error;
}
function showResult(certificate) {
  verificationStatus = "valid";
  verifiedCertificate = certificate;
  const copy = labels();
  const date = new Intl.DateTimeFormat(language, {year:"numeric",month:"long",day:"numeric"}).format(new Date(certificate.issued_at));
  resultBox.className = "verification-result is-valid";
  resultBox.innerHTML = `<h2>✓ ${copy.validTitle}</h2><dl><dt>${copy.validRecipient}</dt><dd>${escapeHtml(certificate.recipient_name)}</dd><dt>${copy.validCourse}</dt><dd>${escapeHtml(certificate.course_title)}</dd><dt>${copy.achievementLevel}</dt><dd>${escapeHtml(copy[`grade_${certificate.achievement_level}`] || certificate.achievement_level)}</dd><dt>${copy.certificateScore}</dt><dd>${escapeHtml(certificate.score_percent)}%</dd><dt>${copy.certificateCodeLabel}</dt><dd>${escapeHtml(certificate.certificate_code)}</dd><dt>${copy.validDate}</dt><dd>${escapeHtml(date)}</dd></dl>`;
}
function escapeHtml(value) { return String(value).replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"})[char]); }
async function verify(code) {
  const normalized = code.trim().toUpperCase();
  codeInput.value = normalized;
  resultBox.className = "verification-result";
  resultBox.textContent = "";
  verificationStatus = null;
  verifiedCertificate = null;
  if (!normalized) return;
  try {
    const response = await fetch(`/certificates/verify/${encodeURIComponent(normalized)}`);
    if (response.status === 404) {
      resultBox.className = "verification-result is-invalid";
      verificationStatus = "invalid";
      resultBox.textContent = labels().invalid;
      return;
    }
    if (!response.ok) throw new Error("Verification request failed");
    showResult(await response.json());
  } catch {
    resultBox.className = "verification-result is-invalid";
    verificationStatus = "error";
    resultBox.textContent = labels().error;
  }
}
languageSelect.addEventListener("change", () => applyLanguage(languageSelect.value));
document.querySelector("#verifyForm").addEventListener("submit", (event) => { event.preventDefault(); verify(codeInput.value); });
applyLanguage(language);
const initialCode = new URLSearchParams(location.search).get("code");
if (initialCode) verify(initialCode);
