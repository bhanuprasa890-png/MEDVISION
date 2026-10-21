/**
 * Frontend Unit & Regression Tests for Task 25
 * Tests Language-Aware Speech Synthesis (Zero Silent English Fallback),
 * Voice Selection & Locale Mapping, and Chest X-Ray Patient-Friendly Explanations
 * across all 18 pathologies in English, Tamil, Hindi, and Telugu.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  SPEECH_LOCALES,
  getSpeechLocale,
  findMatchingVoice,
  isVoiceAvailable,
  speakUtterance,
  stopSpeech,
  pauseSpeech,
  resumeSpeech,
  loadVoicesAsync,
  subscribeVoicesChanged,
} from "../src/utils/speechSynthesis.js";

import {
  CXR_PATHOLOGY_EXPLANATIONS,
  CXR_HEATMAP_EXPLANATIONS,
  CXR_SCORE_EXPLANATIONS,
  CXR_BELOW_THRESHOLD_EXPLANATIONS,
  CXR_EMERGENCY_WARNINGS,
  CXR_UI_STRINGS,
  getChestXrayFindingExplanation,
} from "../src/utils/chestXrayExplanations.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const cxrComponentSource = fs.readFileSync(
  path.join(__dirname, "../src/components/ChestXrayPatientExplanation.jsx"),
  "utf8"
);
const cxrResultCardSource = fs.readFileSync(
  path.join(__dirname, "../src/components/ChestXrayResultCard.jsx"),
  "utf8"
);
const retinaExplanationSource = fs.readFileSync(
  path.join(__dirname, "../src/components/PatientFriendlyExplanation.jsx"),
  "utf8"
);
const chatPanelSource = fs.readFileSync(
  path.join(__dirname, "../src/components/MedAssistChatPanel.jsx"),
  "utf8"
);

describe("1. Language-Aware Speech Synthesis & Locale Mapping", () => {
  it("maps each supported language code to its required speech locale", () => {
    assert.equal(getSpeechLocale("en"), "en-IN");
    assert.equal(getSpeechLocale("ta"), "ta-IN");
    assert.equal(getSpeechLocale("hi"), "hi-IN");
    assert.equal(getSpeechLocale("te"), "te-IN");
    assert.equal(getSpeechLocale("unknown"), "en-IN"); // Safe fallback
  });

  it("selects appropriate regional voices without false-positive matching", () => {
    const mockVoices = [
      { name: "Microsoft David - English (United States)", lang: "en-US" },
      { name: "Microsoft Heera - English (India)", lang: "en-IN" },
      { name: "Google தமிழ்", lang: "ta-IN" },
      { name: "Google हिन्दी", lang: "hi-IN" },
      { name: "Google తెలుగు", lang: "te-IN" },
      { name: "Microsoft Zira - English (United States)", lang: "en-US" },
    ];

    const taVoice = findMatchingVoice(mockVoices, "ta");
    assert.ok(taVoice);
    assert.equal(taVoice.lang, "ta-IN");

    const hiVoice = findMatchingVoice(mockVoices, "hi");
    assert.ok(hiVoice);
    assert.equal(hiVoice.lang, "hi-IN");

    const teVoice = findMatchingVoice(mockVoices, "te");
    assert.ok(teVoice);
    assert.equal(teVoice.lang, "te-IN");

    const enVoice = findMatchingVoice(mockVoices, "en");
    assert.ok(enVoice);
    assert.equal(enVoice.lang, "en-IN");
  });

  it("CRITICAL GUARD: Never matches English (India) voice for Tamil, Hindi, or Telugu", () => {
    // Only English voices exist (typical English Windows installation)
    const englishOnlyVoices = [
      { name: "Microsoft David - English (United States)", lang: "en-US" },
      { name: "Microsoft Heera - English (India)", lang: "en-IN" },
      { name: "Microsoft Ravi - English (India)", lang: "en-IN" },
    ];

    // Must NOT match 'Microsoft Heera - English (India)' merely because it contains 'India'
    const taMatch = findMatchingVoice(englishOnlyVoices, "ta");
    assert.equal(taMatch, null, "Tamil must NOT match an English (India) voice");

    const hiMatch = findMatchingVoice(englishOnlyVoices, "hi");
    assert.equal(hiMatch, null, "Hindi must NOT match an English (India) voice");

    const teMatch = findMatchingVoice(englishOnlyVoices, "te");
    assert.equal(teMatch, null, "Telugu must NOT match an English (India) voice");
  });

  it("returns null for empty or invalid voice lists", () => {
    assert.equal(findMatchingVoice([], "ta"), null);
    assert.equal(findMatchingVoice(null, "hi"), null);
  });
});

describe("2. Non-English Voice Availability & Zero Silent Fallback", () => {
  it("aborts speech synthesis and calls onVoiceUnavailable when non-English voice is absent", () => {
    let speakCalled = false;
    let cancelCalled = false;
    let unavailableCalled = false;

    // Mock window.speechSynthesis where only English voices exist
    const originalWindow = global.window;
    global.window = {
      speechSynthesis: {
        getVoices: () => [
          { name: "Microsoft David", lang: "en-US" },
          { name: "Microsoft Heera", lang: "en-IN" },
        ],
        cancel: () => {
          cancelCalled = true;
        },
        speak: () => {
          speakCalled = true;
        },
      },
    };
    global.SpeechSynthesisUtterance = function (text) {
      this.text = text;
    };

    try {
      const result = speakUtterance({
        text: "வணக்கம், இது ஒரு மருத்துவ தகவல்.",
        langCode: "ta",
        onVoiceUnavailable: (details) => {
          unavailableCalled = true;
          assert.equal(details.langCode, "ta");
          assert.equal(details.locale, "ta-IN");
        },
      });

      assert.equal(result.ok, false);
      assert.equal(result.reason, "VOICE_UNAVAILABLE");
      assert.equal(unavailableCalled, true, "onVoiceUnavailable must be triggered");
      assert.equal(speakCalled, false, "speechSynthesis.speak() must NEVER be called without a matching voice!");
      assert.equal(cancelCalled, true, "Existing speech must be cancelled first");
    } finally {
      global.window = originalWindow;
    }
  });

  it("speaks successfully with matching voice and assigned locale when voice is available", () => {
    let spokenUtterance = null;

    const originalWindow = global.window;
    global.window = {
      speechSynthesis: {
        getVoices: () => [
          { name: "Google தமிழ்", lang: "ta-IN" },
        ],
        cancel: () => {},
        speak: (utt) => {
          spokenUtterance = utt;
        },
      },
    };
    global.SpeechSynthesisUtterance = function (text) {
      this.text = text;
      this.lang = "";
      this.voice = null;
      this.rate = 1.0;
    };

    try {
      const result = speakUtterance({
        text: "வணக்கம், இது ஒரு மருத்துவ தகவல்.",
        langCode: "ta",
      });

      assert.equal(result.ok, true);
      assert.ok(spokenUtterance);
      assert.equal(spokenUtterance.lang, "ta-IN");
      assert.equal(spokenUtterance.voice.name, "Google தமிழ்");
    } finally {
      global.window = originalWindow;
    }
  });

  it("verifies playback controls: stopSpeech, pauseSpeech, resumeSpeech", () => {
    let paused = false;
    let resumed = false;
    let cancelled = false;

    const originalWindow = global.window;
    global.window = {
      speechSynthesis: {
        pause: () => {
          paused = true;
        },
        resume: () => {
          resumed = true;
        },
        cancel: () => {
          cancelled = true;
        },
      },
    };

    try {
      pauseSpeech();
      assert.equal(paused, true);
      resumeSpeech();
      assert.equal(resumed, true);
      stopSpeech();
      assert.equal(cancelled, true);
    } finally {
      global.window = originalWindow;
    }
  });

  it("handles delayed voice loading via loadVoicesAsync with voiceschanged event", async () => {
    let handlerRef = null;
    const originalWindow = global.window;

    let calls = 0;
    global.window = {
      speechSynthesis: {
        getVoices: () => {
          calls++;
          if (calls === 1) return []; // Initially empty
          return [{ name: "Delayed Voice", lang: "hi-IN" }];
        },
        addEventListener: (event, handler) => {
          if (event === "voiceschanged") {
            handlerRef = handler;
          }
        },
        removeEventListener: () => {},
      },
    };

    try {
      const loadPromise = loadVoicesAsync(500);
      // Simulate browser firing voiceschanged
      if (handlerRef) {
        handlerRef();
      }
      const loadedVoices = await loadPromise;
      assert.ok(loadedVoices.length > 0);
      assert.equal(loadedVoices[0].lang, "hi-IN");
    } finally {
      global.window = originalWindow;
    }
  });
});

describe("3. Chest X-Ray Explanations: 18 Pathologies Across 4 Languages", () => {
  const expectedPathologies = [
    "Atelectasis",
    "Consolidation",
    "Infiltration",
    "Pneumothorax",
    "Edema",
    "Emphysema",
    "Fibrosis",
    "Effusion",
    "Pneumonia",
    "Pleural_Thickening",
    "Cardiomegaly",
    "Nodule",
    "Mass",
    "Hernia",
    "Lung Lesion",
    "Fracture",
    "Lung Opacity",
    "Enlarged Cardiomediastinum",
  ];

  it("contains complete entries for all 18 TorchXRayVision DenseNet-121 pathologies", () => {
    for (const pathology of expectedPathologies) {
      assert.ok(
        CXR_PATHOLOGY_EXPLANATIONS[pathology],
        `CXR_PATHOLOGY_EXPLANATIONS must contain entry for '${pathology}'`
      );
    }
  });

  it("provides comprehensive multilingual content in en, ta, hi, te for each pathology", () => {
    for (const pathology of expectedPathologies) {
      const entry = CXR_PATHOLOGY_EXPLANATIONS[pathology];
      for (const lang of ["en", "ta", "hi", "te"]) {
        const langData = entry[lang];
        assert.ok(langData, `Pathology '${pathology}' missing language '${lang}'`);
        assert.ok(langData.title, `${pathology}.${lang} missing title`);
        assert.ok(langData.badge, `${pathology}.${lang} missing badge`);
        assert.ok(langData.whatItMeans, `${pathology}.${lang} missing whatItMeans`);
        assert.ok(langData.whatModelSaw, `${pathology}.${lang} missing whatModelSaw`);
        assert.ok(langData.analogy, `${pathology}.${lang} missing analogy`);
        assert.ok(Array.isArray(langData.nextSteps) && langData.nextSteps.length > 0, `${pathology}.${lang} missing nextSteps`);
        assert.ok(langData.careCategory, `${pathology}.${lang} missing careCategory`);
      }
    }
  });

  it("verifies authentic native script for non-English translations", () => {
    for (const pathology of expectedPathologies) {
      const entry = CXR_PATHOLOGY_EXPLANATIONS[pathology];
      // Tamil: \u0B80-\u0BFF
      assert.equal(/[\u0B80-\u0BFF]/.test(entry.ta.title), true, `${pathology}.ta title must contain Tamil script`);
      // Hindi: \u0900-\u097F
      assert.equal(/[\u0900-\u097F]/.test(entry.hi.title), true, `${pathology}.hi title must contain Devanagari script`);
      // Telugu: \u0C00-\u0C7F
      assert.equal(/[\u0C00-\u0C7F]/.test(entry.te.title), true, `${pathology}.te title must contain Telugu script`);
    }
  });

  it("resolves both underscore and space label variations seamlessly", () => {
    const withUnderscore = getChestXrayFindingExplanation("Pleural_Thickening", "en");
    const withSpace = getChestXrayFindingExplanation("Pleural Thickening", "en");
    assert.equal(withUnderscore.title, withSpace.title);

    const lesionWithSpace = getChestXrayFindingExplanation("Lung Lesion", "ta");
    const lesionWithUnderscore = getChestXrayFindingExplanation("Lung_Lesion", "ta");
    assert.equal(lesionWithSpace.title, lesionWithUnderscore.title);

    // Fallback for unknown pathology
    const fallback = getChestXrayFindingExplanation("NonExistentFinding", "en");
    assert.ok(fallback.title);
  });
});

describe("4. Non-Diagnostic Guardrails, Score Interpretation & Heatmap Limits", () => {
  it("explains uncalibrated sigmoid scores without claiming disease probability in all 4 languages", () => {
    for (const lang of ["en", "ta", "hi", "te"]) {
      const scoreData = CXR_SCORE_EXPLANATIONS[lang];
      assert.ok(scoreData, `CXR_SCORE_EXPLANATIONS missing language '${lang}'`);
      assert.ok(scoreData.scoreMeaning);
      assert.ok(scoreData.thresholdMeaning);
      assert.ok(scoreData.cautiousInterpretation);

      // Verify English explicitly mentions uncalibrated / research prototype
      if (lang === "en") {
        assert.equal(scoreData.scoreMeaning.toLowerCase().includes("uncalibrated"), true);
        assert.equal(scoreData.scoreMeaning.toLowerCase().includes("not an 80% or 62%"), true);
      }
    }
  });

  it("handles below-threshold results without asserting complete absence of disease", () => {
    for (const lang of ["en", "ta", "hi", "te"]) {
      const belowData = CXR_BELOW_THRESHOLD_EXPLANATIONS[lang];
      assert.ok(belowData);
      assert.ok(belowData.title);
      assert.ok(belowData.summary);
      assert.ok(belowData.caution);

      if (lang === "en") {
        assert.equal(belowData.caution.toLowerCase().includes("does not prove your lungs are completely healthy"), true);
      }
    }
  });

  it("strictly enforces what Grad-CAM visual attention CANNOT prove in all 4 languages", () => {
    for (const lang of ["en", "ta", "hi", "te"]) {
      const heatmapData = CXR_HEATMAP_EXPLANATIONS[lang];
      assert.ok(heatmapData);
      assert.ok(heatmapData.title);
      assert.ok(heatmapData.whatItRepresentsText);
      assert.ok(heatmapData.colorRed);
      assert.ok(heatmapData.colorYellowGreen);
      assert.ok(heatmapData.colorBlue);
      assert.ok(Array.isArray(heatmapData.limits) && heatmapData.limits.length >= 4);
      assert.ok(heatmapData.doctorRoleText);
    }
  });

  it("provides emergency red-flag symptoms in all 4 languages", () => {
    for (const lang of ["en", "ta", "hi", "te"]) {
      const emerg = CXR_EMERGENCY_WARNINGS[lang];
      assert.ok(emerg);
      assert.ok(emerg.title);
      assert.ok(emerg.intro);
      assert.ok(Array.isArray(emerg.symptoms) && emerg.symptoms.length >= 4);
      assert.ok(emerg.instruction);
    }
  });

  it("provides complete UI strings for CXR explanation component across all 4 languages", () => {
    for (const lang of ["en", "ta", "hi", "te"]) {
      const ui = CXR_UI_STRINGS[lang];
      assert.ok(ui);
      assert.ok(ui.sectionHeading);
      assert.ok(ui.readAloud);
      assert.ok(ui.pauseAudio);
      assert.ok(ui.resumeAudio);
      assert.ok(ui.stopAudio);
      assert.ok(ui.audioPlaying);
      assert.ok(ui.audioPaused);
      assert.ok(ui.audioFinished);
      assert.ok(ui.audioUnavailable);
      assert.ok(ui.voiceUnavailable);
    }
  });
});

describe("5. Component Integration & Accessibility Contracts", () => {
  it("ChestXrayPatientExplanation component exists and provides accessible controls", () => {
    assert.equal(
      cxrComponentSource.includes("export function ChestXrayPatientExplanation"),
      true,
      "Component must export ChestXrayPatientExplanation"
    );
    assert.equal(
      cxrComponentSource.includes("aria-labelledby=\"understand-cxr-title\""),
      true,
      "Section must declare accessible label"
    );
    assert.equal(
      cxrComponentSource.includes("role=\"group\""),
      true,
      "Language toolbar must have role=group"
    );
    assert.equal(
      cxrComponentSource.includes("aria-pressed="),
      true,
      "Language buttons must declare aria-pressed state"
    );
    assert.equal(
      cxrComponentSource.includes("role=\"status\""),
      true,
      "Live region must be present for audio feedback"
    );
    assert.equal(
      cxrComponentSource.includes("aria-live=\"polite\""),
      true,
      "Live region must be polite"
    );
  });

  it("ChestXrayResultCard mounts ChestXrayPatientExplanation component", () => {
    assert.equal(
      cxrResultCardSource.includes("ChestXrayPatientExplanation"),
      true,
      "ChestXrayResultCard must import and render ChestXrayPatientExplanation"
    );
    assert.equal(
      cxrResultCardSource.includes("<ChestXrayPatientExplanation"),
      true,
      "ChestXrayResultCard JSX must contain <ChestXrayPatientExplanation"
    );
  });

  it("PatientFriendlyExplanation uses shared speech synthesis utility", () => {
    assert.equal(
      retinaExplanationSource.includes("speakUtterance"),
      true,
      "Retina explanation must use shared speakUtterance"
    );
    assert.equal(
      retinaExplanationSource.includes("stopSpeech"),
      true,
      "Retina explanation must use shared stopSpeech"
    );
  });

  it("MedAssistChatPanel uses shared speech synthesis utility with voice guard", () => {
    assert.equal(
      chatPanelSource.includes("speakUtterance"),
      true,
      "MedAssistChatPanel must use shared speakUtterance"
    );
    assert.equal(
      chatPanelSource.includes("stopSpeech"),
      true,
      "MedAssistChatPanel must use shared stopSpeech"
    );
  });
});

describe("6. Task 25.1 Targeted Multilingual Speech Verification", () => {
  it("matches native Indic script names (தமிழ், हिन्दी, తెలుగు) when metadata is non-conflicting", () => {
    const mockNativeVoices = [
      { name: "Google தமிழ்", lang: "" },
      { name: "Google हिन्दी", lang: "" },
      { name: "Google తెలుగు", lang: "" },
      { name: "Microsoft Valluvar", lang: "ta" },
      { name: "Microsoft Kalpana", lang: "hi" },
      { name: "Microsoft Chitra", lang: "te" },
    ];

    const taMatch = findMatchingVoice(mockNativeVoices, "ta");
    assert.ok(taMatch);
    assert.equal(taMatch.name.includes("தமிழ்") || taMatch.name.includes("Valluvar"), true);

    const hiMatch = findMatchingVoice(mockNativeVoices, "hi");
    assert.ok(hiMatch);
    assert.equal(hiMatch.name.includes("हिन्दी") || hiMatch.name.includes("Kalpana"), true);

    const teMatch = findMatchingVoice(mockNativeVoices, "te");
    assert.ok(teMatch);
    assert.equal(teMatch.name.includes("తెలుగు") || teMatch.name.includes("Chitra"), true);
  });

  it("proves that subscribing to voiceschanged dynamically tracks voice updates", () => {
    let listener = null;
    let unsubscribeCalled = false;
    const originalWindow = global.window;

    global.window = {
      speechSynthesis: {
        getVoices: () => [{ name: "Async Voice", lang: "te-IN" }],
        addEventListener: (event, cb) => {
          if (event === "voiceschanged") listener = cb;
        },
        removeEventListener: (event, cb) => {
          if (event === "voiceschanged") unsubscribeCalled = true;
        },
      },
    };

    try {
      let receivedVoices = null;
      const unsubscribe = subscribeVoicesChanged((v) => {
        receivedVoices = v;
      });

      assert.ok(listener, "voiceschanged listener must be registered");
      listener();
      assert.ok(receivedVoices);
      assert.equal(receivedVoices[0].lang, "te-IN");

      unsubscribe();
      assert.equal(unsubscribeCalled, true, "unsubscribe must remove the event listener");
    } finally {
      global.window = originalWindow;
    }
  });

  it("filters out normal cancellation and interruption events from triggering speech errors", () => {
    let errorTriggered = false;
    let spokenUtterance = null;
    const originalWindow = global.window;

    global.window = {
      speechSynthesis: {
        getVoices: () => [{ name: "Microsoft Heera", lang: "en-IN" }],
        cancel: () => {},
        speak: (utt) => {
          spokenUtterance = utt;
        },
      },
    };
    global.SpeechSynthesisUtterance = function (text) {
      this.text = text;
      this.lang = "";
    };

    try {
      speakUtterance({
        text: "Testing speech cancellation",
        langCode: "en",
        onError: () => {
          errorTriggered = true;
        },
      });

      assert.ok(spokenUtterance);
      // Simulate browser firing canceled event upon window.speechSynthesis.cancel()
      spokenUtterance.onerror({ error: "canceled" });
      assert.equal(errorTriggered, false, "canceled error must NOT trigger onError callback");

      spokenUtterance.onerror({ error: "interrupted" });
      assert.equal(errorTriggered, false, "interrupted error must NOT trigger onError callback");

      // Genuine error should still trigger onError
      spokenUtterance.onerror({ error: "audio-busy" });
      assert.equal(errorTriggered, true, "genuine errors must trigger onError callback");
    } finally {
      global.window = originalWindow;
    }
  });

  it("verifies both RetinaGuard and CXR components subscribe to voiceschanged and async voice loading", () => {
    // Both components must import and wire subscribeVoicesChanged & loadVoicesAsync
    const cxrSource = fs.readFileSync(
      path.join(__dirname, "../src/components/ChestXrayPatientExplanation.jsx"),
      "utf8"
    );
    const retinaSource = fs.readFileSync(
      path.join(__dirname, "../src/components/PatientFriendlyExplanation.jsx"),
      "utf8"
    );

    assert.equal(
      cxrSource.includes("subscribeVoicesChanged"),
      true,
      "ChestXrayPatientExplanation must import and use subscribeVoicesChanged"
    );
    assert.equal(
      cxrSource.includes("loadVoicesAsync"),
      true,
      "ChestXrayPatientExplanation must import and use loadVoicesAsync"
    );

    assert.equal(
      retinaSource.includes("subscribeVoicesChanged"),
      true,
      "PatientFriendlyExplanation must import and use subscribeVoicesChanged"
    );
    assert.equal(
      retinaSource.includes("loadVoicesAsync"),
      true,
      "PatientFriendlyExplanation must import and use loadVoicesAsync"
    );
  });
});

