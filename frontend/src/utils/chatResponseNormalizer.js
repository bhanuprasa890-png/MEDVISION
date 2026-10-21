/**
 * Normalizer and validator for MedAssist conversational assistant responses and errors.
 *
 * Guarantees:
 * 1. Strict extraction of clean string messages from known response shapes.
 * 2. Rejection of un-extractable objects without resorting to String(obj) or JSON.stringify(obj).
 * 3. Never renders "[object Object]", "undefined", or "null".
 * 4. Sanitization against leaked stack traces, system instructions, or credentials.
 * 5. Structured normalization of FastAPI 422 validation errors into human-readable text.
 */

const FORBIDDEN_LITERALS = new Set([
  "[object Object]",
  "[object Array]",
  "[object Error]",
  "undefined",
  "null",
  "NaN",
]);

const SENSITIVE_PATTERNS = [
  /Traceback\s+\(most\s+recent\s+call\s+last\)/i,
  /GEMINI_API_KEY/i,
  /OPENAI_API_KEY/i,
  /MEDASSIST_SYSTEM_PROMPT/i,
  /SYSTEM\s+INSTRUCTION/i,
  /\bsk-[a-zA-Z0-9]{20,}\b/,
  /\bAIzaSy[a-zA-Z0-9_-]{20,}\b/,
];

/**
 * Extract clean string message from recognized response payloads.
 * @param {unknown} response
 * @returns {string|null}
 */
export function extractRawMessageText(response) {
  if (typeof response === "string") {
    const trimmed = response.trim();
    return trimmed.length > 0 ? trimmed : null;
  }

  if (!response || typeof response !== "object") {
    return null;
  }

  // 1. Direct message property
  if (typeof response.message === "string") {
    const trimmed = response.message.trim();
    if (trimmed.length > 0) return trimmed;
  } else if (response.message && typeof response.message === "object") {
    // Nested message object e.g. { message: { text: "..." } } or { message: { content: "..." } }
    if (typeof response.message.text === "string" && response.message.text.trim()) {
      return response.message.text.trim();
    }
    if (typeof response.message.content === "string" && response.message.content.trim()) {
      return response.message.content.trim();
    }
  }

  // 2. Direct text property
  if (typeof response.text === "string") {
    const trimmed = response.text.trim();
    if (trimmed.length > 0) return trimmed;
  }

  // 3. Direct content property (if string)
  if (typeof response.content === "string") {
    const trimmed = response.content.trim();
    if (trimmed.length > 0) return trimmed;
  }

  // 4. Data envelope e.g. { data: { message: "..." } }
  if (response.data && typeof response.data === "object") {
    const fromData = extractRawMessageText(response.data);
    if (fromData) return fromData;
  }

  // 5. Parts array e.g. { parts: [{ text: "..." }] }
  if (Array.isArray(response.parts) && response.parts.length > 0) {
    const textPieces = response.parts
      .map((p) => (p && typeof p.text === "string" ? p.text : ""))
      .filter((t) => t.length > 0);
    if (textPieces.length > 0) {
      return textPieces.join("\n\n").trim();
    }
  }

  // 6. Candidates array e.g. { candidates: [{ content: { parts: [{ text: "..." }] } }] }
  if (Array.isArray(response.candidates) && response.candidates.length > 0) {
    const firstCand = response.candidates[0];
    if (firstCand?.content?.parts && Array.isArray(firstCand.content.parts)) {
      const textPieces = firstCand.content.parts
        .map((p) => (p && typeof p.text === "string" ? p.text : ""))
        .filter((t) => t.length > 0);
      if (textPieces.length > 0) {
        return textPieces.join("\n\n").trim();
      }
    }
  }

  return null;
}

/**
 * Validate extracted message text against forbidden literals, emptiness, and leakage.
 * @param {string|null} text
 * @returns {{ valid: boolean, error?: string }}
 */
export function validateMessageContent(text) {
  if (!text || typeof text !== "string") {
    return { valid: false, error: "Received an empty response from MedAssist. Please try again." };
  }

  const trimmed = text.trim();
  if (trimmed.length === 0) {
    return { valid: false, error: "Received an empty response from MedAssist. Please try again." };
  }

  if (FORBIDDEN_LITERALS.has(trimmed)) {
    return { valid: false, error: "Received an invalid or malformed response from MedAssist. Please try again." };
  }

  // Check for sensitive leakage or raw provider dumps
  for (const pattern of SENSITIVE_PATTERNS) {
    if (pattern.test(trimmed)) {
      return {
        valid: false,
        error: "MedAssist response was suppressed due to safety and prompt integrity rules. Please try again.",
      };
    }
  }

  return { valid: true };
}

