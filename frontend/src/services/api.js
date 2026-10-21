/**
 * API client service for MedVision AI backend.
 *
 * Notice: This client contains strictly UI-to-API communication logic.
 * It does NOT contain database credentials, secrets, model weights, or inference code.
 */

const API_BASE_URL = (import.meta.env && import.meta.env.VITE_API_BASE_URL) || "http://localhost:8000";

if (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.PROD && !import.meta.env.VITE_API_BASE_URL) {
  console.warn(
    "[MEDVISION] Warning: VITE_API_BASE_URL is not set in production build. Falling back to default: http://localhost:8000. Set VITE_API_BASE_URL during build for production deployments."
  );
}

// In-memory runtime authorization token (e.g. from user session or auth gateway)
// Notice: Tokens are strictly held in-memory and NEVER persisted to disk/localStorage/bundle.
let runtimeAuthToken = null;

/**
 * Configure runtime authorization token for API requests.
 * @param {string|null} token
 */
export function setAuthToken(token) {
  runtimeAuthToken = token && typeof token === "string" ? token.trim() : null;
}

/**
 * Get the currently configured runtime authorization token.
 * @returns {string|null}
 */
export function getAuthToken() {
  return runtimeAuthToken;
}

/**
 * Build authorization headers if a token is configured.
 * @returns {Record<string, string>}
 */
function getAuthHeaders() {
  if (!runtimeAuthToken) return {};
  return {
    Authorization: `Bearer ${runtimeAuthToken}`,
  };
}


/**
 * Fetch backend system health status.
 * @returns {Promise<{ status: string, service: string, version: string, timestamp: string }>}
 */
export async function getHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: "GET",
      headers: { Accept: "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Health check failed with HTTP status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Health check error:", error);
    throw error;
  }
}

/**
 * Upload retinal fundus image for validation and placeholder analysis.
 * @param {File} file
 * @returns {Promise<object>}
 */
export async function analyzeRetina(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/retina/analyze`, {
      method: "POST",
      headers: { ...getAuthHeaders() },
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      const errorMsg = data.detail || `Server returned error status ${response.status}`;
      throw new Error(errorMsg);
    }

    return data;
  } catch (error) {
    console.error("Retina analysis API error:", error);
    throw error;
  }
}

/**
 * Upload retinal fundus image for real AI prediction and Grad-CAM explainability.
 * @param {File} file
 * @param {boolean} includeGradcam
 * @returns {Promise<object>}
 */
export async function predictRetina(file, includeGradcam = true) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const url = `${API_BASE_URL}/api/v1/retina/predict?include_gradcam=${Boolean(includeGradcam)}`;
    const response = await fetch(url, {
      method: "POST",
      headers: { ...getAuthHeaders() },
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      const errorMsg = data.detail || `Server returned error status ${response.status}`;
      throw new Error(errorMsg);
    }

    return data;
  } catch (error) {
    console.error("Retina prediction API error:", error);
    throw error;
  }
}

/**
 * Fetch RetinaGuard AI model readiness and hardware status.
 * @returns {Promise<{ status: string, is_loaded: boolean, model_version: string, device: string, num_classes: number, classes: object, gradcam_supported: boolean }>}
 */
export async function getRetinaModelStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/retina/model-status`, {
      method: "GET",
      headers: { Accept: "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch model status (HTTP ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error("Model status check error:", error);
    throw error;
  }
}

/**
 * Upload chest radiograph (CXR) for validation and placeholder analysis.
 * @param {File} file
 * @returns {Promise<object>}
 */
export async function analyzeChestXray(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chest-xray/analyze`, {
      method: "POST",
      headers: { ...getAuthHeaders() },
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      const errorMsg = data.detail || `Server returned error status ${response.status}`;
      throw new Error(errorMsg);
    }

    return data;
  } catch (error) {
    console.error("Chest X-Ray analysis API error:", error);
    throw error;
  }
}

/**
 * Upload chest radiograph (CXR) for real multi-label AI prediction and Grad-CAM explainability.
 * @param {File} file
 * @param {boolean} includeGradcam
 * @returns {Promise<object>}
 */
export async function predictChestXray(file, includeGradcam = true) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const url = `${API_BASE_URL}/api/v1/chest-xray/predict?include_gradcam=${Boolean(includeGradcam)}`;
    const response = await fetch(url, {
      method: "POST",
      headers: { ...getAuthHeaders() },
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      const errorMsg = data.detail || `Server returned error status ${response.status}`;
      throw new Error(errorMsg);
    }

    return data;
  } catch (error) {
    console.error("Chest X-Ray prediction API error:", error);
    throw error;
  }
}

/**
 * Fetch Chest X-Ray AI model readiness, hardware status, and supported pathologies.
 * @returns {Promise<{ model_name: string, model_version: string, status: string, device: string, checkpoint_hash: string, weights_path: string, pathologies_count: number, pathologies: string[], disclaimer: string }>}
 */
export async function getChestXrayModelStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chest-xray/model-status`, {
      method: "GET",
      headers: { Accept: "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch CXR model status (HTTP ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error("CXR Model status check error:", error);
    throw error;
  }
}

import { normalizeErrorMessage } from "../utils/chatResponseNormalizer.js";


/**
 * Send health-education query to MedAssist conversational engine.
 * @param {string} message - User query text (max 1000 characters)
 * @param {Array<{role: string, content: string}>} conversationHistory - Session history (up to 20 turns)
 * @param {object|null} scanContext - Optional validated non-identifiable scan metadata
 * @param {string} language - User language preference code (e.g. 'en', 'ta', 'hi', 'te')
 * @returns {Promise<{ message: string, provider: string, model: string, disclaimer: string, created_at: string }>}
 */
export async function sendChatMessage(message, conversationHistory = [], scanContext = null, language = "en") {
  try {
    const payload = {
      message: message.trim(),
      conversation_history: conversationHistory,
      scan_context: scanContext,
      language: language || "en",
    };

    const response = await fetch(`${API_BASE_URL}/api/v1/chat/message`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg = normalizeErrorMessage(data, response.status);
      const error = new Error(errorMsg);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (error) {
    console.error("MedAssist chat API error:", error);
    if (!(error instanceof Error) || !error.message || error.message === "[object Object]") {
      const safeMsg = normalizeErrorMessage(error);
      const err = new Error(safeMsg);
      if (error && typeof error === "object") {
        err.status = error.status;
        err.data = error.data;
      }
      throw err;
    }
    throw error;
  }
}

/**
 * Fetch MedAssist provider readiness and configuration status.
 * @returns {Promise<{ status: string, provider: string, model: string, is_configured: boolean, disclaimer: string }>}
 */
export async function getChatStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/status`, {
      method: "GET",
      headers: { Accept: "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch MedAssist status (HTTP ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error("MedAssist status check error:", error);
    throw error;
  }
}
