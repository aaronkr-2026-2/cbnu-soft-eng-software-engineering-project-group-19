(() => {
  function escapeHtml(value) {
    const node = document.createElement("span");
    node.textContent = String(value);
    return node.innerHTML.replaceAll('"', "&quot;").replaceAll("'", "&#39;");
  }

  function certificateDialog() {
    let dialog = document.getElementById("certificateDialog");
    if (dialog) return dialog;
    dialog = document.createElement("dialog");
    dialog.id = "certificateDialog";
    dialog.className = "certificate-dialog";
    dialog.setAttribute("aria-labelledby", "certificateDocumentTitle");
    dialog.innerHTML = `
      <div id="certificateBody" class="certificate-paper"></div>
      <div class="certificate-actions">
        <button type="button" id="certificateClose" class="button button-outline"></button>
        <a id="certificateOpenPdf" class="button button-outline"></a>
        <a id="certificateDownload" class="button button-dark" download></a>
      </div>`;
    dialog.querySelector("#certificateClose").addEventListener("click", () => dialog.close());
    document.body.append(dialog);
    return dialog;
  }

  function downloadUrl(code, language, inline = false) {
    const search = new URLSearchParams({ lang: language });
    if (inline) search.set("inline", "true");
    return `/certificates/verify/${encodeURIComponent(code)}/pdf?${search}`;
  }

  const uzMonths = [
    "yanvar",
    "fevral",
    "mart",
    "aprel",
    "may",
    "iyun",
    "iyul",
    "avgust",
    "sentabr",
    "oktabr",
    "noyabr",
    "dekabr",
  ];

  function showCertificate(certificate, language, t) {
    const issueDate = new Date(certificate.issued_at);
    const issuedDate =
      language === "uz"
        ? `${issueDate.getUTCDate()}-${uzMonths[issueDate.getUTCMonth()]}, ${issueDate.getUTCFullYear()}`
        : new Intl.DateTimeFormat(language, {
            year: "numeric",
            month: "long",
            day: "numeric",
            timeZone: "UTC",
          }).format(issueDate);
    const verifyUrl = new URL("https://scholward-academy.vercel.app/app/verify.html");
    verifyUrl.searchParams.set("code", certificate.certificate_code);
    verifyUrl.searchParams.set("lang", language);
    const grade = certificate.achievement_level || "bronze";
    const score = certificate.score_percent == null ? "—" : `${certificate.score_percent}%`;
    const dialog = certificateDialog();
    const paper = dialog.querySelector("#certificateBody");
    paper.lang = language;
    paper.innerHTML = `
    <div class="certificate-frame">
      <header class="certificate-header">
        <div class="certificate-logo">
          <img src="/app/scholward-crest.svg" width="48" height="48" alt="">
          <span class="certificate-wordmark">SCHOLWARD <span>Academy</span></span>
        </div>
        <div class="certificate-level">
          <span>${escapeHtml(t("achievementLevel"))}</span>
          <strong>${escapeHtml(t(`grade_${grade}`))}</strong>
        </div>
        <a class="certificate-verify-link" href="${escapeHtml(verifyUrl.href)}" target="_blank" rel="noopener">
          ${escapeHtml(t("navVerifyCertificate"))}
        </a>
      </header>
      <div class="certificate-content">
        <h2 id="certificateDocumentTitle">${escapeHtml(t("certificateDocumentTitle"))}</h2>
        <p class="certificate-awarded">${escapeHtml(t("awardedTo"))}</p>
        <p class="certificate-recipient">${escapeHtml(certificate.recipient_name)}</p>
        <p class="certificate-statement">${escapeHtml(t("certificateTitle"))}</p>
        <p class="certificate-course">${escapeHtml(certificate.course_title)}</p>
        <p class="certificate-score">${escapeHtml(t("certificateScore"))} <strong>${escapeHtml(score)}</strong></p>
      </div>
      <footer class="certificate-footer">
        <dl>
          <div>
            <dt>${escapeHtml(t("issuedOn"))}</dt>
            <dd>${escapeHtml(issuedDate)}</dd>
          </div>
          <div>
            <dt>${escapeHtml(t("certificateCode"))}</dt>
            <dd class="certificate-code">${escapeHtml(certificate.certificate_code)}</dd>
          </div>
        </dl>
      </footer>
    </div>`;
    dialog.querySelector("#certificateClose").textContent = t("closeCertificate");
    const download = dialog.querySelector("#certificateDownload");
    download.textContent = t("downloadCertificatePdf");
    download.href = downloadUrl(certificate.certificate_code, language);
    const openPdf = dialog.querySelector("#certificateOpenPdf");
    openPdf.textContent = t("openCertificatePdf");
    openPdf.href = downloadUrl(certificate.certificate_code, language, true);
    if (!dialog.open) dialog.showModal();
  }

  window.ScholwardCertificate = { show: showCertificate, downloadUrl };
})();
