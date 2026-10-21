import React, { useEffect, useState } from "react";
import { Activity, ShieldAlert, MessageSquare } from "lucide-react";
import { getHealth } from "../services/api";
import { useLanguage } from "../context/LanguageContext";
import { LanguageSelector } from "./LanguageSelector";

export function Header({ activeTab, setActiveTab }) {
  const { t, language } = useLanguage();
  const [backendHealth, setBackendHealth] = useState({
    status: "checking",
    version: null,
  });

  useEffect(() => {
    let isMounted = true;
    async function checkStatus() {
      try {
        const data = await getHealth();
        if (isMounted) {
          if (data && data.status === "healthy") {
            setBackendHealth({ status: "healthy", version: data.version });
          } else {
            setBackendHealth({ status: "offline", version: null });
          }
        }
      } catch (err) {
        if (isMounted) {
          setBackendHealth({ status: "offline", version: null });
        }
      }
    }

    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-2">
          {/* Logo & Identity */}
          <div
            role="button"
            tabIndex={0}
            onClick={() => setActiveTab("home")}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                setActiveTab("home");
              }
            }}
            aria-label="MedVision AI home"
            className="flex items-center space-x-3 cursor-pointer rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 p-1 flex-shrink-0"
          >
            <div className="w-10 h-10 rounded-xl bg-slate-950/80 border border-teal-500/30 flex items-center justify-center p-1 shadow-lg shadow-teal-500/10 overflow-hidden">
              <img
                src="/assets/medvision-logo-symbol.png"
                alt="MedVision AI Logo"
                className="w-full h-full object-contain"
              />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-white tracking-tight">MedVision AI</span>
                <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20">
                  {t("navigation", "researchPrototype")}
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                {t("navigation", "tagline")}
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav
            aria-label="Main navigation"
            className="flex items-center space-x-1 sm:space-x-2 overflow-x-auto max-w-[50vw] sm:max-w-none py-1"
          >
            <button
              onClick={() => setActiveTab("home")}
              aria-current={activeTab === "home" ? "page" : undefined}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap cursor-pointer ${
                activeTab === "home"
                  ? "bg-slate-800 text-teal-400 shadow-sm"
                  : "text-slate-300 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              {language === "en" ? "Overview" : `${t("navigation", "overview")} (Overview)`}
            </button>
            <button
              onClick={() => setActiveTab("retina")}
              aria-current={activeTab === "retina" ? "page" : undefined}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap cursor-pointer ${
                activeTab === "retina"
                  ? "bg-slate-800 text-teal-400 shadow-sm"
                  : "text-slate-300 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              {language === "en" ? "Retina Module" : `${t("navigation", "retinaModule")}`}
            </button>
            <button
              onClick={() => setActiveTab("chest-xray")}
              aria-current={activeTab === "chest-xray" ? "page" : undefined}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap cursor-pointer ${
                activeTab === "chest-xray"
                  ? "bg-slate-800 text-teal-400 shadow-sm"
                  : "text-slate-300 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              {language === "en" ? "Chest X-Ray Module" : `${t("navigation", "chestXrayModule")}`}
            </button>
            <button
              onClick={() => setActiveTab("medassist")}
              aria-current={activeTab === "medassist" ? "page" : undefined}
              className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap cursor-pointer ${
                activeTab === "medassist"
                  ? "bg-slate-800 text-teal-400 shadow-sm"
                  : "text-slate-300 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>{t("navigation", "medassist")}</span>
            </button>
          </nav>

          {/* Right Controls: Global Language Selector & Backend Health */}
          <div className="flex items-center space-x-2 sm:space-x-3 flex-shrink-0">
            {/* Global Language Selector */}
            <LanguageSelector variant="header" />

            {/* Backend Status Indicator */}
            <div className="hidden lg:flex items-center space-x-2 text-xs bg-slate-950 px-3 py-1.5 rounded-full border border-slate-800">
              <span className="text-slate-400">{t("navigation", "backendStatus")}:</span>
              {backendHealth.status === "healthy" ? (
                <span className="flex items-center space-x-1 text-emerald-400 font-medium">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse motion-reduce:animate-none"></span>
                  <span>{t("navigation", "online")} (v{backendHealth.version || "0.1"})</span>
                </span>
              ) : backendHealth.status === "checking" ? (
                <span className="flex items-center space-x-1 text-amber-400">
                  <Activity className="w-3 h-3 animate-spin motion-reduce:animate-none" />
                  <span>{t("navigation", "checking")}</span>
                </span>
              ) : (
                <span className="flex items-center space-x-1 text-rose-400 font-medium">
                  <ShieldAlert className="w-3 h-3" />
                  <span>{t("navigation", "offline")}</span>
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
