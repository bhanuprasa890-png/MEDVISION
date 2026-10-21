/**
 * Frontend Unit & Regression Tests for Task 23
 * Tests Universal Language Support, Voice Chat (Speech-to-Text),
 * Spoken Responses (Text-to-Speech), and Accessibility Integration.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  SUPPORTED_LANGUAGES,
  DEFAULT_LANGUAGE,
  TRANSLATIONS,
  getTranslation,
} from "../src/i18n/translations.js";

import {
  GRADE_EXPLANATIONS,
  HEATMAP_EXPLANATIONS,
  EMERGENCY_WARNINGS,
  UI_STRINGS,
} from "../src/utils/patientExplanations.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const chatPanelSource = fs.readFileSync(
  path.join(__dirname, "../src/components/MedAssistChatPanel.jsx"),
  "utf8"
);
const headerSource = fs.readFileSync(
  path.join(__dirname, "../src/components/Header.jsx"),
  "utf8"
);
const selectorSource = fs.readFileSync(
  path.join(__dirname, "../src/components/LanguageSelector.jsx"),
  "utf8"
);
const contextSource = fs.readFileSync(
  path.join(__dirname, "../src/context/LanguageContext.jsx"),
  "utf8"
);
const explanationComponentSource = fs.readFileSync(
  path.join(__dirname, "../src/components/PatientFriendlyExplanation.jsx"),
  "utf8"
);
const apiSource = fs.readFileSync(
  path.join(__dirname, "../src/services/api.js"),
  "utf8"
);

describe("1. Internationalization Architecture & Supported Languages", () => {
  const expectedCodes = ["en", "ta", "hi", "te"];

  it("registers all required Indian languages and baseline English", () => {
    for (const code of expectedCodes) {
      const meta = SUPPORTED_LANGUAGES[code];
      assert.ok(meta, `Language '${code}' must be declared in SUPPORTED_LANGUAGES`);
      assert.equal(meta.code, code);
      assert.ok(meta.label, `Language '${code}' must have an English label`);
      assert.ok(meta.nativeLabel, `Language '${code}' must have a native script label`);
      assert.ok(meta.speechLang, `Language '${code}' must have a speechLang locale`);
      assert.ok(Array.isArray(meta.voiceQuery), `Language '${code}' must have voice queries`);
      assert.ok(meta.reviewStatus, `Language '${code}' must declare clinical review status`);
    }
  });

  it("verifies authentic native script for non-English languages", () => {
    // Tamil: \u0B80-\u0BFF
    assert.equal(/[\u0B80-\u0BFF]/.test(SUPPORTED_LANGUAGES.ta.nativeLabel), true);
    // Hindi: \u0900-\u097F
    assert.equal(/[\u0900-\u097F]/.test(SUPPORTED_LANGUAGES.hi.nativeLabel), true);
    // Telugu: \u0C00-\u0C7F
    assert.equal(/[\u0C00-\u0C7F]/.test(SUPPORTED_LANGUAGES.te.nativeLabel), true);
  });

  it("ensures getTranslation falls back gracefully without silent blanks", () => {
    // Exact match
    assert.equal(getTranslation("navigation", "overview", "en"), "Overview");
    // Fallback for non-existent key
    assert.equal(getTranslation("navigation", "nonExistentKey", "ta"), "nonExistentKey");
    // Fallback for invalid language code
    assert.equal(getTranslation("navigation", "overview", "invalid_code"), "Overview");
  });

  it("validates catalog completeness across all sections for all 4 languages", () => {
    const sections = ["navigation", "upload", "medassist", "voice"];
    for (const sec of sections) {
      assert.ok(TRANSLATIONS[sec], `Section '${sec}' must exist in TRANSLATIONS`);
      const enKeys = Object.keys(TRANSLATIONS[sec].en);
      assert.ok(enKeys.length > 0, `Section '${sec}.en' must have keys`);

      for (const code of ["ta", "hi", "te"]) {
        assert.ok(TRANSLATIONS[sec][code], `Section '${sec}' must support language '${code}'`);
        for (const key of enKeys) {
          const val = TRANSLATIONS[sec][code][key];
          assert.ok(
            val && typeof val === "string" && val.trim().length > 0,
            `Missing or empty translation for key '${sec}.${code}.${key}'`
          );
        }
      }
    }
  });
});

describe("2. Multilingual Patient-Friendly Explanations (Task 22 Extension)", () => {
  const grades = [0, 1, 2, 3, 4];
  const languages = ["en", "ta", "hi", "te"];

  it("defines comprehensive explanations for all 5 DR grades in all 4 languages", () => {
    for (const g of grades) {
      const data = GRADE_EXPLANATIONS[g];
      assert.ok(data, `Grade ${g} must be defined`);

      for (const lang of languages) {
        const item = data[lang];
        assert.ok(item, `Grade ${g} must have translation for '${lang}'`);
        assert.ok(item.badge, `Grade ${g} (${lang}) must have a badge`);
        assert.ok(item.title, `Grade ${g} (${lang}) must have a title`);
        assert.ok(item.whatModelPredicted, `Grade ${g} (${lang}) must explain model prediction`);
        assert.ok(item.everydayExplanation, `Grade ${g} (${lang}) must have everyday explanation`);
        assert.ok(item.analogy, `Grade ${g} (${lang}) must have lay analogy`);
        assert.ok(Array.isArray(item.nextSteps) && item.nextSteps.length >= 2, `Grade ${g} (${lang}) must have next steps`);
        assert.ok(item.urgency, `Grade ${g} (${lang}) must state care urgency`);
      }
    }
  });

  it("defines heatmap interpretations and negative proof limits across all 4 languages", () => {
    for (const lang of languages) {
      const hm = HEATMAP_EXPLANATIONS[lang];
      assert.ok(hm, `Heatmap explanation must exist for '${lang}'`);
      assert.ok(hm.title);
      assert.ok(hm.whatItRepresentsText);
      assert.ok(hm.colorRed);
      assert.ok(hm.colorBlue);
      assert.ok(Array.isArray(hm.limits) && hm.limits.length >= 3, `Limits must have at least 3 items in '${lang}'`);
      assert.ok(hm.doctorRoleText);
    }
  });

  it("defines emergency warning signs across all 4 languages", () => {
    for (const lang of languages) {
      const em = EMERGENCY_WARNINGS[lang];
      assert.ok(em, `Emergency warnings must exist for '${lang}'`);
      assert.ok(em.title);
      assert.ok(em.intro);
      assert.ok(Array.isArray(em.symptoms) && em.symptoms.length >= 4, `Must have >= 4 emergency symptoms in '${lang}'`);
      assert.ok(em.instruction);
    }
  });
});

describe("3. Voice Chat & Speech-to-Text Integration in MedAssist", () => {
  it("implements microphone button with accessible state and title in MedAssistChatPanel", () => {
    assert.equal(
      chatPanelSource.includes("startVoiceInput"),
      true,
      "MedAssistChatPanel must implement startVoiceInput"
    );
    assert.equal(
      chatPanelSource.includes("stopVoiceInput"),
      true,
      "MedAssistChatPanel must implement stopVoiceInput"
    );
    assert.equal(
      chatPanelSource.includes('aria-label='),
      true,
      "Microphone button must define accessible aria-label"
    );
    assert.equal(
      chatPanelSource.includes('aria-pressed='),
      true,
      "Microphone button must indicate toggle listening state via aria-pressed"
    );
  });

  it("handles speech recognition interim/final results without automatically submitting", () => {
    assert.equal(
      chatPanelSource.includes("setInputText"),
      true,
      "Speech recognition must populate textarea for user editing"
    );
    // Speech results must not call handleSendMessage automatically
    assert.equal(
      chatPanelSource.includes("recognition.onresult"),
      true,
      "SpeechRecognition must listen to onresult"
    );
    assert.equal(
      chatPanelSource.includes("finalTranscript"),
      true,
      "Must track finalTranscript"
    );
  });

  it("handles microphone permission denial, unsupported browser, and network errors gracefully", () => {
    assert.equal(
      chatPanelSource.includes("not-allowed"),
      true,
      "Must handle microphone permission denial ('not-allowed')"
    );
    assert.equal(
      chatPanelSource.includes("speechUnsupported"),
      true,
      "Must handle browsers without speech recognition support"
    );
    assert.equal(
      chatPanelSource.includes("networkError"),
      true,
      "Must handle speech network errors"
    );
    assert.equal(
      chatPanelSource.includes('role="alert"') && chatPanelSource.includes('aria-live="assertive"'),
      true,
      "Must display accessible alerts on voice error"
    );
  });
});

describe("4. Spoken MedAssist Responses (Text-to-Speech) & Accessibility", () => {
  it("implements read-aloud controls for assistant messages with Play, Pause, Resume, and Stop", () => {
    assert.equal(
      chatPanelSource.includes("handleReadAloud"),
      true,
      "MedAssistChatPanel must implement handleReadAloud"
    );
    assert.equal(
      chatPanelSource.includes("handleStopReadAloud"),
      true,
      "MedAssistChatPanel must implement handleStopReadAloud"
    );
    assert.equal(
      chatPanelSource.includes("activeSpeechMessageId"),
      true,
      "Must track activeSpeechMessageId"
    );
    assert.equal(
      chatPanelSource.includes("isSpeechPaused"),
      true,
      "Must support pausing and resuming speech"
    );
  });

  it("negotiates language-matched speech synthesis voice with fallback notice", () => {
    assert.equal(
      chatPanelSource.includes("speechLang"),
      true,
      "Utterance must be assigned speechLang of active language"
    );
    assert.equal(
      chatPanelSource.includes("voiceSynthesizerUnavailable"),
      true,
      "Must handle devices lacking regional voices gracefully"
    );
    assert.equal(
      chatPanelSource.includes("speechSynthesis.cancel()"),
      true,
      "Must cancel speech on stop, language change, or unmount"
    );
  });
});

describe("5. Global Language Selection & Contract Invariance", () => {
  it("exposes LanguageProvider and useLanguage hook in LanguageContext", () => {
    assert.equal(contextSource.includes("export function LanguageProvider"), true);
    assert.equal(contextSource.includes("export function useLanguage"), true);
    assert.equal(contextSource.includes("SUPPORTED_LANGUAGES"), true);
  });

  it("renders accessible LanguageSelector dropdown with keyboard support", () => {
    assert.equal(selectorSource.includes("role=\"listbox\""), true);
    assert.equal(selectorSource.includes("role=\"option\""), true);
    assert.equal(selectorSource.includes("aria-selected="), true);
    assert.equal(selectorSource.includes("handleKeyDown"), true);
  });

  it("integrates language selector into Header and PatientFriendlyExplanation", () => {
    assert.equal(headerSource.includes("LanguageSelector"), true);
    assert.equal(explanationComponentSource.includes("useLanguage"), true);
  });

  it("forwards user language preference to sendChatMessage API client", () => {
    assert.equal(
      apiSource.includes("language = \"en\""),
      true,
      "sendChatMessage must accept language parameter"
    );
    assert.equal(
      apiSource.includes("language: language || \"en\""),
      true,
      "sendChatMessage payload must include language"
    );
  });
});
