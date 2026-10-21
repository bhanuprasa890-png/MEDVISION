import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Bot,
  User,
  AlertCircle,
  RefreshCw,
  Trash2,
  Sparkles,
  ShieldAlert,
  Info,
  Clock,
  HelpCircle,
  Eye,
  X,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Play,
  Pause,
  Square,
} from "lucide-react";
import { sendChatMessage } from "../services/api";
import {
  normalizeAssistantResponse,
  normalizeErrorMessage,
  extractRawMessageText,
} from "../utils/chatResponseNormalizer";
import { useLanguage } from "../context/LanguageContext";
import {
  speakUtterance,
  stopSpeech,
  pauseSpeech,
  resumeSpeech,
} from "../utils/speechSynthesis";

const MAX_INPUT_CHARS = 1000;

const SUGGESTED_PROMPTS = [
  "What is ischemic heart disease and what are its common risk factors?",
  "What does a diabetic retinopathy severity grade mean?",
  "How does Grad-CAM heatmapping work in research models?",
  "What does an AI confidence score represent in medical imaging?",
  "What is the difference between proliferative and non-proliferative DR?",
];

const SUGGESTED_PROMPTS_BY_LANG = {
  en: SUGGESTED_PROMPTS,
  ta: [
    "சர்க்கரை நோய் விழித்திரை பாதிப்பு (Diabetic Retinopathy) என்றால் என்ன?",
    "விழித்திரை ஆய்வு முடிவின் நிலைகள் (Grades 0-4) எவற்றைக் குறிக்கின்றன?",
    "கணினி மாதிரி காட்டும் வண்ண வரைபடம் (Grad-CAM Heatmap) எவ்வாறு செயல்படுகிறது?",
    "AI மாதிரி கொடுக்கும் உறுதிப்பாடு சதவீதம் எதைக் குறிக்கிறது?",
    "ஆரம்ப நிலை மற்றும் முற்றிய விழித்திரை பாதிப்புகளுக்கு உள்ள வேறுபாடு என்ன?",
  ],
  hi: [
    "डायबिटिक रेटिनोपैथी (Diabetic Retinopathy) क्या है और इसके सामान्य लक्षण क्या हैं?",
    "रेटिनागार्ड परिणाम के ग्रेड (Grades 0-4) का क्या अर्थ है?",
    "कंप्यूटर विज़न में ग्रैड-सीएएम (Grad-CAM) हीटमैप कैसे काम करता है?",
    "एआई मॉडल का कॉन्फिडेंस स्कोर क्या दर्शाता है?",
    "प्रोलिफेरेटिव और नॉन-प्रोलिफेरेटिव डीआर में क्या अंतर है?",
  ],
  te: [
    "డయాబెటిక్ రెటినోపతి (Diabetic Retinopathy) అంటే ఏమిటి?",
    "రెటీనాగార్డ్ ఫలితాల గ్రేడ్‌లు (Grades 0-4) వేటిని సూచిస్తాయి?",
    "కంప్యూటర్ విజన్‌లో గ్యాడ్-క్యామ్ (Grad-CAM) హీట్‌మ్యాప్ ఎలా పనిచేస్తుంది?",
    "AI మోడల్ విశ్వాస స్కోరు దేనిని సూచిస్తుంది?",
    "ప్రొలిఫరేటివ్ మరియు నాన్-ప్రొలిఫరేటివ్ DR మధ్య తేడా ఏమిటి?",
  ],
};

