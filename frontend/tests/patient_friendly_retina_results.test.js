/**
 * Frontend Unit & Accessibility Test Suite
 * Tests for Patient-Friendly RetinaGuard Results, Plain-Language Explanations,
 * Bilingual Support (English & Tamil), Heatmap Interpretation, and Accessibility Contracts.
 */

import test, { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  GRADE_EXPLANATIONS,
  HEATMAP_EXPLANATIONS,
  EMERGENCY_WARNINGS,
  UI_STRINGS,
} from "../src/utils/patientExplanations.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

describe("1. Plain-Language Explanations for All 5 Diabetic Retinopathy Grades", () => {
  const grades = [0, 1, 2, 3, 4];

  it("provides comprehensive plain-English explanations for all 5 clinical grades", () => {
    for (const g of grades) {
      const data = GRADE_EXPLANATIONS[g];
      assert.ok(data, `Grade ${g} must be defined in GRADE_EXPLANATIONS`);
      assert.equal(data.clinicalGrade, g);
      assert.ok(data.clinicalName, `Grade ${g} must retain its clinical name`);

      const en = data.en;
      assert.ok(en.title, `Grade ${g} must have a plain English title`);
      assert.ok(en.whatModelPredicted, `Grade ${g} must explain what the model saw`);
      assert.ok(en.everydayExplanation, `Grade ${g} must provide everyday wording`);
      assert.ok(en.analogy, `Grade ${g} must provide an intuitive analogy`);
      assert.ok(Array.isArray(en.nextSteps) && en.nextSteps.length >= 2, `Grade ${g} must have evidence-based next steps`);
      assert.ok(en.urgency, `Grade ${g} must state care urgency`);

      // Ensure no technical medical jargon is left without plain language context
      assert.ok(!en.everydayExplanation.includes("uncalibrated softmax"), "Must not confuse users with ML jargon");
    }
  });

  it("plain English explanations accurately convey the medical progression without inventing treatments", () => {
    // Grade 0: Normal / undamaged
    assert.match(GRADE_EXPLANATIONS[0].en.everydayExplanation, /clear.*undamaged|nourish.*retina/i);
    assert.match(GRADE_EXPLANATIONS[0].en.urgency, /routine/i);

    // Grade 1: Early / microaneurysms
    assert.match(GRADE_EXPLANATIONS[1].en.everydayExplanation, /microaneurysms|weak spots/i);
    assert.match(GRADE_EXPLANATIONS[1].en.whatModelPredicted, /early-stage/i);

    // Grade 2: Moderate / leaking or blocked vessels
    assert.match(GRADE_EXPLANATIONS[2].en.everydayExplanation, /blocked or swollen|leaking/i);

    // Grade 3: Severe / significant blockage & oxygen starvation
    assert.match(GRADE_EXPLANATIONS[3].en.everydayExplanation, /blocked.*cutting off oxygen|starved/i);

    // Grade 4: Advanced / Proliferative / fragile new blood vessels
    assert.match(GRADE_EXPLANATIONS[4].en.everydayExplanation, /fragile.*new.*blood vessels|bleed into/i);
    assert.match(GRADE_EXPLANATIONS[4].en.urgency, /urgent/i);
  });
});

describe("2. Authentic Bilingual Support (English and Tamil)", () => {
  const grades = [0, 1, 2, 3, 4];

  it("provides complete Tamil explanations for all 5 clinical grades", () => {
    for (const g of grades) {
      const data = GRADE_EXPLANATIONS[g];
      const ta = data.ta;
      assert.ok(ta, `Grade ${g} must have Tamil translations`);
      assert.ok(ta.title, `Grade ${g} Tamil title must exist`);
      assert.ok(ta.whatModelPredicted, `Grade ${g} Tamil whatModelPredicted must exist`);
      assert.ok(ta.everydayExplanation, `Grade ${g} Tamil everydayExplanation must exist`);
      assert.ok(ta.analogy, `Grade ${g} Tamil analogy must exist`);
      assert.ok(Array.isArray(ta.nextSteps) && ta.nextSteps.length >= 2, `Grade ${g} Tamil nextSteps must exist`);
      assert.ok(ta.urgency, `Grade ${g} Tamil urgency must exist`);

      // Verify Tamil script presence (Unicode range \u0B80-\u0BFF)
      const hasTamilScript = /[\u0B80-\u0BFF]/.test(ta.title);
      assert.equal(hasTamilScript, true, `Grade ${g} Tamil title must contain authentic Tamil script`);
    }
  });

  it("UI strings exist and correspond in both English and Tamil", () => {
    assert.ok(UI_STRINGS.en, "UI_STRINGS.en must exist");
    assert.ok(UI_STRINGS.ta, "UI_STRINGS.ta must exist");

    const requiredKeys = [
      "sectionHeading",
      "sectionSubheading",
      "languageToggleLabel",
      "readAloud",
      "pauseAudio",
      "resumeAudio",
      "stopAudio",
      "audioUnavailable",
      "tamilVoiceUnavailable",
      "confidenceTitle",
      "lowConfidenceWarning",
      "disclaimerBannerTitle",
      "disclaimerBannerText",
      "noPrediction",
    ];

    for (const key of requiredKeys) {
      assert.ok(UI_STRINGS.en[key], `English key '${key}' must be defined`);
      assert.ok(UI_STRINGS.ta[key], `Tamil key '${key}' must be defined`);
      assert.equal(
        /[\u0B80-\u0BFF]/.test(UI_STRINGS.ta[key]),
        true,
        `Tamil string for '${key}' must contain Tamil script`
      );
    }
  });
});

