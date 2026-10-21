# API Contract Documentation — MedVision AI

This document outlines the API specifications for the MedVision AI backend service.

---

## Base Configuration

- **Development Host**: `http://127.0.0.1:8000` or `http://localhost:8000`
- **Prefix**: `/api` (for health) and `/api/v1` (for domain endpoints)
- **Content Type**: `application/json` (except image uploads which use `multipart/form-data`)

---

## 1. Health Check Endpoint

### `GET /api/health`

Verifies that the backend service is operational.

#### Request
No parameters required.

#### Response: `200 OK`
```json
{
  "status": "healthy",
  "service": "MedVision AI Backend",
  "version": "0.1.0-alpha",
  "timestamp": "2026-10-16T11:15:30.123456Z",
  "environment": "development"
}
```

---

## 2. Retinal Image Analysis Endpoint

### `POST /api/v1/retina/analyze`

Uploads a retinal fundus image for validation and session registration.

#### Request Specifications
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `file`: Binary file upload (Required)
- **Constraints**:
  - Formats: `image/jpeg`, `image/png`, `image/webp`
  - Max Size: `10 MB` (10,485,760 bytes)

#### Success Response: `200 OK` (Development Placeholder)
```json
{
  "session_id": "b3f0249c-f9e4-4d8e-b5f7-9bf4e4d7a8c1",
  "modality": "retina",
  "status": "DEVELOPMENT_PLACEHOLDER",
  "message": "Retina model pipeline is not implemented yet. File successfully received and validated.",
  "model_version": "retina_v0.1_dev_placeholder",
  "metadata": {
    "file_name": "sample_retina.jpg",
    "file_size_bytes": 1048576,
    "mime_type": "image/jpeg",
    "image_width": 2048,
    "image_height": 1536,
    "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "prediction": null,
  "explanation": null,
  "disclaimer": "RESEARCH ONLY: Not for clinical or diagnostic use. Never use placeholder responses for patient decisions.",
  "created_at": "2026-10-16T11:15:32.456789Z"
}
```

#### Error Responses

##### `400 Bad Request` — Invalid or Corrupted Image
```json
{
  "detail": "Uploaded file is corrupted or could not be decoded as a valid image."
}
```

##### `413 Request Entity Too Large` — File Size Exceeded
```json
{
  "detail": "File size exceeds the maximum limit of 10 MB."
}
```

##### `415 Unsupported Media Type` — Unsupported Format
```json
{
  "detail": "Unsupported file format 'application/pdf'. Allowed formats: image/jpeg, image/png, image/webp."
}
```

---

## 3. Chest X-Ray Analysis Endpoint

### `POST /api/v1/chest-xray/analyze`

Uploads a chest radiograph (CXR) for validation and session registration.

#### Request Specifications
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `file`: Binary file upload (Required)
- **Constraints**:
  - Formats: `image/jpeg`, `image/png`, `image/webp`
  - Max Size: `10 MB` (10,485,760 bytes)

#### Success Response: `200 OK` (Development Placeholder)
```json
{
  "session_id": "d7e1932f-a392-4f11-8be5-6184a441e93a",
  "modality": "chest_xray",
  "status": "DEVELOPMENT_PLACEHOLDER",
  "message": "Chest X-Ray model pipeline is not implemented yet. File successfully received and validated.",
  "model_version": "chest_xray_v0.1_dev_placeholder",
  "metadata": {
    "file_name": "cxr_sample.png",
    "file_size_bytes": 2097152,
    "mime_type": "image/png",
    "image_width": 1024,
    "image_height": 1024,
    "file_hash": "c85b1a774b971a82efd978a63be36e7fd29b71f9cf7d953a992451f0f7f3f317"
  },
  "prediction": null,
  "explanation": null,
  "disclaimer": "RESEARCH ONLY: Not for clinical or diagnostic use. Never use placeholder responses for patient decisions.",
  "created_at": "2026-10-16T11:15:35.789012Z"
}
```

#### Error Responses
Identical validation specifications as the retina endpoint (`400`, `413`, `415`).

---

## 4. MedAssist Health-Education Chat Endpoints

### `GET /api/v1/chat/status`

Returns the operational readiness, primary provider, model, and fallback configuration of the MedAssist conversational assistant.

#### Success Response: `200 OK`
```json
{
  "status": "ready",
  "provider": "gemini",
  "model": "gemini-3.5-flash",
  "is_configured": true,
  "fallback_configured": false,
  "fallback_provider": null,
  "disclaimer": "EDUCATIONAL RESEARCH USE ONLY: Not a clinical diagnosis, medical directive, or treatment plan."
}
```

---

### `POST /api/v1/chat/message`

Sends a health-education query to MedAssist with bounded conversational history.

#### Request Specifications
- **Content-Type**: `application/json`
- **Body Schema**:
  - `message`: string (1–1000 characters, required)
  - `conversation_history`: list of `ChatMessage` (max 20 items, role "user"|"assistant", content max 15000 characters)
  - `scan_context`: optional non-identifiable scan metadata

#### Success Response: `200 OK`
```json
{
  "message": "Ischemic heart disease involves narrowed coronary arteries reducing blood flow to the heart...",
  "provider": "gemini",
  "model": "gemini-3.5-flash",
  "fallback_used": false,
  "disclaimer": "EDUCATIONAL RESEARCH USE ONLY: Not a clinical diagnosis, medical directive, or treatment plan. Always consult a qualified physician or eye-care specialist for personal health concerns or urgent symptoms.",
  "created_at": "2026-10-21T01:30:00Z"
}
```

#### Error Responses

##### `429 Too Many Requests` — Upstream Quota Exhausted
Returned when provider daily/plan quota is exhausted and no fallback is configured, or both providers' quotas are exhausted.
```json
{
  "detail": "MedAssist AI provider (gemini) quota exceeded (HTTP 429). The upstream plan or daily request limit has been exhausted. Please verify API plan and billing details, or configure a fallback provider (OPENAI_API_KEY) in the backend. (Provider quota resets in approximately 10.8h)."
}
```

##### `503 Service Unavailable` — High Provider Demand or Unconfigured
Returned when the provider is unconfigured or temporarily unavailable due to upstream capacity overload after bounded retries.
```json
{
  "detail": "MedAssist AI provider is temporarily unavailable due to high demand. Please try again in a moment."
}
```

##### `422 Unprocessable Content` — Input Validation Error
Returned when the message or history exceeds length bounds or contains malformed data.
```json
{
  "detail": "conversation_history -> 0 -> role: Input should be 'user' or 'assistant'"
}
```