/**
 * Normalize and validate complete assistant response.
 * Returns distinct typed result without throwing.
 *
 * @param {unknown} response
 * @returns {{
 *   success: boolean,
 *   messageText?: string,
 *   provider?: string,
 *   model?: string,
 *   fallback_used?: boolean,
 *   disclaimer?: string,
 *   created_at?: string,
 *   error?: string
 * }}
 */
export function normalizeAssistantResponse(response) {
  if (!response) {
    return {
      success: false,
      error: "Received an empty response from MedAssist. Please try again.",
    };
  }

  const rawText = extractRawMessageText(response);
  const validation = validateMessageContent(rawText);

  if (!validation.valid) {
    return {
      success: false,
      error: validation.error || "Received an invalid response from MedAssist. Please try again.",
    };
  }

  const isObject = typeof response === "object" && response !== null;

  return {
    success: true,
    messageText: rawText.trim(),
    provider: isObject && typeof response.provider === "string" ? response.provider : undefined,
    model: isObject && typeof response.model === "string" ? response.model : undefined,
    fallback_used: isObject ? Boolean(response.fallback_used) : false,
    disclaimer: isObject && typeof response.disclaimer === "string" ? response.disclaimer : undefined,
    created_at: isObject && typeof response.created_at === "string" ? response.created_at : undefined,
  };
}

/**
 * Normalize API error payloads, HTTP statuses, and Error objects into human-readable text.
 * Never returns "[object Object]" or raw stack dumps.
 *
 * @param {unknown} errorOrData
 * @param {number} [httpStatus]
 * @returns {string}
 */
export function normalizeErrorMessage(errorOrData, httpStatus) {
  if (!errorOrData) {
    return httpStatus
      ? `MedAssist request failed (HTTP ${httpStatus}). Please try again.`
      : "An unexpected network error occurred while communicating with MedAssist.";
  }

  // 1. Error instance
  if (errorOrData instanceof Error) {
    const msg = errorOrData.message?.trim();
    if (msg && !FORBIDDEN_LITERALS.has(msg) && !msg.startsWith("[object ")) {
      return msg;
    }
    // If Error.message was "[object Object]", check errorOrData.data
    if (errorOrData.data) {
      return normalizeErrorMessage(errorOrData.data, errorOrData.status || httpStatus);
    }
  }

  // 2. Direct string payload
  if (typeof errorOrData === "string") {
    const trimmed = errorOrData.trim();
    if (trimmed && !FORBIDDEN_LITERALS.has(trimmed) && !trimmed.startsWith("[object ")) {
      return trimmed;
    }
  }

  // 3. Object with .detail
  if (typeof errorOrData === "object" && errorOrData !== null) {
    const detail = errorOrData.detail;

    // A. detail is a string
    if (typeof detail === "string") {
      const trimmed = detail.trim();
      if (trimmed && !FORBIDDEN_LITERALS.has(trimmed)) {
        return trimmed;
      }
    }

    // B. detail is an Array of validation errors (FastAPI 422)
    if (Array.isArray(detail) && detail.length > 0) {
      const items = detail
        .map((item) => {
          if (typeof item === "string") return item.trim();
          if (item && typeof item === "object") {
            const locParts = Array.isArray(item.loc)
              ? item.loc.filter((p) => p !== "body")
              : [];
            const loc = locParts.join(" -> ");
            const msg = item.msg || item.message || "";
            return loc ? `${loc}: ${msg}` : msg;
          }
          return "";
        })
        .filter((t) => t.length > 0 && !FORBIDDEN_LITERALS.has(t));

      if (items.length > 0) {
        return items.join("; ");
      }
    }

    // C. detail is a nested object
    if (detail && typeof detail === "object") {
      if (typeof detail.message === "string" && detail.message.trim()) {
        return detail.message.trim();
      }
      if (typeof detail.error === "string" && detail.error.trim()) {
        return detail.error.trim();
      }
    }

    // D. Top-level message or error
    if (typeof errorOrData.message === "string") {
      const trimmed = errorOrData.message.trim();
      if (trimmed && !FORBIDDEN_LITERALS.has(trimmed) && !trimmed.startsWith("[object ")) {
        return trimmed;
      }
    }
    if (typeof errorOrData.error === "string") {
      const trimmed = errorOrData.error.trim();
      if (trimmed && !FORBIDDEN_LITERALS.has(trimmed) && !trimmed.startsWith("[object ")) {
        return trimmed;
      }
    }
  }

  return httpStatus
    ? `MedAssist request failed with status ${httpStatus}. Please try again.`
    : "An unexpected error occurred while communicating with MedAssist.";
}
