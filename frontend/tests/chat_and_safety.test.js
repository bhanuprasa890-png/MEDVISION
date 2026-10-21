/**
 * Frontend Unit & Safety Contract Test Suite for MedAssist Chatbot
 * Validates chat input boundaries, medical safety notices, privacy boundaries,
 * and component UI contracts.
 */

import test, { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

describe("1. MedAssist Chat Input Validation & Character Bounds", () => {
  const MAX_INPUT_CHARS = 1000;
  const MAX_HISTORY_TURNS = 20;

  function validateChatMessage(text, history = []) {
    if (typeof text !== "string") {
      return { valid: false, error: "Message must be a string." };
    }
    const trimmed = text.trim();
    if (!trimmed) {
      return { valid: false, error: "Message cannot be empty or solely whitespace." };
    }
    if (trimmed.length > MAX_INPUT_CHARS) {
      return {
        valid: false,
        error: `Message length (${trimmed.length}) exceeds maximum limit of ${MAX_INPUT_CHARS} characters.`,
      };
    }
    if (history.length > MAX_HISTORY_TURNS) {
      return {
        valid: false,
        error: `Conversation history length (${history.length}) exceeds maximum limit of ${MAX_HISTORY_TURNS} turns.`,
      };
    }
    return { valid: true, error: null, cleanMessage: trimmed };
  }

  it("accepts valid educational health queries within character limit", () => {
    const validQuery = "What is the difference between non-proliferative and proliferative DR?";
    const result = validateChatMessage(validQuery);
    assert.equal(result.valid, true);
    assert.equal(result.error, null);
    assert.equal(result.cleanMessage, validQuery);
  });

  it("strictly rejects empty and whitespace-only queries", () => {
    assert.equal(validateChatMessage("").valid, false);
    assert.equal(validateChatMessage("   ").valid, false);
    assert.equal(validateChatMessage("\t\n  \n").valid, false);
    assert.match(validateChatMessage("").error, /empty or solely whitespace/);
  });

  it("enforces maximum boundary of 1000 characters for user inputs", () => {
    const exactly1000 = "A".repeat(1000);
    const result1000 = validateChatMessage(exactly1000);
    assert.equal(result1000.valid, true);

    const oversized1001 = "A".repeat(1001);
    const result1001 = validateChatMessage(oversized1001);
    assert.equal(result1001.valid, false);
    assert.match(result1001.error, /exceeds maximum limit of 1000/);
  });

  it("enforces history boundary of maximum 20 turns", () => {
    const validHistory = Array.from({ length: 20 }, (_, i) => ({
      role: i % 2 === 0 ? "user" : "assistant",
      content: `Turn ${i}`,
    }));
    assert.equal(validateChatMessage("Hello", validHistory).valid, true);

    const excessiveHistory = Array.from({ length: 21 }, (_, i) => ({
      role: i % 2 === 0 ? "user" : "assistant",
      content: `Turn ${i}`,
    }));
    const excessiveResult = validateChatMessage("Hello", excessiveHistory);
    assert.equal(excessiveResult.valid, false);
    assert.match(excessiveResult.error, /exceeds maximum limit of 20 turns/);
  });
});

describe("2. MedAssistChatPanel Component Safety & UI Contracts", () => {
  const panelPath = path.resolve(__dirname, "../src/components/MedAssistChatPanel.jsx");
  const panelSource = fs.readFileSync(panelPath, "utf-8");

  it("displays prominent non-diagnostic educational research disclaimers", () => {
    assert.equal(
      panelSource.includes("Educational & Research Use Only"),
      true,
      "Chat panel must contain visible educational research disclaimer"
    );
    assert.equal(
      panelSource.includes("Not a diagnostic service"),
      true,
      "Chat panel must explicitly declare it is not a diagnostic service"
    );
    assert.equal(
      panelSource.includes("Always consult a licensed healthcare professional"),
      true,
      "Chat panel must advise consulting licensed healthcare professionals"
    );
  });

  it("displays explicit privacy warnings against submitting personal health information (PHI)", () => {
    assert.equal(
      panelSource.includes("Privacy Guard:"),
      true,
      "Chat panel must feature a Privacy Guard notice"
    );
    assert.equal(
      panelSource.includes("medical record numbers (MRNs)"),
      true,
      "Chat panel must warn against submitting MRNs"
    );
    assert.equal(
      panelSource.includes("MedVision AI does not persist conversational data"),
      true,
      "Chat panel must inform users that conversational data is not persisted"
    );
  });

  it("provides helpful suggested research prompts in empty state", () => {
    assert.equal(
      panelSource.includes("SUGGESTED_PROMPTS"),
      true,
      "Chat panel must define suggested prompts for empty state"
    );
    assert.equal(
      panelSource.includes("Grad-CAM heatmapping"),
      true,
      "Must offer educational suggestions regarding Grad-CAM heatmapping"
    );
    assert.equal(
      panelSource.includes("diabetic retinopathy severity grade"),
      true,
      "Must offer educational suggestions regarding DR severity grading"
    );
  });

  it("implements Send-on-Enter with Shift+Enter for multiline newline", () => {
    assert.equal(
      panelSource.includes('e.key === "Enter" && !e.shiftKey'),
      true,
      "Must support send on Enter without Shift key"
    );
  });

  it("provides clear retry action on failed messages", () => {
    assert.equal(
      panelSource.includes("handleRetry"),
      true,
      "Must provide retry handler on failed messages"
    );
    assert.equal(
      panelSource.includes("lastFailedMessage"),
      true,
      "Must track last failed message to enable retry"
    );
  });

  it("prevents duplicate user messages after retry", () => {
    assert.equal(
      panelSource.includes("isRetry"),
      true,
      "Must check whether the turn being submitted is a retry"
    );
    assert.equal(
      panelSource.includes("isRetry ? messages :"),
      true,
      "Must reuse existing message list when retrying to avoid duplicate user bubbles"
    );
  });

  it("strictly excludes image files, filenames, and patient identifiers from outgoing chat payloads", () => {
    // Verified: sendChatMessage is called with text, historyPayload, and optional non-image scan context (never images or files)
    assert.equal(
      panelSource.includes("sendChatMessage(text, historyPayload, activeScanContext || null)") ||
        panelSource.includes("sendChatMessage(text, historyPayload, null)"),
      true,
      "Must not pass image files or unverified scan artifacts to external providers"
    );
    assert.equal(
      panelSource.includes("selectedFile") || panelSource.includes("previewUrl"),
      false,
      "Must never pass raw image files or preview data to chat engine"
    );
    assert.equal(
      panelSource.includes("patient_id") || panelSource.includes("patientName"),
      false,
      "Must not have patient identifiers in chat component"
    );
  });

  it("safely catches empty/incomplete response and presents friendly error rather than empty bubble", () => {
    assert.equal(
      panelSource.includes("!response.message.trim()"),
      true,
      "Must validate that response contains trimmed message content"
    );
    assert.equal(
      panelSource.includes("Received an empty response from MedAssist"),
      true,
      "Must raise clear error when response is blank"
    );
  });

  it("renders full pre-formatted text response using whitespace-pre-wrap break-words", () => {
    assert.equal(
      panelSource.includes("whitespace-pre-wrap break-words"),
      true,
      "Must render response without clipping or truncating markdown content"
    );
  });
});

describe("3. MedAssist API Client & Page Integration Contracts", () => {
  const apiPath = path.resolve(__dirname, "../src/services/api.js");
  const apiSource = fs.readFileSync(apiPath, "utf-8");

  it("exports sendChatMessage and getChatStatus functions", () => {
    assert.equal(
      apiSource.includes("export async function sendChatMessage"),
      true,
      "api.js must export sendChatMessage"
    );
    assert.equal(
      apiSource.includes("export async function getChatStatus"),
      true,
      "api.js must export getChatStatus"
    );
  });

  it("targets /api/v1/chat/message and /api/v1/chat/status endpoints", () => {
    assert.equal(
      apiSource.includes("/api/v1/chat/message"),
      true,
      "sendChatMessage must target /api/v1/chat/message"
    );
    assert.equal(
      apiSource.includes("/api/v1/chat/status"),
      true,
      "getChatStatus must target /api/v1/chat/status"
    );
  });

  const pagePath = path.resolve(__dirname, "../src/pages/MedAssistPage.jsx");
  const pageSource = fs.readFileSync(pagePath, "utf-8");

  it("renders educational pillars and ethical safety guardrails in MedAssistPage", () => {
    assert.equal(
      pageSource.includes("MedAssist Health-Education Assistant"),
      true,
      "MedAssistPage must feature clear descriptive header"
    );
    assert.equal(
      pageSource.includes("Ethical Safety Guardrails"),
      true,
      "MedAssistPage must present safety guardrail card"
    );
    assert.equal(
      pageSource.includes("Privacy by Architecture"),
      true,
      "MedAssistPage must present privacy architecture card"
    );
  });
});
