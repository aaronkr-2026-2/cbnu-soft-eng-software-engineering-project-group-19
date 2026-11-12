const portalCopy = {
  uz: { language:"Til", learnerEyebrow:"O‘QUVCHI HISOBI", learnerTitle:"O‘qishni davom ettiring", learnerDescription:"Kurslarga yoziling, darslarni tugating va rivojlanishingizni kuzating.", authorEyebrow:"MUALLIF HISOBI", authorTitle:"Bilimingizni kursga aylantiring", authorDescription:"Kurs yarating, dars va quizlarni boshqaring hamda o‘quvchilar rivojini kuzating.", login:"Kirish", register:"Ro‘yxatdan o‘tish", fullName:"Ism-familiya", email:"Email", password:"Parol", loginSubmit:"Kirish", registerSubmit:"Hisob yaratish", otherRolePrompt:"Boshqa portal kerakmi?", authorPortal:"Mualliflar kirishi", learnerPortal:"O‘quvchilar kirishi", backHome:"Bosh sahifaga qaytish", mismatch:"Bu hisob boshqa turdagi kirish sahifasiga tegishli.", genericError:"Xatolik yuz berdi. Ma’lumotlarni tekshirib qayta urinib ko‘ring.", passkeyLater:"Hisob yaratildi. Passkey’ni Profilim bo‘limida sozlashingiz mumkin." },
  en: { language:"Language", learnerEyebrow:"LEARNER ACCOUNT", learnerTitle:"Continue learning", learnerDescription:"Enroll in courses, complete lessons, and track your progress.", authorEyebrow:"AUTHOR ACCOUNT", authorTitle:"Turn your knowledge into a course", authorDescription:"Create courses, manage lessons and quizzes, and track learner progress.", login:"Sign in", register:"Create account", fullName:"Full name", email:"Email", password:"Password", loginSubmit:"Sign in", registerSubmit:"Create account", otherRolePrompt:"Need the other portal?", authorPortal:"Author sign in", learnerPortal:"Learner sign in", backHome:"Back to home", mismatch:"This account belongs to the other sign-in portal.", genericError:"Something went wrong. Check your details and try again.", passkeyLater:"Account created. You can set up a passkey from your profile." },
  ru: { language:"Язык", learnerEyebrow:"АККАУНТ УЧЕНИКА", learnerTitle:"Продолжайте учиться", learnerDescription:"Записывайтесь на курсы, проходите уроки и следите за прогрессом.", authorEyebrow:"АККАУНТ АВТОРА", authorTitle:"Превратите знания в курс", authorDescription:"Создавайте курсы, управляйте уроками и тестами и следите за прогрессом учеников.", login:"Войти", register:"Создать аккаунт", fullName:"Имя и фамилия", email:"Эл. почта", password:"Пароль", loginSubmit:"Войти", registerSubmit:"Создать аккаунт", otherRolePrompt:"Нужен другой раздел?", authorPortal:"Вход для авторов", learnerPortal:"Вход для учеников", backHome:"На главную", mismatch:"Этот аккаунт относится к другому разделу входа.", genericError:"Произошла ошибка. Проверьте данные и попробуйте снова.", passkeyLater:"Аккаунт создан. Настроить ключ доступа можно в профиле." },
  ko: { language:"언어", learnerEyebrow:"학습자 계정", learnerTitle:"학습을 계속하세요", learnerDescription:"강의에 등록하고 수업을 완료하며 학습 진행 상황을 확인하세요.", authorEyebrow:"강사 계정", authorTitle:"지식을 강의로 만들어 보세요", authorDescription:"강의와 수업, 퀴즈를 관리하고 학습자의 성장을 확인하세요.", login:"로그인", register:"회원가입", fullName:"이름", email:"이메일", password:"비밀번호", loginSubmit:"로그인", registerSubmit:"계정 만들기", otherRolePrompt:"다른 페이지가 필요하신가요?", authorPortal:"강사 로그인", learnerPortal:"학습자 로그인", backHome:"홈으로 돌아가기", mismatch:"이 계정은 다른 로그인 페이지에 등록되어 있어요.", genericError:"오류가 발생했어요. 정보를 확인하고 다시 시도해 주세요.", passkeyLater:"계정이 만들어졌어요. 프로필에서 패스키를 설정할 수 있어요." }
};

const forgotPasswordCopy = {
  uz:"Parolni unutdingizmi?",
  en:"Forgot your password?",
  ru:"Забыли пароль?",
  ko:"비밀번호를 잊으셨나요?"
};

