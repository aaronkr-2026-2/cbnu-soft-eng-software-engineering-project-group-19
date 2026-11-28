const resetCopy = {
  uz: {
    language: "Til",
    title: "Parolni tiklash",
    description: "Hisobingizga bog‘langan email manzilini kiriting.",
    confirmDescription: "Hisobingiz uchun yangi parol kiriting.",
    invalidLink: "Havola yaroqsiz yoki muddati tugagan. Yangi havola so‘rang.",
    email: "Email",
    request: "Tiklash havolasini yuborish",
    sent: "Agar bu email SCHOLWARD Academy hisobiga tegishli bo‘lsa, tiklash havolasi yuborildi.",
    password: "Yangi parol",
    confirm: "Yangi parolni takrorlang",
    show: "Ko‘rsatish",
    hide: "Yashirish",
    save: "Parolni saqlash",
    success: "Parol yangilandi. Endi yangi parol bilan kiring.",
    mismatch: "Parollar bir xil emas.",
    back: "Kirish sahifasiga qaytish",
    unavailable:
      "Parolni tiklash email xizmati serverda sozlanmagan. Administrator SMTP sozlamalarini qo‘shishi kerak.",
    error: "So‘rov bajarilmadi. Keyinroq qayta urinib ko‘ring.",
  },
  en: {
    language: "Language",
    title: "Reset your password",
    description: "Enter the email address linked to your account.",
    confirmDescription: "Choose a new password for your account.",
    invalidLink: "This link is invalid or expired. Request a new link.",
    email: "Email",
    request: "Send reset link",
    sent: "If this email belongs to a SCHOLWARD Academy account, a reset link has been sent.",
    password: "New password",
    confirm: "Confirm new password",
    show: "Show",
    hide: "Hide",
    save: "Save password",
    success: "Password updated. Sign in with your new password.",
    mismatch: "The passwords do not match.",
    back: "Back to sign in",
    unavailable:
      "Password reset email is not configured on this server. An administrator must add SMTP settings.",
    error: "The request failed. Please try again later.",
  },
  ru: {
    language: "Язык",
    title: "Сброс пароля",
    description: "Введите email, связанный с аккаунтом.",
    confirmDescription: "Введите новый пароль для аккаунта.",
    invalidLink: "Ссылка недействительна или просрочена. Запросите новую.",
    email: "Эл. почта",
    request: "Отправить ссылку",
    sent: "Если этот адрес связан с аккаунтом SCHOLWARD Academy, ссылка для сброса отправлена.",
    password: "Новый пароль",
    confirm: "Повторите новый пароль",
    show: "Показать",
    hide: "Скрыть",
    save: "Сохранить пароль",
    success: "Пароль обновлён. Войдите с новым паролем.",
    mismatch: "Пароли не совпадают.",
    back: "Вернуться ко входу",
    unavailable:
      "Отправка писем для сброса пароля не настроена. Администратору нужно указать SMTP.",
    error: "Не удалось выполнить запрос. Попробуйте позже.",
  },
  ko: {
    language: "언어",
    title: "비밀번호 재설정",
    description: "계정에 연결된 이메일을 입력하세요.",
    confirmDescription: "계정의 새 비밀번호를 입력하세요.",
    invalidLink: "링크가 유효하지 않거나 만료됐어요. 새 링크를 요청해 주세요.",
    email: "이메일",
    request: "재설정 링크 보내기",
    sent: "SCHOLWARD Academy 계정에 등록된 이메일이면 재설정 링크를 보냈습니다.",
    password: "새 비밀번호",
    confirm: "새 비밀번호 확인",
    show: "표시",
    hide: "숨기기",
    save: "비밀번호 저장",
    success: "비밀번호가 변경됐어요. 새 비밀번호로 로그인하세요.",
    mismatch: "비밀번호가 일치하지 않아요.",
    back: "로그인으로 돌아가기",
    unavailable:
      "비밀번호 재설정 이메일이 서버에 설정되지 않았어요. 관리자가 SMTP 설정을 추가해야 해요.",
    error: "요청에 실패했어요. 나중에 다시 시도해 주세요.",
  },
};
const languageSelect = document.querySelector("#portalLanguage");
const requestForm = document.querySelector("#resetRequestForm");
const confirmForm = document.querySelector("#resetConfirmForm");
const message = document.querySelector("#resetMessage");
const query = new URLSearchParams(location.search);
let token = query.get("token");
let accountType = query.get("account_type") === "author" ? "author" : "learner";
const passwordToggles = Array.from(
  confirmForm.querySelectorAll(".reset-password-toggle"),
  (button) => {
    const input = document.getElementById(button.getAttribute("aria-controls"));
    return { button, input, label: input.labels[0] };
  },
);
let language = window.ScholwardPreferences.selectedLanguage() || "uz";
let passwordUpdated = false;
let notice;

