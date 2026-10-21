import React, { useState, useRef, useEffect } from "react";
import { Globe, Check, ChevronDown, Info } from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export function LanguageSelector({ variant = "header" }) {
  const { language, setLanguage, supportedLanguages, currentLanguageInfo, t } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Handle keyboard navigation inside dropdown
  const handleKeyDown = (e) => {
    if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  const languagesList = Object.values(supportedLanguages);

  return (
    <div
      ref={dropdownRef}
      onKeyDown={handleKeyDown}
      className="relative inline-block text-left"
    >
      <button
        type="button"
        id="language-selector-button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={`${t("navigation", "selectLanguage")}: ${currentLanguageInfo.label}`}
        className="inline-flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-200 text-xs font-medium border border-slate-700/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 transition-colors cursor-pointer shadow-sm"
      >
        <Globe className="w-3.5 h-3.5 text-teal-400 flex-shrink-0" />
        <span className="font-medium">{currentLanguageInfo.nativeLabel}</span>
        <span className="text-[10px] text-slate-400 hidden sm:inline">
          ({currentLanguageInfo.label})
        </span>
        <ChevronDown
          className={`w-3 h-3 text-slate-400 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <div
          role="listbox"
          aria-labelledby="language-selector-button"
          tabIndex={-1}
          className="absolute right-0 mt-2 w-56 rounded-xl bg-slate-900 border border-slate-700/90 shadow-2xl z-50 py-1.5 focus:outline-none"
        >
          <div className="px-3 py-1.5 border-b border-slate-800 text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
            <span>{t("navigation", "selectLanguage")}</span>
            <span className="text-[9px] text-teal-400 font-mono">i18n</span>
          </div>

          <div className="max-h-60 overflow-y-auto py-1">
            {languagesList.map((lang) => {
              const isSelected = lang.code === language;
              return (
                <button
                  key={lang.code}
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => {
                    setLanguage(lang.code);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between transition-colors cursor-pointer ${
                    isSelected
                      ? "bg-teal-600/20 text-teal-300 font-semibold"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  <div className="flex flex-col">
                    <span className="font-medium text-slate-100">
                      {lang.nativeLabel}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      {lang.label} • {lang.reviewStatus}
                    </span>
                  </div>
                  {isSelected && (
                    <Check className="w-4 h-4 text-teal-400 flex-shrink-0" />
                  )}
                </button>
              );
            })}
          </div>

          <div className="px-3 py-2 border-t border-slate-800/80 bg-slate-950/40 text-[10px] text-slate-400 flex items-start space-x-1.5">
            <Info className="w-3 h-3 text-slate-500 flex-shrink-0 mt-0.5" />
            <span>
              Clinical terms remain visible in original English alongside native explanations.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