const role = document.body.dataset.accountType;
const form = document.querySelector("#portalForm");
const message = document.querySelector("#portalMessage");
const nameField = document.querySelector("#fullNameField");
const languagePicker = document.querySelector("#portalLanguage");
let mode = "login";
let language = localStorage.getItem("studyflow-language") || "uz";

function translate(key) { return portalCopy[language]?.[key] || portalCopy.uz[key] || key; }
function renderText() {
  document.documentElement.lang = language;
  languagePicker.value = language;
  document.querySelectorAll("[data-copy]").forEach((element) => { element.textContent = translate(element.dataset.copy); });
  document.querySelector("#loginTab").classList.toggle("active", mode === "login");
  document.querySelector("#registerTab").classList.toggle("active", mode === "register");
  nameField.hidden = mode === "login";
  nameField.querySelector("input").required = mode === "register";
  form.elements.password.autocomplete = mode === "login" ? "current-password" : "new-password";
  document.querySelector("#portalSubmit").textContent = translate(mode === "login" ? "loginSubmit" : "registerSubmit");
  const forgotLink = document.querySelector("#forgotPasswordLink");
  forgotLink.hidden = mode !== "login";
  forgotLink.textContent = forgotPasswordCopy[language] || forgotPasswordCopy.uz;
  forgotLink.href = `/app/reset-password.html?account_type=${encodeURIComponent(role)}`;
  message.textContent = "";
}

async function request(path, body) {
  const response = await fetch(path, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(response.status === 403 ? translate("mismatch") : result.detail || translate("genericError"));
    error.status = response.status;
    throw error;
  }
  return result;
}

function decodeBase64Url(value) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  return Uint8Array.from(atob(normalized + "=".repeat((4 - normalized.length % 4) % 4)), (char) => char.charCodeAt(0));
}
function encodeBase64Url(value) {
  return btoa(String.fromCharCode(...new Uint8Array(value))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}
async function setupPasskey(token) {
  if (!window.PublicKeyCredential || !navigator.credentials) return;
  const start = await fetch("/auth/passkeys/registration/options", {
    method:"POST", headers:{"Content-Type":"application/json", Authorization:`Bearer ${token}`}, body:"{}"
  }).then(async (response) => {
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Passkey setup failed");
    return data;
  });
  const publicKey = JSON.parse(start.publicKey);
  publicKey.challenge = decodeBase64Url(publicKey.challenge);
  publicKey.user.id = decodeBase64Url(publicKey.user.id);
  publicKey.excludeCredentials = (publicKey.excludeCredentials || []).map((item) => ({...item, id:decodeBase64Url(item.id)}));
  const credential = await navigator.credentials.create({publicKey});
  if (!credential) throw new Error("Passkey setup was cancelled");
  const response = credential.response;
  const payload = {
    challenge_id:start.challenge_id,
    label:navigator.userAgent.includes("iPhone") || navigator.userAgent.includes("Mac") ? "This Apple device" : "This device",
    credential:{
      id:credential.id,
      rawId:encodeBase64Url(credential.rawId),
      type:credential.type,
      authenticatorAttachment:credential.authenticatorAttachment,
      response:{clientDataJSON:encodeBase64Url(response.clientDataJSON),attestationObject:encodeBase64Url(response.attestationObject),transports:response.getTransports?.() || []},
      clientExtensionResults:credential.getClientExtensionResults()
    }
  };
  const verified = await fetch("/auth/passkeys/registration/verify", {
    method:"POST", headers:{"Content-Type":"application/json", Authorization:`Bearer ${token}`}, body:JSON.stringify(payload)
  });
  if (!verified.ok) throw new Error("Passkey verification failed");
}

document.querySelector("#loginTab").addEventListener("click", () => { mode = "login"; renderText(); });
document.querySelector("#registerTab").addEventListener("click", () => { mode = "register"; renderText(); });
languagePicker.addEventListener("change", () => { language = languagePicker.value; localStorage.setItem("studyflow-language", language); renderText(); });

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(form));
  const submit = document.querySelector("#portalSubmit");
  submit.disabled = true;
  message.className = "form-message";
  try {
    if (mode === "register") {
      await request("/auth/register", { email:values.email, full_name:values.full_name, password:values.password, preferred_language:language, account_type:role });
    }
    const token = await request("/auth/login", { email:values.email, password:values.password, account_type:role });
    localStorage.setItem("studyflow-token", token.access_token);
    if (mode === "register") {
      try { await setupPasskey(token.access_token); } catch { /* Continue to the profile so passkey setup can be retried there. */ }
    }
    window.location.replace("/app/");
  } catch (error) {
    message.textContent = error.message || translate("genericError");
    message.className = "form-message";
  } finally {
    submit.disabled = false;
  }
});

renderText();
