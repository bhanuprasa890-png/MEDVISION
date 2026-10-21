import React, { useState, useEffect } from "react";
import {
  Volume2,
  VolumeX,
  Play,
  Pause,
  Languages,
  AlertTriangle,
  Info,
  HelpCircle,
  ShieldAlert,
  HeartPulse,
  Eye,
  CheckCircle2,
} from "lucide-react";
import {
  GRADE_EXPLANATIONS,
  HEATMAP_EXPLANATIONS,
  EMERGENCY_WARNINGS,
  UI_STRINGS,
} from "../utils/patientExplanations.js";
import {
  speakUtterance,
  stopSpeech,
  pauseSpeech,
  resumeSpeech,
  findMatchingVoice,
  loadVoicesAsync,
  subscribeVoicesChanged,
} from "../utils/speechSynthesis.js";
import { useLanguage } from "../context/LanguageContext";

// Re-export constants for modular consumption
export {
  GRADE_EXPLANATIONS,
  HEATMAP_EXPLANATIONS,
  EMERGENCY_WARNINGS,
  UI_STRINGS,
};

/**
 * Accessible Patient-Friendly Explanation Component.
 * Supports English, Tamil, Hindi, and Telugu with browser text-to-speech (read aloud).
 */
export function PatientFriendlyExplanation({ prediction, explanation }) {
  const { language: globalLang, setLanguage: setGlobalLang } = useLanguage();
  const [language, setLanguage] = useState(globalLang || "en");
  const [speechState, setSpeechState] = useState("idle"); // 'idle' | 'playing' | 'paused' | 'unsupported'
  const [speechMessage, setSpeechMessage] = useState("");

  // Pre-load voices and subscribe to dynamic voice changes
  useEffect(() => {
    const unsubscribe = subscribeVoicesChanged(() => {});
    loadVoicesAsync();
    return () => {
      unsubscribe();
      stopSpeech();
    };
  }, []);

  // Sync with global language changes
  useEffect(() => {
    if (globalLang && globalLang !== language) {
      setLanguage(globalLang);
      stopSpeech();
      setSpeechState("idle");
      setSpeechMessage("");
    }
  }, [globalLang]);

  const handleLanguageChange = (langCode) => {
    setLanguage(langCode);
    if (setGlobalLang) {
      setGlobalLang(langCode);
    }
    stopSpeech();
    setSpeechState("idle");
    setSpeechMessage("");
  };

  const t = UI_STRINGS[language] || UI_STRINGS.en;
  const gradeIdx = prediction?.predicted_class ?? 0;
  const gradeData = GRADE_EXPLANATIONS[gradeIdx] || GRADE_EXPLANATIONS[0];
  const gradeContent = gradeData[language] || gradeData.en;
  const heatmapContent = HEATMAP_EXPLANATIONS[language] || HEATMAP_EXPLANATIONS.en;
  const emergencyContent = EMERGENCY_WARNINGS[language] || EMERGENCY_WARNINGS.en;

  const isLowConfidence =
    prediction?.confidence_score !== undefined &&
    prediction?.confidence_score !== null &&
    prediction.confidence_score < 0.6;

  // Cleanup speech synthesis on unmount or language change
  useEffect(() => {
    return () => {
      stopSpeech();
    };
  }, [language]);

  const handleSpeak = () => {
    // Handle pause/resume toggle
    if (speechState === "playing") {
      pauseSpeech();
      setSpeechState("paused");
      setSpeechMessage(t.audioPaused);
      return;
    }

    if (speechState === "paused") {
      resumeSpeech();
      setSpeechState("playing");
      setSpeechMessage(t.audioPlaying);
      return;
    }

    // Construct text to speak based on active language
    const speakText = `${t.sectionHeading}. ${gradeContent.title}. ${gradeContent.whatModelPredicted} ${gradeContent.everydayExplanation} ${heatmapContent.whatItRepresentsTitle}: ${heatmapContent.whatItRepresentsText} ${emergencyContent.title}: ${emergencyContent.intro} ${emergencyContent.symptoms.join(". ")}`;

    const result = speakUtterance({
      text: speakText,
      langCode: language,
      rate: 0.95,
      onStart: () => {
        setSpeechState("playing");
        setSpeechMessage(t.audioPlaying);
      },
      onEnd: () => {
        setSpeechState("idle");
        setSpeechMessage(t.audioFinished);
      },
      onError: (err) => {
        if (err && (err.error === "canceled" || err.error === "interrupted")) {
          setSpeechState("idle");
          return;
        }
        setSpeechState("idle");
        setSpeechMessage(t.audioUnavailable);
      },
      onVoiceUnavailable: () => {
        setSpeechState("unsupported");
        const msg =
          language === "ta"
            ? (t.tamilVoiceUnavailable || t.voiceUnavailable)
            : t.voiceUnavailable;
        setSpeechMessage(msg);
      },
    });

    if (!result.ok && result.reason === "SPEECH_UNSUPPORTED") {
      setSpeechState("unsupported");
      setSpeechMessage(t.audioUnavailable);
    }
  };

  const handleStopSpeech = () => {
    stopSpeech();
    setSpeechState("idle");
    setSpeechMessage(t.audioFinished);
  };

  if (!prediction) {
    return (
      <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800 text-xs text-slate-400">
        {t.noPrediction}
      </div>
    );
  }

  return (
    <section
      aria-labelledby="understand-result-title"
      className="bg-slate-950 border border-teal-500/30 rounded-2xl p-6 mt-6 shadow-2xl relative overflow-hidden"
    >
      {/* Decorative accent glow */}
      <div className="absolute top-0 right-0 w-72 h-72 bg-teal-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Header with Title and Language / Accessibility Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 text-teal-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <HelpCircle className="w-4 h-4" />
            <span>Patient &amp; Public Guidance</span>
          </div>
          <h3
            id="understand-result-title"
            className="text-lg sm:text-xl font-bold text-white tracking-tight"
          >
            {t.sectionHeading}
          </h3>
          <p className="text-xs text-slate-400 mt-1">{t.sectionSubheading}</p>
        </div>

        {/* Language Selection & Read-Aloud Toolbar */}
        <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
          {/* Language Selector Buttons */}
          <div
            role="group"
            aria-label={t.languageToggleLabel}
            className="inline-flex flex-wrap rounded-lg bg-slate-900 p-1 border border-slate-800 text-xs gap-1"
          >
            <button
              type="button"
              onClick={() => handleLanguageChange("en")}
              aria-pressed={language === "en"}
              className={`px-2.5 py-1.5 rounded-md font-semibold transition-all cursor-pointer ${
                language === "en"
                  ? "bg-teal-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              English
            </button>
            <button
              type="button"
              onClick={() => handleLanguageChange("ta")}
              aria-pressed={language === "ta"}
              className={`px-2.5 py-1.5 rounded-md font-semibold transition-all cursor-pointer ${
                language === "ta"
                  ? "bg-teal-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              தமிழ் (Tamil)
            </button>
            <button
              type="button"
              onClick={() => handleLanguageChange("hi")}
              aria-pressed={language === "hi"}
              className={`px-2.5 py-1.5 rounded-md font-semibold transition-all cursor-pointer ${
                language === "hi"
                  ? "bg-teal-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              हिन्दी (Hindi)
            </button>
            <button
              type="button"
              onClick={() => handleLanguageChange("te")}
              aria-pressed={language === "te"}
              className={`px-2.5 py-1.5 rounded-md font-semibold transition-all cursor-pointer ${
                language === "te"
                  ? "bg-teal-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              తెలుగు (Telugu)
            </button>
          </div>

          {/* Read Aloud Button */}
          <button
            type="button"
            onClick={handleSpeak}
            aria-label={
              speechState === "playing"
                ? t.pauseAudio
                : speechState === "paused"
                ? t.resumeAudio
                : t.readAloud
            }
            className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all cursor-pointer ${
              speechState === "playing"
                ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                : "bg-slate-900 hover:bg-slate-800 text-slate-200 border-slate-700"
            }`}
          >
            {speechState === "playing" ? (
              <>
                <Pause className="w-3.5 h-3.5" />
                <span>{t.pauseAudio}</span>
              </>
            ) : speechState === "paused" ? (
              <>
                <Play className="w-3.5 h-3.5" />
                <span>{t.resumeAudio}</span>
              </>
            ) : (
              <>
                <Volume2 className="w-3.5 h-3.5 text-teal-400" />
                <span>{t.readAloud}</span>
              </>
            )}
          </button>

          {speechState !== "idle" && (
            <button
              type="button"
              onClick={handleStopSpeech}
              aria-label={t.stopAudio}
              className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-700 cursor-pointer"
              title={t.stopAudio}
            >
              <VolumeX className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Accessible Live Region for Audio Feedback */}
      {speechMessage && (
        <div
          role="status"
          aria-live="polite"
          className="mt-3 px-3 py-1.5 rounded-lg bg-teal-500/10 border border-teal-500/20 text-[11px] text-teal-300 flex items-center space-x-2"
        >
          <Info className="w-3.5 h-3.5 flex-shrink-0" />
          <span>{speechMessage}</span>
        </div>
      )}

      {/* Low Confidence Warning (if applicable) */}
      {isLowConfidence && (
        <div className="mt-4 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start space-x-2.5">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <strong className="block text-amber-200 mb-0.5">{t.confidenceTitle}</strong>
            {t.lowConfidenceWarning}
          </div>
        </div>
      )}

      {/* Main Grid: Grade Explanation & Heatmap Guidance */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-5">
        {/* Card 1: What the Grade Means */}
        <div className="bg-slate-900/80 rounded-xl p-5 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between gap-2 mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-teal-500/20 text-teal-300 border border-teal-500/30">
                {gradeContent.badge}
              </span>
              <span className="text-[11px] text-slate-400 font-mono">
                {gradeData.clinicalName}
              </span>
            </div>

            <h4 className="text-base font-bold text-white mb-2 leading-snug">
              {gradeContent.title}
            </h4>

            <p className="text-xs text-slate-300 leading-relaxed mb-3">
              <strong className="text-white block mb-1">
                {language === "ta"
                  ? "கணினி மாதிரி கண்டறிந்தது:"
                  : language === "hi"
                  ? "कंप्यूटर मॉडल द्वारा पाया गया:"
                  : language === "te"
                  ? "కంప్యూటర్ మోడల్ గుర్తించింది:"
                  : "What the model saw:"}
              </strong>
              {gradeContent.whatModelPredicted}
            </p>

            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 text-xs text-slate-300 mb-3 leading-relaxed">
              <strong className="text-teal-300 block mb-1">
                {language === "ta"
                  ? "எளிய மொழியில் இதன் அர்த்தம்:"
                  : language === "hi"
                  ? "सरल शब्दों में इसका अर्थ:"
                  : language === "te"
                  ? "సరళమైన మాటల్లో దీని అర్థం:"
                  : "In everyday words:"}
              </strong>
              {gradeContent.everydayExplanation}
            </div>

            <div className="text-[11px] text-slate-400 italic bg-slate-950/30 p-2.5 rounded border border-slate-800/40">
              💡{" "}
              <strong>
                {language === "ta"
                  ? "ஒப்பீடு:"
                  : language === "hi"
                  ? "सरल उदाहरण (सादृश्य):"
                  : language === "te"
                  ? "ఉదాహరణ పోలిక:"
                  : "Simple Analogy:"}
              </strong>{" "}
              {gradeContent.analogy}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <span className="text-slate-400">
              {language === "ta"
                ? "பரிந்துரைக்கப்பட்ட கவனிப்பு:"
                : language === "hi"
                ? "देखभाल श्रेणी:"
                : language === "te"
                ? "సంరక్షణ విభాగం:"
                : "Care Category:"}
            </span>
            <span className="font-semibold text-teal-300">{gradeContent.urgency}</span>
          </div>
        </div>

        {/* Card 2: What the Grad-CAM Heatmap Represents & Limits */}
        <div className="bg-slate-900/80 rounded-xl p-5 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 mb-2 text-teal-400 text-xs font-semibold uppercase tracking-wider">
              <Eye className="w-3.5 h-3.5" />
              <span>{heatmapContent.title}</span>
            </div>

            <h4 className="text-sm font-bold text-white mb-2">
              {heatmapContent.whatItRepresentsTitle}
            </h4>

            <p className="text-xs text-slate-300 leading-relaxed mb-3">
              {heatmapContent.whatItRepresentsText}
            </p>

            {/* Color Guide */}
            <div className="space-y-1.5 p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 text-[11px] mb-3">
              <span className="font-semibold text-slate-300 block mb-1">
                {heatmapContent.colorGuideTitle}
              </span>
              <div className="flex items-center space-x-2 text-amber-300">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 flex-shrink-0" />
                <span>{heatmapContent.colorRed}</span>
              </div>
              <div className="flex items-center space-x-2 text-emerald-300">
                <span className="w-2.5 h-2.5 rounded-full bg-yellow-400 flex-shrink-0" />
                <span>{heatmapContent.colorYellowGreen}</span>
              </div>
              <div className="flex items-center space-x-2 text-blue-300">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500 flex-shrink-0" />
                <span>{heatmapContent.colorBlue}</span>
              </div>
            </div>

            {/* What it CANNOT prove */}
            <div className="p-3 bg-rose-500/10 rounded-lg border border-rose-500/20 text-xs text-rose-300 space-y-1.5">
              <strong className="block text-rose-200">
                {heatmapContent.whatItCannotProveTitle}
              </strong>
              <ul className="list-disc list-inside space-y-1 text-[11px] leading-relaxed">
                {heatmapContent.limits.map((limit, idx) => (
                  <li key={idx}>{limit}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 leading-relaxed">
            <strong className="text-slate-300 block mb-0.5">
              {heatmapContent.doctorRoleTitle}
            </strong>
            {heatmapContent.doctorRoleText}
          </div>
        </div>
      </div>

      {/* Card 3: Evidence-Based Next Steps */}
      <div className="mt-5 p-5 bg-slate-900/60 rounded-xl border border-slate-800">
        <h4 className="text-sm font-bold text-white mb-3 flex items-center space-x-2">
          <HeartPulse className="w-4 h-4 text-teal-400" />
          <span>
            {language === "ta"
              ? "பரிந்துரைக்கப்படும் அடுத்த கட்ட நடவடிக்கைகள்"
              : language === "hi"
              ? "अनुशंसित साक्ष्य-आधारित अगले कदम"
              : language === "te"
              ? "సూచించబడిన తదుపరి చర్యలు"
              : "Recommended Evidence-Based Next Steps"}
          </span>
        </h4>

        <ul className="space-y-2 text-xs text-slate-300 leading-relaxed">
          {gradeContent.nextSteps.map((step, idx) => (
            <li key={idx} className="flex items-start space-x-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 flex-shrink-0 mt-0.5" />
              <span>{step}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Card 4: Urgent Emergency Warning Signs */}
      <div className="mt-4 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
        <div className="flex items-start space-x-2.5">
          <ShieldAlert className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
          <div>
            <strong className="text-rose-200 block text-xs mb-1">
              {emergencyContent.title}
            </strong>
            <p className="text-[11px] text-rose-300/90 mb-2 leading-relaxed">
              {emergencyContent.intro}
            </p>
            <ul className="list-disc list-inside space-y-1 text-[11px] text-rose-200 leading-relaxed">
              {emergencyContent.symptoms.map((symptom, idx) => (
                <li key={idx}>{symptom}</li>
              ))}
            </ul>
            <p className="mt-2 text-[11px] font-semibold text-rose-300">
              {emergencyContent.instruction}
            </p>
          </div>
        </div>
      </div>

      {/* Educational Notice Banner */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-start space-x-2">
        <Info className="w-3.5 h-3.5 text-slate-500 flex-shrink-0 mt-0.5" />
        <span>
          <strong className="text-slate-300">{t.disclaimerBannerTitle}: </strong>
          {t.disclaimerBannerText}
        </span>
      </div>
    </section>
  );
}
