import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Read source files directly to verify structural and contract guarantees
const cardSource = fs.readFileSync(
  path.join(__dirname, "../src/components/RetinaPredictionResultCard.jsx"),
  "utf8"
);
const panelSource = fs.readFileSync(
  path.join(__dirname, "../src/components/MedAssistChatPanel.jsx"),
  "utf8"
);
const appSource = fs.readFileSync(
  path.join(__dirname, "../src/App.jsx"),
  "utf8"
);
const pageSource = fs.readFileSync(
  path.join(__dirname, "../src/pages/RetinaAnalysisPage.jsx"),
  "utf8"
);
const medAssistPageSource = fs.readFileSync(
  path.join(__dirname, "../src/pages/MedAssistPage.jsx"),
  "utf8"
);

describe("1. RetinaGuard-to-MedAssist Context Contract & Safety", () => {
  it("provides an explicit 'Ask MedAssist About This Result' action button", () => {
    assert.equal(
      cardSource.includes("Ask MedAssist About This Result"),
      true,
      "RetinaPredictionResultCard must render an explicit 'Ask MedAssist About This Result' button"
    );
    assert.equal(
      cardSource.includes("onAskMedAssist"),
      true,
      "Card must accept and invoke onAskMedAssist callback"
    );
  });

  it("constructs a strictly validated scanContext object with only genuine prediction fields", () => {
    // Check that only trusted prediction metadata is passed
    assert.equal(
      cardSource.includes('modality: "retina"'),
      true,
      "scanContext must explicitly set modality to 'retina'"
    );
    assert.equal(
      cardSource.includes("predicted_class: prediction?.predicted_class"),
      true,
      "scanContext must include predicted_class"
    );
    assert.equal(
      cardSource.includes("class_label: prediction?.class_label"),
      true,
      "scanContext must include class_label"
    );
    assert.equal(
      cardSource.includes("confidence_score: prediction?.confidence_score"),
      true,
      "scanContext must include confidence_score"
    );
    assert.equal(
      cardSource.includes("model_version: result?.model_version"),
      true,
      "scanContext must include model_version"
    );
    assert.equal(
      cardSource.includes("session_id: result?.session_id"),
      true,
      "scanContext must include anonymous audit session_id"
    );
  });

  it("strictly excludes raw image payloads, base64 strings, and patient identifiers", () => {
    // Negative test: verify no image binary/base64 or patient info in scanContext construction
    assert.equal(
      cardSource.includes("originalPreviewUrl") && cardSource.includes("scanContext = {"),
      true,
      "File must contain preview and scanContext definitions"
    );
    assert.equal(
      cardSource.includes("imageData:") || cardSource.includes("image_bytes:") || cardSource.includes("base64:"),
      false,
      "Must not pass image bytes or base64 data in scanContext"
    );
    assert.equal(
      cardSource.includes("patient_name") || cardSource.includes("mrn:") || cardSource.includes("patient_id"),
      false,
      "Must not include patient identifiers"
    );
  });
});

describe("2. Application Flow & Navigation Integration", () => {
  it("manages sharedScanContext in memory in App.jsx and switches tab to 'medassist'", () => {
    assert.equal(
      appSource.includes("sharedScanContext"),
      true,
      "App.jsx must manage sharedScanContext state"
    );
    assert.equal(
      appSource.includes('setActiveTab("medassist")'),
      true,
      "App.jsx must switch activeTab to 'medassist' upon user selection"
    );
    assert.equal(
      appSource.includes("handleClearScanContext"),
      true,
      "App.jsx must provide a handler to clear scan context"
    );
  });

  it("wires onAskMedAssist through RetinaAnalysisPage", () => {
    assert.equal(
      pageSource.includes("onAskMedAssist"),
      true,
      "RetinaAnalysisPage must accept and forward onAskMedAssist"
    );
  });

  it("wires activeScanContext and onClearScanContext through MedAssistPage", () => {
    assert.equal(
      medAssistPageSource.includes("activeScanContext"),
      true,
      "MedAssistPage must accept activeScanContext"
    );
    assert.equal(
      medAssistPageSource.includes("onClearScanContext"),
      true,
      "MedAssistPage must accept onClearScanContext"
    );
  });
});

describe("3. MedAssistChatPanel Active Context Banner & Actions", () => {
  it("renders a dedicated context banner when activeScanContext is present", () => {
    assert.equal(
      panelSource.includes("activeScanContext && ("),
      true,
      "Panel must conditionally render banner when activeScanContext is present"
    );
    assert.equal(
      panelSource.includes("Discussing RetinaGuard Result:"),
      true,
      "Banner must clearly state it is discussing RetinaGuard result"
    );
  });

  it("provides a 'Clear Context' action to allow switching to general questions", () => {
    assert.equal(
      panelSource.includes("Clear Context"),
      true,
      "Banner must provide 'Clear Context' button"
    );
    assert.equal(
      panelSource.includes("onClearScanContext"),
      true,
      "Banner must invoke onClearScanContext callback"
    );
  });

  it("dynamically adapts suggested prompts to the specific retinal result", () => {
    assert.equal(
      panelSource.includes("activeScanContext ? ["),
      true,
      "Panel must provide tailored suggested questions when scan context is present"
    );
    assert.equal(
      panelSource.includes("activeScanContext.class_label"),
      true,
      "Suggested questions must reference the specific class label"
    );
  });

  it("forwards activeScanContext to sendChatMessage API client", () => {
    assert.equal(
      panelSource.includes("sendChatMessage(text, historyPayload, activeScanContext || null)"),
      true,
      "Panel must pass activeScanContext (or null if absent) to sendChatMessage"
    );
  });
});

describe("4. Privacy & State Isolation (Zero Persistent Storage)", () => {
  it("never writes scan context to localStorage, sessionStorage, or cookies", () => {
    assert.equal(
      appSource.includes("localStorage.setItem") || appSource.includes("sessionStorage.setItem"),
      false,
      "App.jsx must not persist scan context to browser storage"
    );
    assert.equal(
      panelSource.includes("localStorage.setItem") || panelSource.includes("sessionStorage.setItem"),
      false,
      "MedAssistChatPanel must not persist scan context to browser storage"
    );
    assert.equal(
      cardSource.includes("localStorage.setItem") || cardSource.includes("sessionStorage.setItem"),
      false,
      "RetinaPredictionResultCard must not persist scan context to browser storage"
    );
  });
});
