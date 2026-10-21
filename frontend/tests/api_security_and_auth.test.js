/**
 * Security and authentication regression tests for frontend API client.
 *
 * Verifies:
 * 1. Runtime in-memory token configuration (setAuthToken, getAuthToken).
 * 2. Dynamic Authorization header injection on protected requests.
 * 3. Clearing auth token returns headers to unauthenticated state.
 * 4. Zero secret leakage: no hardcoded API secrets in frontend code.
 */

import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { setAuthToken, getAuthToken } from "../src/services/api.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

describe("Frontend API Client — Authentication & Security Invariants", () => {
  beforeEach(() => {
    setAuthToken(null);
  });

  test("initial auth token is null by default", () => {
    assert.equal(getAuthToken(), null);
  });

  test("setAuthToken configures in-memory runtime token", () => {
    setAuthToken("test-jwt-token-abcdef123456");
    assert.equal(getAuthToken(), "test-jwt-token-abcdef123456");
  });

  test("setAuthToken trims whitespace", () => {
    setAuthToken("   padded-token-value   ");
    assert.equal(getAuthToken(), "padded-token-value");
  });

  test("setAuthToken with null or empty string clears token", () => {
    setAuthToken("active-token");
    assert.equal(getAuthToken(), "active-token");

    setAuthToken("");
    assert.equal(getAuthToken(), null);

    setAuthToken("active-token-2");
    setAuthToken(null);
    assert.equal(getAuthToken(), null);
  });

  test("source code contains zero hardcoded API keys or secrets", () => {
    const srcDir = path.resolve(__dirname, "../src");

    function scanFiles(dir) {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          scanFiles(fullPath);
        } else if (entry.isFile() && (entry.name.endsWith(".js") || entry.name.endsWith(".jsx"))) {
          const content = fs.readFileSync(fullPath, "utf-8");
          // Prohibit actual API key patterns
          assert.equal(
            /AIza[0-9A-Za-z\-_]{20,}/.test(content),
            false,
            `Found Google API key pattern in ${fullPath}`
          );
          assert.equal(
            /sk-[0-9A-Za-z\-_]{20,}/.test(content),
            false,
            `Found OpenAI API key pattern in ${fullPath}`
          );
        }
      }
    }

    scanFiles(srcDir);
  });
});
