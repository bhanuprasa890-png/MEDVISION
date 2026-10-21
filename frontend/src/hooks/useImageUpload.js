import { useState, useCallback } from "react";

const MAX_SIZE_MB = 10;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];

/**
 * Custom React hook managing medical image file selection, client-side validation,
 * upload state, and analysis placeholder responses.
 */
export function useImageUpload() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const reset = useCallback(() => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setIsLoading(false);
    setError(null);
    setResult(null);
  }, [previewUrl]);

  const handleFileSelect = useCallback((file) => {
    setError(null);
    setResult(null);

    if (!file) {
      return;
    }

    // Client-side format validation
    if (!ALLOWED_TYPES.includes(file.type)) {
      setError(
        `Unsupported file type (${file.type || "unknown"}). Please select a JPEG, PNG, or WebP image.`
      );
      return;
    }

    // Client-side size validation
    if (file.size > MAX_SIZE_BYTES) {
      setError(
        `File is too large (${(file.size / (1024 * 1024)).toFixed(2)} MB). Maximum allowed size is ${MAX_SIZE_MB} MB.`
      );
      return;
    }

    if (file.size === 0) {
      setError("The selected file is empty (0 bytes).");
      return;
    }

    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
  }, []);

  const uploadAndAnalyze = useCallback(
    async (analysisFn) => {
      if (!selectedFile) {
        setError("Please choose an image file before requesting analysis.");
        return;
      }
      if (isLoading) {
        return; // Guard against duplicate submissions
      }

      setIsLoading(true);
      setError(null);
      setResult(null);

      try {
        const responseData = await analysisFn(selectedFile);
        setResult(responseData);
      } catch (err) {
        setError(err.message || "An unexpected error occurred while communicating with the backend.");
      } finally {
        setIsLoading(false);
      }
    },
    [selectedFile, isLoading]
  );

  return {
    selectedFile,
    previewUrl,
    isLoading,
    error,
    result,
    handleFileSelect,
    uploadAndAnalyze,
    reset,
  };
}

export { ALLOWED_TYPES, MAX_SIZE_MB, MAX_SIZE_BYTES };