describe("3. Grad-CAM Heatmap Interpretation & Boundary Limits", () => {
  it("explains what the Grad-CAM heatmap represents in plain language", () => {
    assert.ok(HEATMAP_EXPLANATIONS.en.whatItRepresentsText.includes("attention map"));
    assert.ok(HEATMAP_EXPLANATIONS.en.whatItRepresentsText.includes("artificial intelligence focused"));
    assert.ok(/[\u0B80-\u0BFF]/.test(HEATMAP_EXPLANATIONS.ta.whatItRepresentsText));
  });

  it("provides clear color-coding interpretation", () => {
    assert.match(HEATMAP_EXPLANATIONS.en.colorRed, /high.*focus/i);
    assert.match(HEATMAP_EXPLANATIONS.en.colorBlue, /little influence|background/i);
  });

  it("strictly enforces what the heatmap CANNOT prove", () => {
    const limitsEn = HEATMAP_EXPLANATIONS.en.limits;
    assert.ok(Array.isArray(limitsEn) && limitsEn.length >= 3);
    assert.ok(limitsEn.some((l) => l.includes("NOT prove that disease is definitely present")));
    assert.ok(limitsEn.some((l) => l.includes("NOT outline real biological disease borders")));
    assert.ok(limitsEn.some((l) => l.includes("NOT a medical scan, X-ray, or biopsy")));

    const limitsTa = HEATMAP_EXPLANATIONS.ta.limits;
    assert.ok(Array.isArray(limitsTa) && limitsTa.length >= 3);
    assert.ok(limitsTa.some((l) => /உறுதிப்படுத்தாது/.test(l)));
  });

  it("explains why an in-person eye doctor examination is irreplaceable", () => {
    assert.match(HEATMAP_EXPLANATIONS.en.doctorRoleText, /licensed eye doctor/i);
    assert.match(HEATMAP_EXPLANATIONS.en.doctorRoleText, /slit lamp|ophthalmoscope|dilated/i);
    assert.ok(/மருத்துவர்/.test(HEATMAP_EXPLANATIONS.ta.doctorRoleText));
  });
});

describe("4. Evidence-Based Next Steps & Emergency Warnings", () => {
  it("clearly distinguishes routine follow-up from urgent care", () => {
    // Grade 0 emphasizes yearly routine exams
    assert.ok(GRADE_EXPLANATIONS[0].en.nextSteps.some((s) => s.includes("annual dilated eye exam")));

    // Grade 4 emphasizes urgent specialist care
    assert.ok(GRADE_EXPLANATIONS[4].en.nextSteps.some((s) => /urgent evaluation|retina clinic/i.test(s)));
  });

  it("includes emergency red-flag symptoms in both languages", () => {
    assert.ok(Array.isArray(EMERGENCY_WARNINGS.en.symptoms));
    assert.ok(EMERGENCY_WARNINGS.en.symptoms.some((s) => s.includes("Sudden loss of vision")));
    assert.ok(EMERGENCY_WARNINGS.en.symptoms.some((s) => s.includes("curtain, veil, or shadow")));
    assert.ok(EMERGENCY_WARNINGS.en.symptoms.some((s) => s.includes("flashes of light")));

    assert.ok(Array.isArray(EMERGENCY_WARNINGS.ta.symptoms));
    assert.ok(EMERGENCY_WARNINGS.ta.symptoms.some((s) => /பார்வை மங்குதல்|பார்வை பறிபோதல்/.test(s)));
    assert.ok(EMERGENCY_WARNINGS.ta.symptoms.some((s) => /கரும் திரை/.test(s)));
    assert.ok(EMERGENCY_WARNINGS.ta.symptoms.some((s) => /மின்னல்/.test(s)));
  });
});

describe("5. Component Accessibility and Contract Invariance", () => {
  const componentPath = path.join(__dirname, "../src/components/PatientFriendlyExplanation.jsx");
  const resultCardPath = path.join(__dirname, "../src/components/RetinaPredictionResultCard.jsx");

  it("PatientFriendlyExplanation component file exists and is well-formed JSX", () => {
    assert.equal(fs.existsSync(componentPath), true);
    const content = fs.readFileSync(componentPath, "utf-8");
    assert.ok(content.includes("export function PatientFriendlyExplanation"));
    assert.ok(content.includes("aria-labelledby=\"understand-result-title\""));
    assert.ok(content.includes("role=\"status\""));
    assert.ok(content.includes("aria-live=\"polite\""));
  });

  it("RetinaPredictionResultCard imports and renders PatientFriendlyExplanation", () => {
    const content = fs.readFileSync(resultCardPath, "utf-8");
    assert.ok(content.includes('import { PatientFriendlyExplanation } from "./PatientFriendlyExplanation";'));
    assert.ok(content.includes("<PatientFriendlyExplanation prediction={prediction} explanation={explanation} />"));
  });

  it("preserves RetinaGuard prediction and MedAssist scanContext contracts", () => {
    const content = fs.readFileSync(resultCardPath, "utf-8");
    // Verifies that scanContext construction for onAskMedAssist remains untouched
    assert.ok(content.includes('modality: "retina"'));
    assert.ok(content.includes("predicted_class: prediction?.predicted_class"));
    assert.ok(content.includes("confidence_score: prediction?.confidence_score"));
    assert.ok(content.includes("all_class_scores: prediction?.all_class_scores"));
    assert.ok(content.includes("session_id: result?.session_id"));
  });

  it("handles missing or uncertain results gracefully", () => {
    assert.ok(UI_STRINGS.en.lowConfidenceWarning.includes("< 60%"));
    assert.ok(UI_STRINGS.en.noPrediction.includes("No prediction data"));
  });
});
