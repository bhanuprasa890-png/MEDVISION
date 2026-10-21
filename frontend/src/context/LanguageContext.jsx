import React, { createContext, useContext, useState, useCallback, useMemo } from "react";
import {
  SUPPORTED_LANGUAGES,
  DEFAULT_LANGUAGE,
  getTranslation,
} from "../i18n/translations";

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(DEFAULT_LANGUAGE);

  const setLanguage = useCallback((langCode) => {
    if (SUPPORTED_LANGUAGES[langCode]) {
      setLanguageState(langCode);
    } else {
      console.warn(`[i18n] Language '${langCode}' is not supported. Defaulting to '${DEFAULT_LANGUAGE}'.`);
      setLanguageState(DEFAULT_LANGUAGE);
    }
  }, []);

  const t = useCallback(
    (section, key) => {
      return getTranslation(section, key, language);
    },
    [language]
  );

  const currentLanguageInfo = useMemo(() => {
    return SUPPORTED_LANGUAGES[language] || SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE];
  }, [language]);

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      t,
      supportedLanguages: SUPPORTED_LANGUAGES,
      currentLanguageInfo,
    }),
    [language, setLanguage, t, currentLanguageInfo]
  );

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    // Provide a safe fallback if accessed outside Provider (e.g. in standalone tests)
    return {
      language: DEFAULT_LANGUAGE,
      setLanguage: () => {},
      t: (section, key) => getTranslation(section, key, DEFAULT_LANGUAGE),
      supportedLanguages: SUPPORTED_LANGUAGES,
      currentLanguageInfo: SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE],
    };
  }
  return context;
}
