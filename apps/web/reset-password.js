const resetCopy = {
  uz:{language:"Til",title:"Parolni tiklash",description:"Hisobingizga bog‘langan email manzilini kiriting.",email:"Email",request:"Tiklash havolasini yuborish",sent:"Agar bu email StudyFlow hisobiga tegishli bo‘lsa, tiklash havolasi yuborildi.",password:"Yangi parol",confirm:"Yangi parolni takrorlang",save:"Parolni saqlash",success:"Parol yangilandi. Endi yangi parol bilan kiring.",mismatch:"Parollar bir xil emas.",back:"Kirish sahifasiga qaytish",unavailable:"Parolni tiklash email xizmati serverda sozlanmagan. Administrator SMTP sozlamalarini qo‘shishi kerak.",error:"So‘rov bajarilmadi. Keyinroq qayta urinib ko‘ring."},
  en:{language:"Language",title:"Reset your password",description:"Enter the email address linked to your account.",email:"Email",request:"Send reset link",sent:"If this email belongs to a StudyFlow account, a reset link has been sent.",password:"New password",confirm:"Confirm new password",save:"Save password",success:"Password updated. Sign in with your new password.",mismatch:"The passwords do not match.",back:"Back to sign in",unavailable:"Password reset email is not configured on this server. An administrator must add SMTP settings.",error:"The request failed. Please try again later."},
  ru:{language:"Язык",title:"Сброс пароля",description:"Введите email, связанный с аккаунтом.",email:"Эл. почта",request:"Отправить ссылку",sent:"Если этот адрес связан с аккаунтом StudyFlow, ссылка для сброса отправлена.",password:"Новый пароль",confirm:"Повторите новый пароль",save:"Сохранить пароль",success:"Пароль обновлён. Войдите с новым паролем.",mismatch:"Пароли не совпадают.",back:"Вернуться ко входу",unavailable:"Отправка писем для сброса пароля не настроена. Администратору нужно указать SMTP.",error:"Не удалось выполнить запрос. Попробуйте позже."},
  ko:{language:"언어",title:"비밀번호 재설정",description:"계정에 연결된 이메일을 입력하세요.",email:"이메일",request:"재설정 링크 보내기",sent:"StudyFlow 계정에 등록된 이메일이면 재설정 링크를 보냈습니다.",password:"새 비밀번호",confirm:"새 비밀번호 확인",save:"비밀번호 저장",success:"비밀번호가 변경됐어요. 새 비밀번호로 로그인하세요.",mismatch:"비밀번호가 일치하지 않아요.",back:"로그인으로 돌아가기",unavailable:"비밀번호 재설정 이메일이 서버에 설정되지 않았어요. 관리자가 SMTP 설정을 추가해야 해요.",error:"요청에 실패했어요. 나중에 다시 시도해 주세요."}
};
const languageSelect=document.querySelector("#portalLanguage");
const requestForm=document.querySelector("#resetRequestForm");
const confirmForm=document.querySelector("#resetConfirmForm");
const message=document.querySelector("#resetMessage");
const query=new URLSearchParams(location.search);
const token=query.get("token");
const accountType=query.get("account_type")==="author"?"author":"learner";
let language=localStorage.getItem("studyflow-language")||"uz";
function render(){
  const c=resetCopy[language]||resetCopy.uz;
  document.documentElement.lang=language; languageSelect.value=language;
  for(const [id,key] of [["languageLabel","language"],["title","title"],["description","description"],["emailLabel","email"],["requestButton","request"],["passwordLabel","password"],["confirmLabel","confirm"],["confirmButton","save"],["backLink","back"]]) document.getElementById(id).textContent=c[key];
  document.getElementById("backLink").href=accountType==="author"?"/app/author-login.html":"/app/learner-login.html";
  requestForm.hidden=Boolean(token); confirmForm.hidden=!token;
}
languageSelect.addEventListener("change",()=>{language=languageSelect.value;localStorage.setItem("studyflow-language",language);render();});
async function post(url,body){
  const response=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  const result=await response.json().catch(()=>({}));
  if(!response.ok)throw new Error(result.detail||resetCopy[language].error);
  return result;
}
requestForm.addEventListener("submit",async(event)=>{
  event.preventDefault(); const button=document.querySelector("#requestButton"); button.disabled=true; message.textContent="";
  try{await post("/auth/password-reset/request",{email:requestForm.elements.email.value});message.textContent=resetCopy[language].sent;}
  catch(error){message.textContent=/not configured|unable to send/i.test(error.message)?resetCopy[language].unavailable:(error.message||resetCopy[language].error);}
  finally{button.disabled=false;}
});
confirmForm.addEventListener("submit",async(event)=>{
  event.preventDefault(); const button=document.querySelector("#confirmButton"); button.disabled=true; message.textContent="";
  const password=confirmForm.elements.new_password.value;
  if(password!==confirmForm.elements.confirm_password.value){message.textContent=resetCopy[language].mismatch;button.disabled=false;return;}
  try{await post("/auth/password-reset/confirm",{token,new_password:password});message.textContent=resetCopy[language].success;confirmForm.hidden=true;history.replaceState({},"",location.pathname);}
  catch(error){message.textContent=error.message||resetCopy[language].error;}
  finally{button.disabled=false;}
});
render();
