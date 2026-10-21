/**
 * Language-Aware Speech Synthesis Utility for MEDVISION.
 *
 * Implements strict language-to-locale mapping, deterministic voice selection,
 * asynchronous voices loading, and zero silent English fallback for regional languages
 * (Tamil, Hindi, Telugu).
 */

export const SPEECH_LOCALES = {
  en: "en-IN",
  ta: "ta-IN",
  hi: "hi-IN",
  te: "te-IN",
};

/**
 * Returns the exact speech locale for a supported application language code.
 *
 * @param {string} langCode - Application language code ('en', 'ta', 'hi', 'te')
 * @returns {string} Target BCP-47 speech locale
 */
export function getSpeechLocale(langCode) {
  return SPEECH_LOCALES[langCode] || SPEECH_LOCALES.en;
}

/**
 * Deterministically finds a browser speech voice matching the requested language.
 *
 * CRITICAL SAFETY RULE:
 * Never match generic terms like 'india' across non-English languages because
 * English (India) voices contain 'India' in their name and would mistakenly
 * speak Tamil, Hindi, or Telugu using an English engine.
 *
 * @param {SpeechSynthesisVoice[]} voices - Available browser voices
 * @param {string} langCode - Application language code ('en', 'ta', 'hi', 'te')
 * @returns {SpeechSynthesisVoice | null} Matched voice or null
 */
export function findMatchingVoice(voices, langCode) {
  if (!Array.isArray(voices) || voices.length === 0) {
    return null;
  }

  const targetLocale = getSpeechLocale(langCode).toLowerCase(); // e.g. 'ta-in'
  const langPrefix = (langCode || "en").toLowerCase(); // e.g. 'ta'

  if (langPrefix === "ta") {
    // 1. Exact locale match (ta-IN, ta_IN)
    const exact = voices.find(
      (v) => (v.lang || "").toLowerCase().replace(/_/g, "-") === targetLocale
    );
    if (exact) return exact;

    // 2. Tamil language prefix match (ta-*, ta)
    const prefixMatch = voices.find((v) => {
      const l = (v.lang || "").toLowerCase().replace(/_/g, "-");
      return l === "ta" || l.startsWith("ta-");
    });
    if (prefixMatch) return prefixMatch;

    // 3. Supplementary name match: 'tamil', 'தமிழ்', 'valluvar', 'latha'
    // Metadata must NOT conflict with an unrelated language (e.g. must not be English, Hindi, etc.)
    const nameMatch = voices.find((v) => {
      const n = (v.name || "").toLowerCase();
      const l = (v.lang || "").toLowerCase().replace(/_/g, "-");
      const isTamilName =
        n.includes("tamil") ||
        n.includes("தமிழ்") ||
        n.includes("valluvar") ||
        n.includes("latha");
      const isNotConflicting =
        !l ||
        l === "ta" ||
        l.startsWith("ta-") ||
        (!l.startsWith("en") &&
          !l.startsWith("hi") &&
          !l.startsWith("te") &&
          !l.startsWith("es") &&
          !l.startsWith("fr") &&
          !l.startsWith("de") &&
          !l.startsWith("zh") &&
          !l.startsWith("ja"));
      return isTamilName && isNotConflicting;
    });
    return nameMatch || null;
  }

  if (langPrefix === "hi") {
    // 1. Exact locale match (hi-IN, hi_IN)
    const exact = voices.find(
      (v) => (v.lang || "").toLowerCase().replace(/_/g, "-") === targetLocale
    );
    if (exact) return exact;

    // 2. Hindi language prefix match (hi-*, hi)
    const prefixMatch = voices.find((v) => {
      const l = (v.lang || "").toLowerCase().replace(/_/g, "-");
      return l === "hi" || l.startsWith("hi-");
    });
    if (prefixMatch) return prefixMatch;

    // 3. Supplementary name match: 'hindi', 'हिन्दी', 'हिंदी', 'kalpana', 'hemant'
    const nameMatch = voices.find((v) => {
      const n = (v.name || "").toLowerCase();
      const l = (v.lang || "").toLowerCase().replace(/_/g, "-");
      const isHindiName =
        n.includes("hindi") ||
        n.includes("हिन्दी") ||
        n.includes("हिंदी") ||
        n.includes("kalpana") ||
        n.includes("hemant");
      const isNotConflicting =
        !l ||
        l === "hi" ||
        l.startsWith("hi-") ||
        (!l.startsWith("en") &&
          !l.startsWith("ta") &&
          !l.startsWith("te") &&
          !l.startsWith("es") &&
          !l.startsWith("fr") &&
          !l.startsWith("de") &&
          !l.startsWith("zh") &&
          !l.startsWith("ja"));
      return isHindiName && isNotConflicting;
    });
    return nameMatch || null;
  }

  if (langPrefix === "te") {
    // 1. Exact locale match (te-IN, te_IN)
    const exact = voices.find(
      (v) => (v.lang || "").toLowerCase().replace(/_/g, "-") === targetLocale
    );
    if (exact) return exact;

    // 2. Telugu language prefix match (te-*, te)
    const prefixMatch = voices.find((v) => {
      const l = (v.lang || "").toLowerCase().replace(/_/g, "-");
      return l === "te" || l.startsWith("te-");
    });
    if (prefixMatch) return prefixMatch;

    // 3. Supplementary name match: 'telugu', 'తెలుగు', 'chitra', 'mohan'
    const nameMatch = voices.find((v) => {
      const n = (v.name || "").toLowerCase();
      const l = (v.lang || "").toLowerCase().replace(/_/g, "-");
      const isTeluguName =
        n.includes("telugu") ||
        n.includes("తెలుగు") ||
        n.includes("chitra") ||
        n.includes("mohan");
      const isNotConflicting =
        !l ||
        l === "te" ||
        l.startsWith("te-") ||
        (!l.startsWith("en") &&
          !l.startsWith("ta") &&
          !l.startsWith("hi") &&
          !l.startsWith("es") &&
          !l.startsWith("fr") &&
          !l.startsWith("de") &&
          !l.startsWith("zh") &&
          !l.startsWith("ja"));
      return isTeluguName && isNotConflicting;
    });
    return nameMatch || null;
  }

  // English (en) - Prefer en-IN per Task 25 specification, then any en-*
  const enIn = voices.find(
    (v) => (v.lang || "").toLowerCase().replace(/_/g, "-") === "en-in"
  );
  if (enIn) return enIn;

  const enAny = voices.find((v) => {
    const l = (v.lang || "").toLowerCase().replace(/_/g, "-");
    return l === "en" || l.startsWith("en-");
  });
  return enAny || null;
}

