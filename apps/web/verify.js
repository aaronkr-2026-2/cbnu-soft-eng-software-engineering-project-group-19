const verifyCopy = {
  uz: {
    languageLabel: "Tilni tanlang",
    verifyEyebrow: "RASMIY TEKSHIRUV",
    verifyTitle: "Sertifikat haqiqiyligini tekshiring",
    verifyBody:
      "Sertifikatdagi noyob kodni kiriting. Natija SCHOLWARD Academy rasmiy reyestridan olinadi.",
    certificateCodeLabel: "Sertifikat kodi",
    verifySubmit: "Tekshirish",
    validTitle: "Sertifikat haqiqiy",
    validRecipient: "Ism-familiya",
    validCourse: "Kurs",
    validDate: "Berilgan sana",
    achievementLevel: "Sertifikat darajasi",
    certificateScore: "Imtihon bali",
    grade_bronze: "Boshlang‘ich",
    grade_silver: "O‘rta",
    grade_gold: "Yuqori",
    certificateDocumentTitle: "Kursni tamomlaganlik sertifikati",
    awardedTo: "Ushbu sertifikat taqdim etiladi",
    certificateTitle: "Kursni muvaffaqiyatli tamomladi",
    closeCertificate: "Yopish",
    downloadCertificatePdf: "PDF’ni yuklab olish",
    openCertificatePdf: "PDF’ni ochish",
    downloadCertificateAgain: "Sertifikatni qayta yuklab olish",
    invalid: "Bu kod bo‘yicha sertifikat topilmadi.",
    error: "Tekshiruv vaqtida xatolik yuz berdi. Qayta urinib ko‘ring.",
  },
  en: {
    languageLabel: "Choose language",
    verifyEyebrow: "OFFICIAL VERIFICATION",
    verifyTitle: "Verify a certificate",
    verifyBody:
      "Enter the unique code printed on the certificate. Results come from the official SCHOLWARD Academy registry.",
    certificateCodeLabel: "Certificate code",
    verifySubmit: "Verify",
    validTitle: "Certificate is valid",
    validRecipient: "Recipient",
    validCourse: "Course",
    validDate: "Issue date",
    achievementLevel: "Certificate level",
    certificateScore: "Exam score",
    grade_bronze: "Foundation",
    grade_silver: "Intermediate",
    grade_gold: "Advanced",
    certificateDocumentTitle: "Certificate of Completion",
    awardedTo: "This certificate is presented to",
    certificateTitle: "has successfully completed the course",
    closeCertificate: "Close",
    downloadCertificatePdf: "Download PDF",
    openCertificatePdf: "Open PDF",
    downloadCertificateAgain: "Download certificate again",
    invalid: "No certificate was found for this code.",
    error: "Verification failed. Please try again.",
  },
  ru: {
    languageLabel: "Выберите язык",
    verifyEyebrow: "ОФИЦИАЛЬНАЯ ПРОВЕРКА",
    verifyTitle: "Проверить подлинность сертификата",
    verifyBody:
      "Введите уникальный код с сертификата. Результат проверяется по официальному реестру SCHOLWARD Academy.",
    certificateCodeLabel: "Код сертификата",
    verifySubmit: "Проверить",
    validTitle: "Сертификат действителен",
    validRecipient: "Получатель",
    validCourse: "Курс",
    validDate: "Дата выдачи",
    achievementLevel: "Уровень сертификата",
    certificateScore: "Результат экзамена",
    grade_bronze: "Базовый",
    grade_silver: "Средний",
    grade_gold: "Продвинутый",
    certificateDocumentTitle: "Сертификат об окончании курса",
    awardedTo: "Настоящий сертификат выдан",
    certificateTitle: "успешно завершил(а) курс",
    closeCertificate: "Закрыть",
    downloadCertificatePdf: "Скачать PDF",
    openCertificatePdf: "Открыть PDF",
    downloadCertificateAgain: "Скачать сертификат повторно",
    invalid: "Сертификат с таким кодом не найден.",
    error: "Не удалось выполнить проверку. Попробуйте ещё раз.",
  },
  ko: {
    languageLabel: "언어 선택",
    verifyEyebrow: "공식 인증",
    verifyTitle: "수료증 진위 확인",
    verifyBody:
      "수료증에 표시된 고유 코드를 입력하세요. 결과는 SCHOLWARD Academy 공식 등록 정보에서 확인됩니다.",
    certificateCodeLabel: "수료증 코드",
    verifySubmit: "확인",
    validTitle: "유효한 수료증입니다",
    validRecipient: "수료자",
    validCourse: "강의",
    validDate: "발급일",
    achievementLevel: "수료증 등급",
    certificateScore: "시험 점수",
    grade_bronze: "기초",
    grade_silver: "중급",
    grade_gold: "고급",
    certificateDocumentTitle: "과정 수료증",
    awardedTo: "이 수료증을 드립니다",
    certificateTitle: "강의를 성공적으로 수료했습니다",
    closeCertificate: "닫기",
    downloadCertificatePdf: "PDF 다운로드",
    openCertificatePdf: "PDF 열기",
    downloadCertificateAgain: "수료증 다시 다운로드",
    invalid: "해당 코드의 수료증을 찾을 수 없습니다.",
    error: "확인 중 오류가 발생했어요. 다시 시도해 주세요.",
  },
};
const languageSelect = document.querySelector("#language");
const codeInput = document.querySelector("#certificateCode");
const resultBox = document.querySelector("#verificationResult");
const query = new URLSearchParams(location.search);
let language = window.ScholwardPreferences.selectedLanguage() || "uz";
let requestedCode = "";
let verificationRequest = 0;
let verificationStatus = null;
let verifiedCertificate = null;
const labels = () => verifyCopy[language] || verifyCopy.uz;
function applyLanguage(code) {
  language = Object.hasOwn(verifyCopy, code) ? code : "uz";
  window.ScholwardPreferences.saveLanguage(language, true);
  document.documentElement.lang = language;
  document.title = `SCHOLWARD Academy — ${labels().verifyTitle}`;
  languageSelect.value = language;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (labels()[key]) element.textContent = labels()[key];
  });
  if (requestedCode && verificationStatus !== "invalid") verify(requestedCode);
  else if (verificationStatus === "invalid") resultBox.textContent = labels().invalid;
}
function openVerifiedCertificate() {
  if (!verifiedCertificate) return;
  const copy = labels();
  const documentCopy = {
    ...copy,
    issuedOn: copy.validDate,
    certificateCode: copy.certificateCodeLabel,
    navVerifyCertificate: copy.verifyTitle,
  };
  window.ScholwardCertificate.show(verifiedCertificate, language, (key) => documentCopy[key] ?? "");
}