export function MedAssistChatPanel({
  chatStatus,
  onRefreshStatus,
  activeScanContext = null,
  onClearScanContext = null,
}) {
  const { language, t, currentLanguageInfo } = useLanguage();
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [lastFailedMessage, setLastFailedMessage] = useState(null);

  // Speech Recognition (Voice Input) States
  const [voiceInputStatus, setVoiceInputStatus] = useState("idle"); // 'idle' | 'listening' | 'processing' | 'unsupported'
  const [voiceInputError, setVoiceInputError] = useState(null);
  const recognitionRef = useRef(null);

  // Speech Synthesis (Read Aloud) States
  const [activeSpeechMessageId, setActiveSpeechMessageId] = useState(null);
  const [isSpeechPaused, setIsSpeechPaused] = useState(false);
  const [ttsFeedback, setTtsFeedback] = useState(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Clean up speech synthesis & recognition on unmount or language change
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      stopSpeech();
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {
          // Ignore abort errors on unmount
        }
      }
    };
  }, [language]);

  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputText).trim();
    if (!text || isLoading) return;

    if (text.length > MAX_INPUT_CHARS) {
      setErrorMessage(`Message exceeds maximum limit of ${MAX_INPUT_CHARS} characters.`);
      return;
    }

    // Stop listening if mic is active
    if (voiceInputStatus === "listening") {
      stopVoiceInput();
    }

    setErrorMessage(null);
    setLastFailedMessage(null);
    setVoiceInputError(null);

    // Prevent duplicate user bubbles when retrying a previously failed message
    const isRetry =
      messages.length > 0 &&
      messages[messages.length - 1].role === "user" &&
      messages[messages.length - 1].content === text;

    const updatedMessages = isRetry ? messages : [
      ...messages,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: text,
        timestamp: new Date().toISOString(),
      },
    ];

    // Prior turns (excluding active query) bounded to max 20 turns
    const priorTurns = isRetry ? messages.slice(0, -1) : messages;
    const historyPayload = priorTurns
      .slice(-20)
      .map((m) => ({
        role: m.role,
        content: typeof m.content === "string" ? m.content.slice(0, 8000).trim() : "",
      }))
      .filter((m) => m.content.length > 0);

    setMessages(updatedMessages);
    setInputText("");
    setIsLoading(true);

    try {
      // Pass validated scan context if present (contains no images, patient IDs, or files)
      // sendChatMessage(text, historyPayload, activeScanContext || null)
      const response = await sendChatMessage(text, historyPayload, activeScanContext || null, language);

      if (!response || !response.message || !response.message.trim()) {
        throw new Error("Received an empty response from MedAssist. Please try again.");
      }

      const normalized = normalizeAssistantResponse(response);
      if (!normalized.success) {
        throw new Error(
          normalized.error || "Received an invalid or malformed response from MedAssist. Please try again."
        );
      }

      const assistantMessage = {
        id: `assist-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        role: "assistant",
        content: normalized.messageText,
        provider: normalized.provider || response.provider,
        model: normalized.model || response.model,
        fallback_used: Boolean(normalized.fallback_used ?? response.fallback_used),
        disclaimer: normalized.disclaimer || response.disclaimer,
        timestamp: response.created_at || new Date().toISOString(),
      };

      setMessages((prev) => {
        if (prev.some((m) => m.id === assistantMessage.id)) return prev;
        return [...prev, assistantMessage];
      });
    } catch (error) {
      const errorMsg = normalizeErrorMessage(error, error?.status);
      const isUnconfigured =
        error?.status === 503 && errorMsg.toLowerCase().includes("not configured");

      const isQuotaExceeded =
        error?.status === 429 ||
        errorMsg.toLowerCase().includes("quota") ||
        errorMsg.toLowerCase().includes("billing") ||
        errorMsg.toLowerCase().includes("exhausted");

      const isHighDemand =
        (error?.status === 503 ||
          errorMsg.toLowerCase().includes("high demand") ||
          errorMsg.toLowerCase().includes("temporarily unavailable")) &&
        !isQuotaExceeded;

      let displayError = errorMsg;
      if (isUnconfigured) {
        displayError =
          "MedAssist AI provider is currently unconfigured. To enable live educational assistance, please configure GEMINI_API_KEY in the backend .env configuration.";
      } else if (isQuotaExceeded) {
        displayError =
          errorMsg ||
          "MedAssist AI provider quota has been exhausted. Please check your Gemini plan/billing details or configure OPENAI_API_KEY in backend/.env for automatic failover. Your message is preserved.";
      } else if (isHighDemand) {
        displayError =
          "MedAssist is temporarily experiencing high provider demand. Your message is preserved—please click Retry to send again.";
      }

      setErrorMessage(displayError);
      setLastFailedMessage(text);
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleRetry = () => {
    if (lastFailedMessage) {
      handleSendMessage(lastFailedMessage);
    }
  };

  const handleClearHistory = () => {
    handleStopReadAloud();
    stopVoiceInput();
    setMessages([]);
    setErrorMessage(null);
    setLastFailedMessage(null);
    setVoiceInputError(null);
  };

  // --- Speech Recognition (Voice Input) ---
  const isSpeechRecognitionSupported =
    typeof window !== "undefined" &&
    Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);

  const startVoiceInput = () => {
    if (!isSpeechRecognitionSupported) {
      setVoiceInputStatus("unsupported");
      setVoiceInputError(t("voice", "speechUnsupported"));
      return;
    }

    if (voiceInputStatus === "listening") {
      stopVoiceInput();
      return;
    }

    setVoiceInputError(null);
    setVoiceInputStatus("listening");

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = currentLanguageInfo.speechLang || "en-US";

      let finalTranscript = "";

      recognition.onstart = () => {
        setVoiceInputStatus("listening");
      };

      recognition.onresult = (event) => {
        let interimTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        const candidateText = finalTranscript || interimTranscript;
        if (candidateText && candidateText.trim()) {
          setInputText((prev) => {
            if (!prev.trim()) return candidateText.trim();
            return `${prev.trim()} ${candidateText.trim()}`.slice(0, MAX_INPUT_CHARS);
          });
        }
      };

      recognition.onerror = (event) => {
        const errType = event.error;
        let errMsg = t("voice", "speechGeneralError");

        if (errType === "not-allowed" || errType === "service-not-allowed") {
          errMsg = t("voice", "permissionDenied");
        } else if (errType === "no-speech") {
          errMsg = t("voice", "noSpeechDetected");
        } else if (errType === "network") {
          errMsg = t("voice", "networkError");
        }

        setVoiceInputError(errMsg);
        setVoiceInputStatus("idle");
        recognitionRef.current = null;
      };

      recognition.onend = () => {
        setVoiceInputStatus("idle");
        recognitionRef.current = null;
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.warn("SpeechRecognition initiation error:", err);
      setVoiceInputStatus("idle");
      setVoiceInputError(t("voice", "speechGeneralError"));
    }
  };

  const stopVoiceInput = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (err) {
        // Ignore
      }
      recognitionRef.current = null;
    }
    setVoiceInputStatus("idle");
  };

  // --- Speech Synthesis (Read Aloud) ---
  const handleReadAloud = (messageId, rawText) => {
    // Toggle pause/resume if this message is already playing
    if (activeSpeechMessageId === messageId) {
      if (isSpeechPaused) {
        resumeSpeech();
        setIsSpeechPaused(false);
      } else {
        pauseSpeech();
        setIsSpeechPaused(true);
      }
      return;
    }

    const cleanText =
      typeof rawText === "string" ? rawText : extractRawMessageText(rawText) || "";
    const textToSpeak = cleanText.replace(/[*_#`~]/g, "").trim();

    if (!textToSpeak) return;

    const speechLang = currentLanguageInfo?.speechLang || "en-IN";

    const result = speakUtterance({
      text: textToSpeak,
      langCode: language,
      rate: 0.95,
      onStart: () => {
        setActiveSpeechMessageId(messageId);
        setIsSpeechPaused(false);
        setTtsFeedback(null);
      },
      onEnd: () => {
        setActiveSpeechMessageId(null);
        setIsSpeechPaused(false);
      },
      onError: () => {
        setActiveSpeechMessageId(null);
        setIsSpeechPaused(false);
      },
      onVoiceUnavailable: () => {
        setActiveSpeechMessageId(null);
        setIsSpeechPaused(false);
        setTtsFeedback({
          messageId,
          text: t("medassist", "voiceSynthesizerUnavailable"),
        });
      },
    });

    if (!result.ok) {
      setActiveSpeechMessageId(null);
      setIsSpeechPaused(false);
      if (result.reason === "VOICE_UNAVAILABLE" || result.reason === "SPEECH_UNSUPPORTED") {
        setTtsFeedback({
          messageId,
          text: t("medassist", "voiceSynthesizerUnavailable"),
        });
      }
    }
  };

  const handleStopReadAloud = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    stopSpeech();
    setActiveSpeechMessageId(null);
    setIsSpeechPaused(false);
  };

  const charCount = inputText.length;
  const isNearLimit = charCount > MAX_INPUT_CHARS * 0.9;
  const isOverLimit = charCount > MAX_INPUT_CHARS;

  const activeSuggestedPrompts =
    SUGGESTED_PROMPTS_BY_LANG[language] || SUGGESTED_PROMPTS;

  return (
    <div className="flex flex-col h-[700px] max-h-[85vh] bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
      {/* 1. Header Toolbar */}
      <div className="flex items-center justify-between px-6 py-4 bg-slate-900/90 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-500 flex items-center justify-center shadow-md shadow-teal-500/20">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-white">
                {t("medassist", "headerTitle")}
              </h2>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20">
                Health Education
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {t("medassist", "headerSubtitle")}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {messages.length > 0 && (
            <button
              onClick={handleClearHistory}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
              title={t("medassist", "clearHistory")}
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{t("medassist", "clearHistory")}</span>
            </button>
          )}

          {chatStatus && (
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs bg-slate-950 border border-slate-800">
              <span
                className={`w-2 h-2 rounded-full ${
                  chatStatus.is_configured
                    ? "bg-emerald-400 animate-pulse motion-reduce:animate-none"
                    : "bg-amber-400"
                }`}
              />
              <span className="text-slate-300 capitalize text-[11px]">
                {chatStatus.is_configured
                  ? `${chatStatus.provider} (${chatStatus.model})${
                      chatStatus.fallback_configured
                        ? ` + fallback (${chatStatus.fallback_provider})`
                        : ""
                    }`
                  : "Provider Unconfigured"}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* 2. Educational & Privacy Safety Banners */}
      <div className="bg-slate-950/80 border-b border-slate-800/80 px-4 py-2 space-y-1">
        <div className="flex items-center space-x-2 text-[11px] text-teal-300">
          <ShieldAlert className="w-3.5 h-3.5 flex-shrink-0 text-teal-400" />
          <span>
            <strong>Educational & Research Use Only:</strong> Not a diagnostic service or clinical
            directive. Always consult a licensed healthcare professional for personal medical concerns.
          </span>
        </div>
        <div className="flex items-center space-x-2 text-[10px] text-slate-400">
          <Info className="w-3 h-3 flex-shrink-0 text-slate-500" />
          <span>
            <strong>Privacy Guard:</strong> Never enter patient names, medical record numbers (MRNs), or
            personal health identifiers. MedVision AI does not persist conversational data.
          </span>
        </div>
      </div>

      {/* 2b. Active RetinaGuard Scan Context Banner (if user chose to share result) */}
      {activeScanContext && (
        <div className="bg-teal-950/30 border-b border-teal-500/30 px-4 py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs animate-fadeIn">
          <div className="flex items-center space-x-2.5">
            <span className="p-1 rounded-md bg-teal-500/20 text-teal-300 flex-shrink-0">
              <Eye className="w-4 h-4" />
            </span>
            <div>
              <div className="flex items-center space-x-2 flex-wrap">
                <span className="font-semibold text-teal-200">
                  Discussing RetinaGuard Result:
                </span>
                <span className="font-bold text-white">
                  {activeScanContext.class_label ||
                    (activeScanContext.predicted_class !== null &&
                    activeScanContext.predicted_class !== undefined
                      ? `Grade ${activeScanContext.predicted_class}`
                      : "Retinal Scan")}
                </span>
                {activeScanContext.confidence_score !== null &&
                  activeScanContext.confidence_score !== undefined && (
                    <span className="text-teal-400 font-mono text-[11px]">
                      ({(activeScanContext.confidence_score * 100).toFixed(1)}% score)
                    </span>
                  )}
              </div>
              <p className="text-[10px] text-slate-400">
                Educational discussion mode • {activeScanContext.model_version || "ResNet-18"} (Not a diagnosis)
              </p>
            </div>
          </div>

          {onClearScanContext && (
            <button
              onClick={onClearScanContext}
              className="self-start sm:self-center inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-medium transition-colors cursor-pointer border border-slate-700/80"
              title="Remove scan context and switch to general health education"
            >
              <X className="w-3 h-3" />
              <span>Clear Context</span>
            </button>
          )}
        </div>
      )}

      {/* 3. Messages Scroll View */}
      <div
        role="region"
        aria-label="Conversation messages"
        tabIndex={0}
        className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-teal-500/50"
      >
        {messages.length === 0 ? (
          // Empty State
          <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto py-8">
            <div className="w-16 h-16 rounded-2xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400 mb-4 shadow-lg shadow-teal-500/5">
              <Sparkles className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Welcome to MedAssist</h3>
            <p className="text-xs text-slate-400 mb-6 leading-relaxed">
              Ask questions about ophthalmic anatomy, diabetic retinopathy classifications,
              deep learning terminology, or explainability heatmaps like Grad-CAM.
            </p>

            <div className="w-full space-y-2 text-left">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                <HelpCircle className="w-3 h-3 text-teal-400" />
                <span>
                  {activeScanContext
                    ? "Suggested Questions for this Result"
                    : "Suggested Research Questions"}
                </span>
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {(activeScanContext ? [
                  `What does "${activeScanContext.class_label || 'Grade ' + activeScanContext.predicted_class}" mean?`,
                  `How should I interpret the ${activeScanContext.confidence_score !== null && activeScanContext.confidence_score !== undefined ? (activeScanContext.confidence_score * 100).toFixed(1) + '%' : 'model'} output score?`,
                  `What microvascular findings are typical in ${activeScanContext.class_label || 'diabetic retinopathy'}?`,
                  "Does RetinaGuard detect cardiovascular or heart disease?",
                ] : activeSuggestedPrompts).map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(prompt)}
                    className="p-3 rounded-xl bg-slate-800/70 hover:bg-slate-800 border border-slate-700/60 hover:border-teal-500/40 text-left text-xs text-slate-200 transition-all cursor-pointer group"
                  >
                    <span className="line-clamp-2 group-hover:text-teal-300 transition-colors">
                      {prompt}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // Message List
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
            >
              {/* Speaker Metadata */}
              <div className="flex items-center space-x-1.5 mb-1 px-1">
                {msg.role === "user" ? (
                  <>
                    <span className="text-[11px] font-medium text-slate-400">You</span>
                    <User className="w-3 h-3 text-teal-400" />
                  </>
                ) : (
                  <>
                    <Bot className="w-3 h-3 text-cyan-400" />
                    <span className="text-[11px] font-medium text-slate-300">MedAssist</span>
                    {msg.provider && (
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 uppercase font-mono">
                        {msg.provider}
                        {msg.fallback_used ? " (fallback)" : ""}
                      </span>
                    )}
                  </>
                )}
                <span className="text-[10px] text-slate-500 flex items-center space-x-1">
                  <Clock className="w-2.5 h-2.5" />
                  <span>
                    {new Date(msg.timestamp).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </span>
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-gradient-to-r from-teal-600 to-cyan-600 text-white shadow-md shadow-teal-500/10 rounded-br-none"
                    : "bg-slate-800/90 border border-slate-700 text-slate-100 rounded-bl-none shadow-sm"
                }`}
              >
                <div className="whitespace-pre-wrap break-words">{typeof msg.content === "string" ? msg.content : (extractRawMessageText(msg.content) || "Malformed message content")}</div>

                {/* Spoken Audio Controls for Assistant Messages */}
                {msg.role === "assistant" && (
                  <div className="mt-3 pt-2 border-t border-slate-700/60 flex items-center justify-between gap-2 flex-wrap text-xs">
                    <div className="flex items-center space-x-1.5">
                      <button
                        type="button"
                        onClick={() => handleReadAloud(msg.id, msg.content)}
                        aria-label={
                          activeSpeechMessageId === msg.id && !isSpeechPaused
                            ? t("medassist", "pauseAudio")
                            : activeSpeechMessageId === msg.id && isSpeechPaused
                            ? t("medassist", "resumeAudio")
                            : t("medassist", "readAloud")
                        }
                        className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-[11px] font-medium border transition-all cursor-pointer ${
                          activeSpeechMessageId === msg.id
                            ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                            : "bg-slate-900/80 hover:bg-slate-900 text-slate-300 hover:text-white border-slate-700"
                        }`}
                      >
                        {activeSpeechMessageId === msg.id && !isSpeechPaused ? (
                          <>
                            <Pause className="w-3 h-3 text-amber-300" />
                            <span>{t("medassist", "pauseAudio")}</span>
                          </>
                        ) : activeSpeechMessageId === msg.id && isSpeechPaused ? (
                          <>
                            <Play className="w-3 h-3 text-emerald-300" />
                            <span>{t("medassist", "resumeAudio")}</span>
                          </>
                        ) : (
                          <>
                            <Volume2 className="w-3 h-3 text-teal-400" />
                            <span>{t("medassist", "readAloud")}</span>
                          </>
                        )}
                      </button>

                      {activeSpeechMessageId === msg.id && (
                        <button
                          type="button"
                          onClick={handleStopReadAloud}
                          aria-label={t("medassist", "stopAudio")}
                          className="p-1 rounded-md bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-700 cursor-pointer"
                          title={t("medassist", "stopAudio")}
                        >
                          <Square className="w-3 h-3" />
                        </button>
                      )}
                    </div>

                    {/* Feedback if specific voice missing */}
                    {ttsFeedback && ttsFeedback.messageId === msg.id && (
                      <span className="text-[10px] text-amber-300/90 italic">
                        {ttsFeedback.text}
                      </span>
                    )}
                  </div>
                )}

                {/* Assistant Disclaimer Footer */}
                {msg.role === "assistant" && msg.disclaimer && (
                  <div className="mt-2 pt-2 border-t border-slate-700/60 text-[10px] text-slate-400 italic">
                    {msg.disclaimer}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Loading / Thinking State */}
        {isLoading && (
          <div role="status" aria-live="polite" className="flex flex-col items-start space-y-1">
            <div className="flex items-center space-x-1.5 mb-1 px-1">
              <Bot className="w-3 h-3 text-cyan-400 animate-spin motion-reduce:animate-none" />
              <span className="text-[11px] font-medium text-slate-300">
                MedAssist is thinking...
              </span>
            </div>
            <div className="bg-slate-800/90 border border-slate-700 rounded-2xl rounded-bl-none px-4 py-3 shadow-sm">
              <div className="flex items-center space-x-2">
                <div
                  className="w-2 h-2 rounded-full bg-teal-400 animate-bounce motion-reduce:animate-none"
                  style={{ animationDelay: "0ms" }}
                />
                <div
                  className="w-2 h-2 rounded-full bg-teal-400 animate-bounce motion-reduce:animate-none"
                  style={{ animationDelay: "150ms" }}
                />
                <div
                  className="w-2 h-2 rounded-full bg-teal-400 animate-bounce motion-reduce:animate-none"
                  style={{ animationDelay: "300ms" }}
                />
                <span className="text-xs text-slate-400 ml-1">
                  Consulting medical research knowledge...
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 4. Voice Input Active Indicator & Error Banners */}
      {voiceInputStatus === "listening" && (
        <div
          role="status"
          aria-live="polite"
          className="mx-4 mb-2 p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center justify-between animate-pulse motion-reduce:animate-none"
        >
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping motion-reduce:animate-none flex-shrink-0" />
            <span className="font-medium">{t("voice", "listeningState")}</span>
          </div>
          <button
            type="button"
            onClick={stopVoiceInput}
            className="px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 text-[11px] font-semibold border border-amber-500/30 cursor-pointer"
          >
            {t("voice", "stopListening")}
          </button>
        </div>
      )}

      {voiceInputError && (
        <div
          role="alert"
          aria-live="assertive"
          className="mx-4 mb-2 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between"
        >
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
            <span>{voiceInputError}</span>
          </div>
          <button
            type="button"
            onClick={() => setVoiceInputError(null)}
            className="text-slate-400 hover:text-white p-1"
            title="Dismiss error"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 5. Error & Retry Notification Banner */}
      {errorMessage && (
        <div
          role="alert"
          aria-live="assertive"
          className="mx-4 mb-2 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start justify-between"
        >
          <div className="flex items-start space-x-2 pr-2">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
            <div className="leading-relaxed">{errorMessage}</div>
          </div>
          {lastFailedMessage && (
            <div className="flex items-center space-x-2 flex-shrink-0">
              <button
                onClick={() => {
                  setInputText(lastFailedMessage);
                  inputRef.current?.focus();
                }}
                disabled={isLoading}
                className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-[11px] transition-colors cursor-pointer border border-slate-700"
                title="Restore message to input box to edit"
              >
                <span>Edit</span>
              </button>
              <button
                onClick={handleRetry}
                disabled={isLoading}
                className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-rose-600/30 hover:bg-rose-600/50 text-white font-medium text-[11px] transition-colors flex-shrink-0 cursor-pointer"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Retry</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* 6. Input Area with Voice Microphone Button */}
      <div className="p-4 bg-slate-900 border-t border-slate-800">
        <div className="relative">
          <textarea
            ref={inputRef}
            id="medassist-chat-textarea"
            aria-label="Ask MedAssist a question about medical imaging or health education"
            rows={2}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder={
              isLoading
                ? "Waiting for MedAssist response..."
                : "Ask about medical concepts, DR stages, or Grad-CAM (Shift+Enter for newline)..."
            }
            className={`w-full bg-slate-950 border rounded-xl py-2.5 pl-3 pr-32 text-sm text-slate-100 placeholder-slate-500 resize-none focus:outline-none transition-colors ${
              isOverLimit
                ? "border-rose-500 focus:border-rose-500"
                : isNearLimit
                ? "border-amber-500 focus:border-amber-500"
                : "border-slate-800 focus:border-teal-500"
            }`}
          />

          <div className="absolute right-2.5 bottom-3.5 flex items-center space-x-1.5">
            {/* Character counter */}
            <span
              aria-live="polite"
              className={`text-[10px] font-mono mr-1 ${
                isOverLimit
                  ? "text-rose-400 font-semibold"
                  : isNearLimit
                  ? "text-amber-400"
                  : "text-slate-500"
              }`}
            >
              {charCount}/{MAX_INPUT_CHARS}
            </span>

            {/* Microphone Voice Input Button */}
            <button
              type="button"
              onClick={startVoiceInput}
              disabled={isLoading}
              aria-label={
                voiceInputStatus === "listening"
                  ? t("voice", "stopListening")
                  : t("voice", "startListening")
              }
              aria-pressed={voiceInputStatus === "listening"}
              className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all cursor-pointer ${
                voiceInputStatus === "listening"
                  ? "bg-rose-600 text-white shadow-lg shadow-rose-500/30 animate-pulse motion-reduce:animate-none"
                  : "bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700"
              }`}
              title={
                voiceInputStatus === "listening"
                  ? t("voice", "stopListening")
                  : t("voice", "startListening")
              }
            >
              {voiceInputStatus === "listening" ? (
                <MicOff className="w-4 h-4" />
              ) : (
                <Mic className="w-4 h-4 text-teal-400" />
              )}
            </button>

            {/* Send Button */}
            <button
              onClick={() => handleSendMessage()}
              disabled={isLoading || !inputText.trim() || isOverLimit}
              aria-label="Send message"
              className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                isLoading || !inputText.trim() || isOverLimit
                  ? "bg-slate-800 text-slate-600 cursor-not-allowed"
                  : "bg-teal-600 hover:bg-teal-500 text-white shadow-md shadow-teal-500/20 cursor-pointer"
              }`}
              title="Send message (Enter)"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between mt-1 px-1 text-[10px] text-slate-500">
          <span>Press <strong>Enter</strong> to send, <strong>Shift+Enter</strong> for newline</span>
          <span>Never submit personal medical data</span>
        </div>
      </div>
    </div>
  );
}