/**
 * Checks whether an authentic speech voice exists for the specified language.
 *
 * @param {string} langCode - Language code ('en', 'ta', 'hi', 'te')
 * @param {SpeechSynthesisVoice[]} [voices] - Optional pre-fetched voices list
 * @returns {boolean} True if matching voice is available
 */
export function isVoiceAvailable(langCode, voices = null) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    return false;
  }

  const voiceList = voices || window.speechSynthesis.getVoices();
  const match = findMatchingVoice(voiceList, langCode);
  return match !== null;
}

/**
 * Subscribes to browser 'voiceschanged' events and returns an unsubscribe function.
 *
 * @param {Function} callback - Invoked when voices change with the updated voices array
 * @returns {Function} Cleanup / unsubscribe function
 */
export function subscribeVoicesChanged(callback) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    return () => {};
  }

  const synth = window.speechSynthesis;
  const handler = () => {
    callback(synth.getVoices() || []);
  };

  if (synth.addEventListener) {
    synth.addEventListener("voiceschanged", handler);
  } else {
    synth.onvoiceschanged = handler;
  }

  return () => {
    if (synth.removeEventListener) {
      synth.removeEventListener("voiceschanged", handler);
    } else if (synth.onvoiceschanged === handler) {
      synth.onvoiceschanged = null;
    }
  };
}

/**
 * Asynchronously loads voices from the browser, awaiting 'voiceschanged' if the list is empty.
 *
 * @param {number} [timeoutMs=1000] - Timeout in milliseconds
 * @returns {Promise<SpeechSynthesisVoice[]>} Available voices
 */