function showResult(certificate) {
  verificationStatus = "valid";
  verifiedCertificate = certificate;
  const copy = labels();
  const date = new Intl.DateTimeFormat(language, {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(certificate.issued_at));
  resultBox.className = "verification-result is-valid";
  const pdfUrl = window.ScholwardCertificate.downloadUrl(certificate.certificate_code, language);
  const viewUrl = window.ScholwardCertificate.downloadUrl(
    certificate.certificate_code,
    language,
    true,
  );
  resultBox.innerHTML = `<h2>✓ ${copy.validTitle}</h2><dl><dt>${copy.validRecipient}</dt><dd>${escapeHtml(certificate.recipient_name)}</dd><dt>${copy.validCourse}</dt><dd>${escapeHtml(certificate.course_title)}</dd><dt>${copy.achievementLevel}</dt><dd>${escapeHtml(copy[`grade_${certificate.achievement_level}`] || certificate.achievement_level)}</dd><dt>${copy.certificateScore}</dt><dd>${escapeHtml(certificate.score_percent)}%</dd><dt>${copy.certificateCodeLabel}</dt><dd>${escapeHtml(certificate.certificate_code)}</dd><dt>${copy.validDate}</dt><dd>${escapeHtml(date)}</dd></dl><div class="verification-actions"><a class="button button-dark verification-download" download href="${escapeHtml(pdfUrl)}">${escapeHtml(copy.downloadCertificateAgain)}</a><a class="button button-outline" href="${escapeHtml(viewUrl)}">${escapeHtml(copy.openCertificatePdf)}</a></div>`;
}
function escapeHtml(value) {
  return String(value).replace(
    /[&<>"']/g,
    (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char],
  );
}
async function verify(code, openCertificate = false) {
  const normalized = code.trim().toUpperCase();
  const request = ++verificationRequest;
  requestedCode = normalized;
  codeInput.value = normalized;
  resultBox.className = "verification-result";
  resultBox.textContent = "";
  verificationStatus = null;
  verifiedCertificate = null;
  if (!normalized) return;
  try {
    const response = await fetch(
      `/certificates/verify/${encodeURIComponent(normalized)}?lang=${language}`,
    );
    if (request !== verificationRequest) return;
    if (response.status === 404) {
      resultBox.className = "verification-result is-invalid";
      verificationStatus = "invalid";
      resultBox.textContent = labels().invalid;
      return;
    }
    if (!response.ok) throw new Error("Verification request failed");
    const certificate = await response.json();
    if (request !== verificationRequest) return;
    showResult(certificate);
    if (openCertificate) openVerifiedCertificate();
  } catch {
    if (request !== verificationRequest) return;
    resultBox.className = "verification-result is-invalid";
    verificationStatus = "error";
    resultBox.textContent = labels().error;
  }
}
languageSelect.addEventListener("change", () => applyLanguage(languageSelect.value));
document.querySelector("#verifyForm").addEventListener("submit", (event) => {
  event.preventDefault();
  verify(codeInput.value);
});
applyLanguage(language);
const initialCode = query.get("code");
if (initialCode) verify(initialCode, query.get("view") === "certificate");