function showNotice(key, success = false) {
  notice = { key, success };
  renderNotice();
}
function renderNotice() {
  message.textContent = notice ? resetCopy[language][notice.key] : "";
  message.classList.toggle("success", Boolean(notice?.success));
}
function clearResetToken() {
  token = null;
  const destination = new URL(location.href);
  destination.searchParams.delete("token");
  destination.searchParams.set("account_type", accountType);
  history.replaceState(history.state, "", destination);
}

function renderPasswordToggle({ button, input, label }) {
  const c = resetCopy[language] || resetCopy.uz;
  const action = input.type === "password" ? c.show : c.hide;
  button.textContent = action;
  button.setAttribute("aria-label", `${action} (${label.textContent})`);
}

for (const field of passwordToggles) {
  field.button.addEventListener("click", () => {
    field.input.type = field.input.type === "password" ? "text" : "password";
    renderPasswordToggle(field);
  });
}

function render() {
  const c = resetCopy[language] || resetCopy.uz;
  document.documentElement.lang = language;
  document.title = `${c.title} — SCHOLWARD Academy`;
  languageSelect.value = language;
  for (const [id, key] of [
    ["languageLabel", "language"],
    ["title", "title"],
    ["description", passwordUpdated ? null : token ? "confirmDescription" : "description"],
    ["emailLabel", "email"],
    ["requestButton", "request"],
    ["passwordLabel", "password"],
    ["confirmLabel", "confirm"],
    ["confirmButton", "save"],
    ["backLink", "back"],
  ])
    document.getElementById(id).textContent = key ? c[key] : "";
  document.getElementById("backLink").href =
    accountType === "author" ? "/app/author-login.html" : "/app/learner-login.html";
  requestForm.hidden = Boolean(token) || passwordUpdated;
  confirmForm.hidden = !token || passwordUpdated;
  passwordToggles.forEach(renderPasswordToggle);
  renderNotice();
}
languageSelect.addEventListener("change", () => {
  language = languageSelect.value;
  window.ScholwardPreferences.saveLanguage(language, true);
  render();
});
async function post(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok)
    throw Object.assign(new Error(), { status: response.status, detail: result.detail });
  return result;
}
requestForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = document.querySelector("#requestButton");
  if (button.disabled) return;
  button.disabled = true;
  notice = undefined;
  renderNotice();
  try {
    await post("/auth/password-reset/request", { email: requestForm.elements.email.value });
    showNotice("sent", true);
  } catch (error) {
    showNotice(
      error.status === 503 && /not configured/i.test(error.detail) ? "unavailable" : "error",
    );
  } finally {
    button.disabled = false;
  }
});
confirmForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = document.querySelector("#confirmButton");
  if (button.disabled) return;
  button.disabled = true;
  notice = undefined;
  renderNotice();
  const password = confirmForm.elements.new_password.value;
  if (password !== confirmForm.elements.confirm_password.value) {
    showNotice("mismatch");
    button.disabled = false;
    return;
  }
  try {
    const result = await post("/auth/password-reset/confirm", { token, new_password: password });
    if (result.account_type === "author" || result.account_type === "learner") {
      accountType = result.account_type;
    }
    passwordUpdated = true;
    clearResetToken();
    confirmForm.reset();
    for (const { input } of passwordToggles) input.type = "password";
    showNotice("success", true);
    render();
  } catch (error) {
    if (error.status === 400) {
      clearResetToken();
      showNotice("invalidLink");
      render();
    } else showNotice("error");
  } finally {
    button.disabled = false;
  }
});
render();
