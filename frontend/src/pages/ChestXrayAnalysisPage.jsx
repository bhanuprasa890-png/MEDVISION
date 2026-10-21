import React, { useEffect, useState } from "react";
import { Activity, AlertTriangle, CheckCircle2, Loader2, Send } from "lucide-react";
import { useImageUpload } from "../hooks/useImageUpload";
import { getChestXrayModelStatus, predictChestXray } from "../services/api";
import { ImageUploader } from "../components/ImageUploader";
import { AnalysisResultCard } from "../components/AnalysisResultCard";
import { ChestXrayResultCard } from "../components/ChestXrayResultCard";
import { useLanguage } from "../context/LanguageContext";
import { getTranslation } from "../i18n/translations";

export function ChestXrayAnalysisPage() {
  const { language } = useLanguage();
  const [modelStatus, setModelStatus] = useState(null);
  const [isStatusLoading, setIsStatusLoading] = useState(true);

  const t = (key) => getTranslation("chestXray", key, language);

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

  useEffect(() => {
    let isMounted = true;
    async function checkModelStatus() {
      try {
        const statusData = await getChestXrayModelStatus();
        if (isMounted) {
          setModelStatus(statusData);
        }
      } catch (err) {
        if (isMounted) {
          setModelStatus({ status: "UNAVAILABLE", model_name: "DenseNet-121" });
        }
      } finally {
        if (isMounted) {
          setIsStatusLoading(false);
        }
      }
    }
    checkModelStatus();
    return () => {
      isMounted = false;
    };
  }, []);

  const isModelLoaded = modelStatus?.status === "LOADED";

  const handleStartAnalysis = () => {
    uploadAndAnalyze(predictChestXray);
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      {/* Module Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
          <div className="inline-flex items-center space-x-2 text-teal-400 text-xs font-semibold uppercase tracking-wider">
            <Activity className="w-4 h-4" />
            <span>Pulmonology & Radiology Research Pipeline</span>
          </div>

          {/* Dynamic Model Availability Badge */}
          {isModelLoaded ? (
            <div className="inline-flex items-center space-x-2 text-xs px-3 py-1 rounded-full border bg-slate-900 border-emerald-500/30 self-start sm:self-auto">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-emerald-300 font-medium">
                {t("badgeActive")}
              </span>
            </div>
          ) : (
            <div className="inline-flex items-center space-x-2 text-xs px-3 py-1 rounded-full border bg-slate-900 border-amber-500/30 self-start sm:self-auto">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              <span className="text-amber-300 font-medium">
                {t("badgeUnavailable")}
              </span>
            </div>
          )}
        </div>

        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          {t("title")}
        </h1>
        <p className="text-sm text-slate-400 mt-2 leading-relaxed">
          {t("subtitle")}
        </p>

        {/* Model Pipeline Notice Banner */}
        {isModelLoaded ? (
          <div className="mt-3 flex items-start space-x-2 px-3 py-1.5 rounded-lg bg-teal-500/10 border border-teal-500/30 text-[11px] text-teal-300">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5 text-teal-400" />
            <span>
              <strong>DenseNet-121 Active:</strong> Pretrained model is loaded and ready. Uploaded chest radiographs will be evaluated across 18 thoracic pathologies with aligned Grad-CAM visual heatmaps.
            </span>
          </div>
        ) : (
          <div className="mt-3 flex items-start space-x-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-[11px] text-amber-300">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>
              <strong>Model Pipeline Standby:</strong> Initializing neural weights. Scans will undergo validation; please verify service readiness.
            </span>
          </div>
        )}
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
          modalityLabel="Chest Radiograph (CXR)"
        />

        {selectedFile && !result && (
          <div className="mt-6 flex justify-end">
            <button
              onClick={handleStartAnalysis}
              disabled={isLoading}
              className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-medium shadow-lg shadow-teal-500/20 transition-all cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{t("analyzing")}</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>{t("startAnalysis")}</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Results Presentation: Real Inference vs Development Placeholder */}
        {result?.prediction ? (
          <ChestXrayResultCard
            result={result}
            originalPreviewUrl={previewUrl}
            onReset={reset}
          />
        ) : (
          <AnalysisResultCard result={result} onReset={reset} />
        )}
      </div>
    </div>
  );
}
