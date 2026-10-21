/**
 * Frontend Unit & Regression Tests for Task 20
 * Verifies UX, Accessibility (a11y), Workflow Reliability, and Non-Diagnostic Presentation.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const indexCss = fs.readFileSync(
  path.join(__dirname, "../src/index.css"),
  "utf8"
);
const appSource = fs.readFileSync(
  path.join(__dirname, "../src/App.jsx"),
  "utf8"
);
const headerSource = fs.readFileSync(
  path.join(__dirname, "../src/components/Header.jsx"),
  "utf8"
);
const uploaderSource = fs.readFileSync(
  path.join(__dirname, "../src/components/ImageUploader.jsx"),
  "utf8"
);
const resultCardSource = fs.readFileSync(
  path.join(__dirname, "../src/components/RetinaPredictionResultCard.jsx"),
  "utf8"
);
const chatPanelSource = fs.readFileSync(
  path.join(__dirname, "../src/components/MedAssistChatPanel.jsx"),
  "utf8"
);
const hookSource = fs.readFileSync(
  path.join(__dirname, "../src/hooks/useImageUpload.js"),
  "utf8"
);

describe("1. Accessible Focus and Reduced Motion (WCAG Guidelines)", () => {
  it("defines accessible :focus-visible outlines in index.css", () => {
    assert.equal(
      indexCss.includes(":focus-visible"),
      true,
      "index.css must define :focus-visible styling for keyboard users"
    );
    assert.equal(
      indexCss.includes("ring-teal-400"),
      true,
      "Focus indicator must have distinct high-contrast color"
    );
  });

  it("defines @media (prefers-reduced-motion) rules in index.css", () => {
    assert.equal(
      indexCss.includes("@media (prefers-reduced-motion: reduce)"),
      true,
      "index.css must honor reduced-motion user preference"
    );
    assert.equal(
      indexCss.includes("animation-duration: 0.01ms !important"),
      true,
      "Reduced-motion rule must minimize animation durations"
    );
  });

  it("applies motion-reduce:animate-none to animated elements across components", () => {
    assert.equal(
      headerSource.includes("motion-reduce:animate-none"),
      true,
      "Header status icons must support motion-reduce"
    );
    assert.equal(
      chatPanelSource.includes("motion-reduce:animate-none"),
      true,
      "MedAssist thinking and bounce animations must support motion-reduce"
    );
    assert.equal(
      resultCardSource.includes("motion-reduce:transition-none"),
      true,
      "Result card score bars must support motion-reduce"
    );
  });
});

describe("2. Semantic Landmarks, ARIA Labels, and Keyboard Navigation", () => {
  it("provides keyboard-accessible logo and labeled main navigation in Header", () => {
    assert.equal(
      headerSource.includes('aria-label="Main navigation"'),
      true,
      "Navigation landmark must have descriptive aria-label"
    );
    assert.equal(
      headerSource.includes('role="button"') && headerSource.includes("tabIndex={0}"),
      true,
      "Logo must be keyboard focusable and identify as a button"
    );
    assert.equal(
      headerSource.includes('e.key === "Enter" || e.key === " "'),
      true,
      "Logo must handle Enter and Space keyboard activations"
    );
    assert.equal(
      headerSource.includes("aria-current="),
      true,
      "Active tab must declare aria-current='page'"
    );
  });

  it("implements keyboard-accessible image upload dropzone in ImageUploader", () => {
    assert.equal(
      uploaderSource.includes('role="button"'),
      true,
      "Dropzone must declare role='button'"
    );
    assert.equal(
      uploaderSource.includes("tabIndex={0}"),
      true,
      "Dropzone must be keyboard focusable with tabIndex 0"
    );
    assert.equal(
      uploaderSource.includes('e.key === "Enter" || e.key === " "'),
      true,
      "Dropzone must trigger file browser on Enter or Space"
    );
    assert.equal(
      uploaderSource.includes('role="alert"') && uploaderSource.includes('aria-live="assertive"'),
      true,
      "Upload validation errors must be announced to screen readers"
    );
  });

  it("provides accessible modal dialog and labeled zoom controls in ImageUploader", () => {
    assert.equal(
      uploaderSource.includes('aria-label="Zoom out"'),
      true,
      "Zoom out button must have accessible aria-label"
    );
    assert.equal(
      uploaderSource.includes('aria-label="Zoom in"'),
      true,
      "Zoom in button must have accessible aria-label"
    );
    assert.equal(
      uploaderSource.includes('aria-label="Reset zoom to 100%"'),
      true,
      "Zoom reset button must have accessible aria-label"
    );
  });

  it("ensures accessible form controls and region landmarks in MedAssistChatPanel", () => {
    assert.equal(
      chatPanelSource.includes('aria-label="Ask MedAssist a question'),
      true,
      "Chat textarea must have an accessible aria-label"
    );
    assert.equal(
      chatPanelSource.includes('aria-label="Send message"'),
      true,
      "Send button must have an accessible aria-label"
    );
    assert.equal(
      chatPanelSource.includes('role="region"') && chatPanelSource.includes('aria-label="Conversation messages"'),
      true,
      "Chat messages view must have accessible region semantics"
    );
    assert.equal(
      chatPanelSource.includes('role="status"') && chatPanelSource.includes('aria-live="polite"'),
      true,
      "Thinking state must be announced via aria-live status"
    );
  });
});

describe("3. Medical-Result Presentation & Clinical Consultation Guardrails", () => {
  it("uses non-diagnostic category phrasing and avoids 'Unknown Diagnosis'", () => {
    assert.equal(
      resultCardSource.includes("Unknown Diagnosis"),
      false,
      "Result card must not claim or imply 'Diagnosis'"
    );
    assert.equal(
      resultCardSource.includes("Classification Unavailable"),
      true,
      "Result card must use neutral non-diagnostic terminology"
    );
  });

  it("clearly explains that softmax output is uncalibrated model score, not clinical probability", () => {
    assert.equal(
      resultCardSource.includes("Uncalibrated model score, not a true clinical probability"),
      true,
      "Must explicitly clarify confidence score is uncalibrated"
    );
    assert.equal(
      resultCardSource.includes("Softmax confidence reflects model activation spread and must not be interpreted as calibrated epidemiological risk"),
      true,
      "Must explain softmax spread in clinical guidance section"
    );
  });

  it("advises evaluation by a licensed eye-care professional (ophthalmologist/optometrist)", () => {
    assert.equal(
      resultCardSource.includes("licensed ophthalmologist or optometrist"),
      true,
      "Result card must advise comprehensive exam by qualified eye care specialist"
    );
  });

  it("explicitly states unsupported scope regarding systemic and other eye diseases", () => {
    assert.equal(
      resultCardSource.includes("does not detect or rule out other eye conditions (glaucoma, macular degeneration) or systemic diseases"),
      true,
      "Must clearly define model boundaries and exclude unsupported conditions"
    );
  });

  it("provides accessible ARIA tablist for visual modes and progressbars for class scores", () => {
    assert.equal(
      resultCardSource.includes('role="tablist"') && resultCardSource.includes('role="tab"'),
      true,
      "Visual attribution modes must use ARIA tablist/tab semantics"
    );
    assert.equal(
      resultCardSource.includes('role="progressbar"'),
      true,
      "Multi-class score distribution must use accessible ARIA progressbars"
    );
  });
});

describe("4. Workflow Reliability & Input Preservation Across Navigation", () => {
  it("preserves unsent inputs and page states across tab navigation using visibility toggling", () => {
    assert.equal(
      appSource.includes('className={activeTab === "medassist" ? "block" : "hidden"}'),
      true,
      "MedAssist page must remain mounted to preserve draft input during navigation"
    );
    assert.equal(
      appSource.includes('className={activeTab === "retina" ? "block" : "hidden"}'),
      true,
      "Retina Analysis page must remain mounted to preserve upload and scan inspection"
    );
  });

  it("prevents duplicate concurrent analysis submissions in useImageUpload hook", () => {
    assert.equal(
      hookSource.includes("if (isLoading)") && hookSource.includes("return;"),
      true,
      "uploadAndAnalyze must guard against duplicate submissions when isLoading is true"
    );
  });
});
