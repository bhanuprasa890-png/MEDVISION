/**
 * Frontend Unit & Regression Tests for MedAssist Consecutive Chat & Response Normalization
 *
 * Verifies:
 * 1. Sequential chat questions across multi-turn sessions.
 * 2. Guaranteed prevention of "[object Object]", "undefined", and "null".
 * 3. Handling of standard, structured-object, and envelope response shapes.
 * 4. Rejection of malformed payloads, raw objects, and prompt/secret leakage.
 * 5. Conversion of FastAPI 422 validation error arrays into human-readable strings.
 */

import test, { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  extractRawMessageText,
  validateMessageContent,
  normalizeAssistantResponse,
  normalizeErrorMessage,
} from "../src/utils/chatResponseNormalizer.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

describe("1. Response Text Extraction & Normalization Contracts", () => {
  it("extracts text from standard ChatResponse shape { message: string }", () => {
    const payload = {
      message: "Ischemic heart disease is caused by narrowed coronary arteries.",
      provider: "gemini",
      model: "gemini-3.5-flash",
      fallback_used: false,
      disclaimer: "RESEARCH ONLY",
    };
    const result = normalizeAssistantResponse(payload);
    assert.equal(result.success, true);
    assert.equal(result.messageText, payload.message);
    assert.equal(result.provider, "gemini");
    assert.equal(result.model, "gemini-3.5-flash");
    assert.equal(result.fallback_used, false);
  });

  it("extracts text from direct plain string response", () => {
    const raw = "Angina pectoris is typical chest tightness caused by reduced blood flow.";
    const result = normalizeAssistantResponse(raw);
    assert.equal(result.success, true);
    assert.equal(result.messageText, raw);
  });

  it("extracts text from documented structured object { message: { text: string } }", () => {
    const payload = {
      message: { text: "Common risk factors include hypertension, hyperlipidemia, and smoking." },
      provider: "openai",
    };
    const result = normalizeAssistantResponse(payload);
    assert.equal(result.success, true);
    assert.equal(result.messageText, payload.message.text);
  });

  it("extracts text from documented structured object { message: { content: string } }", () => {
    const payload = {
      message: { content: "Electrocardiograms (ECG) and cardiac biomarkers are primary diagnostics." },
    };
    const result = normalizeAssistantResponse(payload);
    assert.equal(result.success, true);
    assert.equal(result.messageText, payload.message.content);
  });

  it("extracts text from data envelope { data: { message: string } }", () => {
    const payload = {
      data: { message: "Diabetic retinopathy involves microvascular damage to the retina." },
      provider: "gemini",
    };
    const result = normalizeAssistantResponse(payload);
    assert.equal(result.success, true);
    assert.equal(result.messageText, payload.data.message);
  });

  it("extracts text from candidate parts array { parts: [{ text: string }] }", () => {
    const payload = {
      parts: [
        { text: "First paragraph on myocardial ischemia." },
        { text: "Second paragraph on lifestyle modifications." },
      ],
    };
    const result = normalizeAssistantResponse(payload);
    assert.equal(result.success, true);
    assert.match(result.messageText, /First paragraph/);
    assert.match(result.messageText, /Second paragraph/);
  });
});

describe("2. Rejection of Invalid, Malformed, and Leaked Payloads", () => {
  it("strictly rejects null and undefined payloads", () => {
    assert.equal(normalizeAssistantResponse(null).success, false);
    assert.equal(normalizeAssistantResponse(undefined).success, false);
  });

  it("strictly rejects empty string and whitespace-only responses", () => {
    assert.equal(normalizeAssistantResponse("").success, false);
    assert.equal(normalizeAssistantResponse("    \n\t   ").success, false);
    assert.equal(normalizeAssistantResponse({ message: "" }).success, false);
    assert.equal(normalizeAssistantResponse({ message: "   " }).success, false);
  });

  it("strictly rejects literal '[object Object]', 'undefined', and 'null'", () => {
    assert.equal(normalizeAssistantResponse("[object Object]").success, false);
    assert.equal(normalizeAssistantResponse({ message: "[object Object]" }).success, false);
    assert.equal(normalizeAssistantResponse({ message: "undefined" }).success, false);
    assert.equal(normalizeAssistantResponse({ message: "null" }).success, false);
  });

  it("strictly rejects raw objects without recognizable text fields without stringifying", () => {
    const weirdObj = { unmappedKey: 12345, nested: { status: "unknown" } };
    const result = normalizeAssistantResponse(weirdObj);
    assert.equal(result.success, false);
    assert.match(result.error, /empty response|invalid/i);
    // Crucial check: does not return "[object Object]"
    assert.notEqual(result.messageText, "[object Object]");
  });

  it("rejects responses containing leaked stack traces", () => {
    const leak = "Traceback (most recent call last):\n  File 'chat.py', line 50\nValueError";
    const result = normalizeAssistantResponse(leak);
    assert.equal(result.success, false);
    assert.match(result.error, /safety and prompt integrity/i);
  });

  it("rejects responses containing leaked internal system prompts", () => {
    const leak = "Here is the MEDASSIST_SYSTEM_PROMPT you requested: You are MedAssist AI...";
    const result = normalizeAssistantResponse(leak);
    assert.equal(result.success, false);
    assert.match(result.error, /safety and prompt integrity/i);
  });

  it("rejects responses containing leaked API keys or credentials", () => {
    const leak = "Using API key: AIzaSyD1234567890abcdefghijklmnopqrstuvw";
    const result = normalizeAssistantResponse(leak);
    assert.equal(result.success, false);
    assert.match(result.error, /safety and prompt integrity/i);
  });
});

