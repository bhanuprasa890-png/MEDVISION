/**
 * Frontend Unit & Integration Tests for Task 24:
 * Chest X-Ray Pipeline, Grad-CAM Explainability, and Multilingual Support.
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

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const pageSource = fs.readFileSync(
  path.join(__dirname, "../src/pages/ChestXrayAnalysisPage.jsx"),
  "utf8"
);
const cardSource = fs.readFileSync(
  path.join(__dirname, "../src/components/ChestXrayResultCard.jsx"),
  "utf8"
);
const apiSource = fs.readFileSync(
  path.join(__dirname, "../src/services/api.js"),
  "utf8"
);

describe("1. Chest X-Ray API Integration in api.js", () => {
  it("declares predictChestXray and getChestXrayModelStatus functions", () => {
    assert.match(apiSource, /export\s+async\s+function\s+predictChestXray/);
    assert.match(apiSource, /export\s+async\s+function\s+getChestXrayModelStatus/);
  });

  it("targets authentic API endpoint routes for predict and model-status", () => {
    assert.match(apiSource, /\/api\/v1\/chest-xray\/predict\?include_gradcam=/);
    assert.match(apiSource, /\/api\/v1\/chest-xray\/model-status/);
  });
});

describe("2. Chest X-Ray Multilingual Translation Catalog", () => {
  const languages = ["en", "ta", "hi", "te"];
  const requiredKeys = [
    "title",
    "subtitle",
    "badgeActive",
    "topFinding",
    "topScore",
    "allPathologies",
    "findingsAboveThreshold",
    "noneDetected",
    "explainability",
    "disclaimer",
    "startAnalysis",
    "reset",
  ];

  it("defines complete chestXray translation catalog for all 4 languages", () => {
    assert.ok(TRANSLATIONS.chestXray, "chestXray section must exist in TRANSLATIONS");
    for (const lang of languages) {
      assert.ok(TRANSLATIONS.chestXray[lang], `chestXray.${lang} must exist`);
      for (const key of requiredKeys) {
        const val = TRANSLATIONS.chestXray[lang][key];
        assert.ok(
          val && typeof val === "string" && val.length > 0,
          `chestXray.${lang}.${key} must be a non-empty string`
        );
      }
    }
  });

  it("verifies authentic native scripts for non-English languages in CXR titles", () => {
    const tamilTitle = getTranslation("chestXray", "title", "ta");
    const hindiTitle = getTranslation("chestXray", "title", "hi");
    const teluguTitle = getTranslation("chestXray", "title", "te");

    assert.ok(/[\u0B80-\u0BFF]/.test(tamilTitle), "Tamil title must contain authentic Tamil script");
    assert.ok(/[\u0900-\u097F]/.test(hindiTitle), "Hindi title must contain authentic Devanagari script");
    assert.ok(/[\u0C00-\u0C7F]/.test(teluguTitle), "Telugu title must contain authentic Telugu script");
  });

  it("verifies all 18 standard thoracic pathologies have localized names", () => {
    const standard18 = [
      "Atelectasis", "Consolidation", "Infiltration", "Pneumothorax",
      "Edema", "Emphysema", "Fibrosis", "Effusion",
      "Pneumonia", "Pleural_Thickening", "Cardiomegaly", "Nodule",
      "Mass", "Hernia", "Lung Lesion", "Fracture",
      "Lung Opacity", "Enlarged Cardiomediastinum"
    ];

    for (const lang of languages) {
      const names = TRANSLATIONS.chestXray[lang].pathologyNames;
      assert.ok(names, `pathologyNames must exist for language ${lang}`);
      for (const pathName of standard18) {
        assert.ok(names[pathName], `pathologyName '${pathName}' must be defined for ${lang}`);
      }
    }
  });
});

describe("3. ChestXrayAnalysisPage Component Architecture", () => {
  it("imports real prediction API and model status query", () => {
    assert.match(pageSource, /predictChestXray/);
    assert.match(pageSource, /getChestXrayModelStatus/);
    assert.match(pageSource, /ChestXrayResultCard/);
    assert.match(pageSource, /useLanguage/);
  });

  it("connects analysis initiation to predictChestXray", () => {
    assert.match(pageSource, /uploadAndAnalyze\(predictChestXray\)/);
  });

  it("renders dynamic badge reflecting model readiness", () => {
    assert.match(pageSource, /badgeActive/);
    assert.match(pageSource, /badgeUnavailable/);
  });
});

describe("4. ChestXrayResultCard Component Presentation & Accessibility", () => {
  it("uses useLanguage context and translation lookup", () => {
    assert.match(cardSource, /useLanguage/);
    assert.match(cardSource, /getTranslation/);
  });

  it("implements tabbed visual modes for Grad-CAM overlay, raw heatmap, and original radiograph", () => {
    assert.match(cardSource, /role="tablist"/);
    assert.match(cardSource, /id="tab-cxr-overlay"/);
    assert.match(cardSource, /id="tab-cxr-raw"/);
    assert.match(cardSource, /id="tab-cxr-original"/);
    assert.match(cardSource, /role="tabpanel"/);
  });

  it("implements accessible ARIA progressbars for pathology scores", () => {
    assert.match(cardSource, /role="progressbar"/);
    assert.match(cardSource, /aria-valuenow=/);
    assert.match(cardSource, /aria-valuemin=/);
    assert.match(cardSource, /aria-valuemax=/);
  });

  it("prominently presents non-diagnostic research disclaimer and reset control", () => {
    assert.match(cardSource, /t\("disclaimer"\)/);
    assert.match(cardSource, /calibration_notice/);
    assert.match(TRANSLATIONS.chestXray.en.disclaimer, /RESEARCH PROTOTYPE ONLY/);
    assert.match(cardSource, /onReset/);
  });
});
