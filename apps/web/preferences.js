(() => {
  const languageKey = "studyflow-language";
  const supported = new Set(["uz", "en", "ru", "ko"]);

  function storage(kind) {
    return {
      getItem(key) {
        try {
          return window[kind].getItem(key);
        } catch {
          return null;
        }
      },
      setItem(key, value) {
        try {
          window[kind].setItem(key, value);
          return true;
        } catch {
          return false;
        }
      },
      removeItem(key) {
        try {
          window[kind].removeItem(key);
        } catch {
          // Storage is unavailable in some embedded and private browser sessions.
        }
      },
    };
  }

  const local = storage("localStorage");
  const session = storage("sessionStorage");
  const validLanguage = (value) => (supported.has(value) ? value : null);
  const selectedLanguage = () =>
    validLanguage(new URLSearchParams(location.search).get("lang")) ||
    validLanguage(local.getItem(languageKey));

  function saveLanguage(value, updateAddress = false) {
    if (!validLanguage(value)) return;
    local.setItem(languageKey, value);
    if (updateAddress) {
      const url = new URL(location.href);
      url.searchParams.set("lang", value);
      history.replaceState(history.state, "", url);
    }
  }

  window.ScholwardPreferences = { local, session, selectedLanguage, validLanguage, saveLanguage };
})();