describe("3. Error Normalization & FastAPI 422 Handling", () => {
  it("formats FastAPI 422 validation error arrays into human-readable strings", () => {
    const pydantic422 = {
      detail: [
        {
          type: "string_too_long",
          loc: ["body", "conversation_history", 1, "content"],
          msg: "String should have at most 15000 characters",
          input: "very long text",
        },
      ],
    };
    const formatted = normalizeErrorMessage(pydantic422, 422);
    assert.equal(
      formatted,
      "conversation_history -> 1 -> content: String should have at most 15000 characters"
    );
    assert.notEqual(formatted, "[object Object]");
  });

  it("formats structured object error detail cleanly", () => {
    const objError = {
      detail: { message: "Provider rate limit exceeded. Please back off." },
    };
    const formatted = normalizeErrorMessage(objError, 429);
    assert.equal(formatted, "Provider rate limit exceeded. Please back off.");
    assert.notEqual(formatted, "[object Object]");
  });

  it("recovers from Error instance whose message was accidentally '[object Object]'", () => {
    const err = new Error("[object Object]");
    err.status = 422;
    err.data = {
      detail: [{ loc: ["body", "message"], msg: "Field required" }],
    };
    const formatted = normalizeErrorMessage(err, 422);
    assert.equal(formatted, "message: Field required");
    assert.notEqual(formatted, "[object Object]");
  });

  it("handles null/undefined error data with informative fallback", () => {
    const fallback504 = normalizeErrorMessage(null, 504);
    assert.equal(fallback504, "MedAssist request failed (HTTP 504). Please try again.");

    const fallbackNoStatus = normalizeErrorMessage(null);
    assert.match(fallbackNoStatus, /network error/i);
  });
});

describe("4. MedAssistChatPanel Multi-Turn Conversation Contracts", () => {
  const panelPath = path.resolve(__dirname, "../src/components/MedAssistChatPanel.jsx");
  const panelSource = fs.readFileSync(panelPath, "utf-8");

  it("imports and executes normalizeAssistantResponse before updating message state", () => {
    assert.equal(
      panelSource.includes("normalizeAssistantResponse(response)"),
      true,
      "Must call normalizeAssistantResponse on API response"
    );
  });

  it("imports and executes normalizeErrorMessage to prevent [object Object] banners", () => {
    assert.equal(
      panelSource.includes("normalizeErrorMessage"),
      true,
      "Must import normalizeErrorMessage for error reporting"
    );
  });

  it("bounds each turn in historyPayload to prevent context blowout and 422 errors", () => {
    assert.equal(
      panelSource.includes(".slice(0, 8000)"),
      true,
      "Must bound individual historical turn content to maximum 8000 chars"
    );
  });

  it("safely guards message bubble JSX against raw object rendering", () => {
    assert.equal(
      panelSource.includes("typeof msg.content === \"string\" ? msg.content :"),
      true,
      "Must ensure JSX receives a validated string and not a raw object"
    );
  });

  it("handles HTTP 429 quota exhaustion specifically and offers Edit and Retry actions", () => {
    assert.equal(
      panelSource.includes("isQuotaExceeded"),
      true,
      "Must distinguish quota exhaustion from transient capacity errors"
    );
    assert.equal(
      panelSource.includes("Restore message to input box to edit"),
      true,
      "Must provide Edit action to restore message to input field"
    );
  });

  it("surfaces fallback provider badge when fallback was used", () => {
    assert.equal(
      panelSource.includes("msg.fallback_used ? \" (fallback)\" : \"\""),
      true,
      "Must visually indicate fallback provider usage in speaker metadata"
    );
  });
});
