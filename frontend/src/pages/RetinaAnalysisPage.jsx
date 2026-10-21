import React, { useState, useEffect } from "react";
import { Eye, Loader2, Send, CheckCircle2, AlertCircle, Sparkles } from "lucide-react";
import { useImageUpload } from "../hooks/useImageUpload";
import { predictRetina, getRetinaModelStatus, analyzeRetina } from "../services/api";
import { ImageUploader } from "../components/ImageUploader";
import { AnalysisResultCard } from "../components/AnalysisResultCard";
import { RetinaPredictionResultCard } from "../components/RetinaPredictionResultCard";

export function RetinaAnalysisPage({ onAskMedAssist }) {
  const {
    selectedFile,
    previewUrl,
    isLoading,
    error,
    result,
    handleFileSelect,
    uploadAndAnalyze,
    reset,
  } = useImageUpload();

  const [includeGradcam, setIncludeGradcam] = useState(true);
  const [modelStatus, setModelStatus] = useState(null);
  const [isCheckingModel, setIsCheckingModel] = useState(true);

  // Check RetinaGuard model readiness on page load
  useEffect(() => {
    let isMounted = true;
    async function checkModel() {
      try {
        const status = await getRetinaModelStatus();
        if (isMounted) {
          setModelStatus(status);
        }
      } catch (err) {
        if (isMounted) {
          setModelStatus({ is_loaded: false, status: "OFFLINE", error: err.message });
        }
      } finally {
        if (isMounted) {
          setIsCheckingModel(false);
        }
      }
    }

    checkModel();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleStartAnalysis = () => {
    // Call the verified RetinaGuard predict endpoint with Grad-CAM option
    uploadAndAnalyze((file) => predictRetina(file, includeGradcam));
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      {/* Module Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
          <div className="inline-flex items-center space-x-2 text-teal-400 text-xs font-semibold uppercase tracking-wider">
            <Eye className="w-4 h-4" />
            <span>RetinaGuard • Ophthalmology AI Pipeline</span>
          </div>

          {/* Real-time Model Readiness Badge */}
          <div className="inline-flex items-center space-x-2 text-xs px-3 py-1 rounded-full border bg-slate-900 border-slate-800">
            {isCheckingModel ? (
              <>
                <Loader2 className="w-3 h-3 text-slate-400 animate-spin" />
                <span className="text-slate-400">Verifying Model Pipeline...</span>
              </>
            ) : modelStatus?.is_loaded ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-emerald-300 font-medium">
                  {modelStatus.model_version || "ResNet-18"} Ready ({modelStatus.device || "cpu"})
                </span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <span className="text-amber-300 font-medium">Model Offline / Standby</span>
              </>
            )}
          </div>
        </div>

        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Retinal Fundus Image Analysis
        </h1>
        <p className="text-sm text-slate-400 mt-2 leading-relaxed">
          Upload macula- or optic-disc-centered fundus photographs for 5-class Diabetic Retinopathy
          evaluation (Classes 0–4) paired with Grad-CAM saliency localization.
        </p>

        {/* Prototype Banner */}
        <div className="mt-3 inline-block px-3 py-1 rounded-lg bg-teal-500/10 border border-teal-500/20 text-[11px] text-teal-300">
          Research prototype only — not for diagnosis or clinical decision-making.
        </div>
      </div>

      {/* Upload & Inspection Canvas */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 sm:p-8 backdrop-blur">
        <ImageUploader
          selectedFile={selectedFile}
          previewUrl={previewUrl}
          error={error}
          isLoading={isLoading}
          onFileSelect={handleFileSelect}
          onReset={reset}
          modalityLabel="Retinal Fundus Photograph (JPEG, PNG, WebP)"
        />

        {selectedFile && !result && (
          <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-800/80">
            {/* Grad-CAM Toggle Option */}
            <label className="flex items-center space-x-2.5 text-xs text-slate-300 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={includeGradcam}
                onChange={(e) => setIncludeGradcam(e.target.checked)}
                disabled={isLoading}
                className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-teal-500 focus:ring-teal-400 focus:ring-offset-slate-900 cursor-pointer"
              />
              <span className="flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5 text-teal-400" />
                <span>Generate Grad-CAM visual attention heatmap</span>
              </span>
            </label>

            {/* Execute Analysis Action */}
            <button
              onClick={handleStartAnalysis}
              disabled={isLoading}
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-medium shadow-lg shadow-teal-500/20 transition-all cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Running ResNet-18 Inference &amp; Grad-CAM...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Run RetinaGuard Analysis</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Results Presentation: Dedicated RetinaGuard Prediction Result Card */}
        {result?.prediction ? (
          <RetinaPredictionResultCard
            result={result}
            originalPreviewUrl={previewUrl}
            onReset={reset}
            onAskMedAssist={onAskMedAssist}
          />
        ) : (
          <AnalysisResultCard result={result} onReset={reset} />
        )}
      </div>
    </div>
  );
}