export function loadVoicesAsync(timeoutMs = 1000) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    return Promise.resolve([]);
  }

  const synth = window.speechSynthesis;
  const initial = synth.getVoices();
  if (Array.isArray(initial) && initial.length > 0) {
    return Promise.resolve(initial);
  }

  return new Promise((resolve) => {
    let resolved = false;

    const cleanup = () => {
      resolved = true;
      if (synth.removeEventListener) {
        synth.removeEventListener("voiceschanged", handler);
      } else {
        synth.onvoiceschanged = null;
      }
    };

    const handler = () => {
      if (resolved) return;
      cleanup();
      resolve(synth.getVoices() || []);
    };

    if (synth.addEventListener) {
      synth.addEventListener("voiceschanged", handler);
    } else {
      synth.onvoiceschanged = handler;
    }

    setTimeout(() => {
      if (resolved) return;
      cleanup();
      resolve(synth.getVoices() || []);
    }, timeoutMs);
  });
}

/**
 * Speaks an utterance with strict locale enforcement and non-English voice verification.
 *
 * CRITICAL SAFETY REQUIREMENT:
 * If the language is non-English ('ta', 'hi', 'te') and no matching regional voice
 * is available on the user's device, this function WILL NOT call window.speechSynthesis.speak().
 * Instead, it immediately calls onVoiceUnavailable() and returns { ok: false, reason: 'VOICE_UNAVAILABLE' }.
 *
 * @param {Object} options
 * @param {string} options.text - Text to speak
 * @param {string} [options.langCode='en'] - Selected application language
 * @param {number} [options.rate=0.95] - Speech rate (0.1 to 10)
 * @param {number} [options.pitch=1.0] - Speech pitch
 * @param {Function} [options.onStart] - Callback when speech actually starts
 * @param {Function} [options.onEnd] - Callback when speech completes
 * @param {Function} [options.onError] - Callback on error
 * @param {Function} [options.onVoiceUnavailable] - Callback when matching voice is missing
 * @returns {{ ok: boolean, reason?: string, utterance?: SpeechSynthesisUtterance }}
 */
export function speakUtterance({
  text,
  langCode = "en",
  rate = 0.95,
  pitch = 1.0,
  onStart,
  onEnd,
  onError,
  onVoiceUnavailable,
}) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    onError?.({ error: "SPEECH_UNSUPPORTED" });
    return { ok: false, reason: "SPEECH_UNSUPPORTED" };
  }

  const synth = window.speechSynthesis;

  // Always cancel any existing or stale speech before starting
  synth.cancel();

  const cleanText = (text || "").trim();
  if (!cleanText) {
    return { ok: false, reason: "EMPTY_TEXT" };
  }

  const voices = synth.getVoices() || [];
  const matchedVoice = findMatchingVoice(voices, langCode);
  const targetLocale = getSpeechLocale(langCode);

  // Mandatory Guard: Never silently read Tamil, Hindi, or Telugu text with an English voice
  if (langCode !== "en" && !matchedVoice) {
    onVoiceUnavailable?.({
      langCode,
      locale: targetLocale,
      availableVoicesCount: voices.length,
    });
    return {
      ok: false,
      reason: "VOICE_UNAVAILABLE",
      langCode,
      locale: targetLocale,
    };
  }

  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.lang = targetLocale;
  if (matchedVoice) {
    utterance.voice = matchedVoice;
  }
  utterance.rate = rate;
  utterance.pitch = pitch;

  utterance.onstart = () => {
    onStart?.();
  };

  utterance.onend = () => {
    onEnd?.();
  };

  utterance.onerror = (e) => {
    // Normal cancellation (via stopSpeech or language change) fires 'canceled' or 'interrupted'
    if (e && (e.error === "canceled" || e.error === "interrupted")) {
      return;
    }
    onError?.(e);
  };

  try {
    synth.speak(utterance);
    return { ok: true, utterance, voice: matchedVoice, locale: targetLocale };
  } catch (err) {
    onError?.(err);
    return { ok: false, reason: "SPEAK_CALL_FAILED", error: err };
  }
}

/**
 * Stops any ongoing or queued browser speech synthesis.
 */
export function stopSpeech() {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

/**
 * Pauses active browser speech synthesis.
 */
export function pauseSpeech() {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.pause();
  }
}

/**
 * Resumes paused browser speech synthesis.
 */
export function resumeSpeech() {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.resume();
  }
}
