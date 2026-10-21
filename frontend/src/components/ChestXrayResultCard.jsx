import React, { useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock,
  FileText,
  Hash,
  Info,
  Layers,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { useLanguage } from "../context/LanguageContext";
import { getTranslation } from "../i18n/translations";
import { ChestXrayPatientExplanation } from "./ChestXrayPatientExplanation";

export function ChestXrayResultCard({ result, originalPreviewUrl, onReset }) {
  if (!result || !result.prediction) return null;

  const { language } = useLanguage();
  const [activeVisualMode, setActiveVisualMode] = useState("overlay"); // 'overlay' | 'raw' | 'original'
  const [showAllPathologies, setShowAllPathologies] = useState(false);

  const t = (key) => getTranslation("chestXray", key, language);

  const { prediction, explanation, metadata, session_id, model_version, created_at, disclaimer } = result;
  const topFinding = prediction.top_finding || "Unknown";
  const topScore = prediction.top_score ?? 0;
  const findings = prediction.findings || {};
  const findingsAboveThreshold = prediction.findings_above_threshold || [];

  // Localized pathology name lookup
  const getPathologyName = (path) => {
    const names = getTranslation("chestXray", "pathologyNames", language);
    if (names && typeof names === "object" && names[path]) {
      return names[path];
    }
    return path.replace(/_/g, " ");
  };

  const formattedDate = created_at
    ? new Date(created_at).toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : "Just now";

  return (
    <div className="mt-8 space-y-6" data-testid="chest-xray-result-card">
      {/* Top Header Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 to-slate-950 border border-slate-800 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-teal-400">
                  {t("title")}
                </span>
                <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Analyzed
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Model: <span className="font-mono text-slate-300">{model_version}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <Clock className="w-3.5 h-3.5" />
            <span>{formattedDate}</span>
          </div>
        </div>

        {/* Primary Finding Hero Card */}
        <div className="mt-6 p-6 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
                {t("topFinding")}
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-white mt-1">
                {getPathologyName(topFinding)}
              </h2>
              <p className="text-xs text-slate-400 mt-1 max-w-xl">
                {prediction.clinical_description}
              </p>
            </div>

            <div className="flex flex-col items-start md:items-end">
              <span className="text-xs text-slate-400">{t("topScore")}</span>
              <div className="text-3xl font-extrabold text-teal-400 font-mono">
                {(topScore * 100).toFixed(1)}%
              </div>
              <span className="text-[10px] text-slate-400 mt-0.5">Uncalibrated Sigmoid Activation</span>
            </div>
          </div>
        </div>

        {/* Technical Session Metadata */}
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs text-slate-400">
          <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/50">
            <span className="block text-[10px] uppercase text-slate-400">Session ID</span>
            <span className="font-mono text-slate-300 truncate block" title={session_id}>
              {session_id?.slice(0, 13)}...
            </span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/50">
            <span className="block text-[10px] uppercase text-slate-400">File Name</span>
            <span className="font-mono text-slate-300 truncate block" title={metadata?.file_name}>
              {metadata?.file_name || "radiograph.png"}
            </span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/50">
            <span className="block text-[10px] uppercase text-slate-400">Resolution</span>
            <span className="font-mono text-slate-300 block">
              {metadata?.image_width} × {metadata?.image_height}
            </span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/50">
            <span className="block text-[10px] uppercase text-slate-400">SHA-256 Digest</span>
            <span className="font-mono text-slate-300 truncate block" title={metadata?.file_hash}>
              {metadata?.file_hash ? `${metadata.file_hash.slice(0, 10)}...` : "—"}
            </span>
          </div>
        </div>
      </div>

      {/* Grad-CAM Explainability Section */}
      {explanation && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <h3 className="text-base font-semibold text-white tracking-tight">
                {t("explainability")}
              </h3>
            </div>

            {/* Visual Mode Selector Tabs */}
            <div
              role="tablist"
              aria-label="Radiograph visual inspection mode"
              className="inline-flex rounded-xl bg-slate-950 p-1 border border-slate-800 text-xs self-start sm:self-auto"
            >
              <button
                role="tab"
                id="tab-cxr-overlay"
                aria-selected={activeVisualMode === "overlay"}
                aria-controls="panel-cxr-visual"
                tabIndex={activeVisualMode === "overlay" ? 0 : -1}
                onClick={() => setActiveVisualMode("overlay")}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
                  activeVisualMode === "overlay"
                    ? "bg-teal-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {t("viewOverlay")}
              </button>
              <button
                role="tab"
                id="tab-cxr-raw"
                aria-selected={activeVisualMode === "raw"}
                aria-controls="panel-cxr-visual"
                tabIndex={activeVisualMode === "raw" ? 0 : -1}
                onClick={() => setActiveVisualMode("raw")}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
                  activeVisualMode === "raw"
                    ? "bg-teal-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {t("viewRawHeatmap")}
              </button>
              {originalPreviewUrl && (
                <button
                  role="tab"
                  id="tab-cxr-original"
                  aria-selected={activeVisualMode === "original"}
                  aria-controls="panel-cxr-visual"
                  tabIndex={activeVisualMode === "original" ? 0 : -1}
                  onClick={() => setActiveVisualMode("original")}
                  className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
                    activeVisualMode === "original"
                      ? "bg-teal-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  {t("viewOriginal")}
                </button>
              )}
            </div>
          </div>

          {/* Visual Display Canvas */}
          <div
            id="panel-cxr-visual"
            role="tabpanel"
            aria-labelledby={`tab-cxr-${activeVisualMode}`}
            className="flex flex-col md:flex-row items-center gap-6 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80"
          >
            <div className="relative flex justify-center items-center w-full md:w-80 h-80 bg-black/60 rounded-xl overflow-hidden border border-slate-800">
              {activeVisualMode === "overlay" && (
                <img
                  src={explanation.heatmap_overlay_base64}
                  alt={`Grad-CAM heatmap overlay for ${explanation.target_pathology}`}
                  className="max-h-full max-w-full object-contain"
                />
              )}
              {activeVisualMode === "raw" && (
                <img
                  src={explanation.raw_heatmap_base64}
                  alt={`Raw Grad-CAM colorized heatmap for ${explanation.target_pathology}`}
                  className="max-h-full max-w-full object-contain"
                />
              )}
              {activeVisualMode === "original" && originalPreviewUrl && (
                <img
                  src={originalPreviewUrl}
                  alt="Original input chest radiograph"
                  className="max-h-full max-w-full object-contain"
                />
              )}
            </div>

            {/* Heatmap Interpretability Metrics & Notes */}
            <div className="flex-1 space-y-4">
              <div>
                <span className="text-xs font-semibold text-slate-300">
                  Targeted Pathology: <span className="text-teal-400">{explanation.target_pathology}</span>
                </span>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  {explanation.interpretability_note}
                </p>
              </div>

              {explanation.salient_region_summary && (
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="block text-[10px] text-slate-400 uppercase">Peak Coordinates</span>
                    <span className="font-mono text-slate-300">
                      X: {explanation.salient_region_summary.peak_x}, Y: {explanation.salient_region_summary.peak_y}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="block text-[10px] text-slate-400 uppercase">Peak Intensity</span>
                    <span className="font-mono text-teal-400 font-semibold">
                      {(explanation.salient_region_summary.peak_intensity * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="block text-[10px] text-slate-400 uppercase">Active Area Ratio</span>
                    <span className="font-mono text-slate-300">
                      {(explanation.salient_region_summary.active_area_ratio * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="block text-[10px] text-slate-400 uppercase">Target Layer</span>
                    <span className="font-mono text-slate-300">{explanation.target_layer}</span>
                  </div>
                </div>
              )}

              {/* Color Bar Legend */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] text-slate-400">
                  <span>Baseline / Low Attention</span>
                  <span>Peak Model Attention</span>
                </div>
                <div className="h-2 rounded-full w-full bg-gradient-to-r from-blue-600 via-emerald-400 via-amber-400 to-rose-500" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Multi-label Pathologies Breakdown */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-teal-400" />
            <h3 className="text-base font-semibold text-white tracking-tight">
              {t("allPathologies")}
            </h3>
          </div>
          <button
            onClick={() => setShowAllPathologies(!showAllPathologies)}
            className="text-xs text-teal-400 hover:text-teal-300 font-medium cursor-pointer underline"
          >
            {showAllPathologies ? "Show Detected Only" : "Show All 18 Pathologies"}
          </button>
        </div>

        {/* Detected findings exceeding threshold */}
        <div className="mb-4">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2">
            {t("findingsAboveThreshold")}
          </span>
          {findingsAboveThreshold.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {findingsAboveThreshold.map((item) => (
                <div
                  key={item.name}
                  className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between"
                >
                  <div>
                    <span className="text-xs font-bold text-amber-300">
                      {getPathologyName(item.name)}
                    </span>
                    <span className="block text-[10px] text-slate-400">
                      Threshold: {(item.threshold * 100).toFixed(1)}%
                    </span>
                  </div>
                  <span className="text-sm font-extrabold font-mono text-amber-400">
                    {(item.score * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800 text-xs text-slate-400">
              {t("noneDetected")}
            </div>
          )}
        </div>

        {/* All 18 pathologies list */}
        {showAllPathologies && (
          <div className="mt-4 pt-4 border-t border-slate-800 space-y-3">
            {Object.entries(findings).map(([pathName, score]) => {
              const isTop = pathName === topFinding;
              const isDetected = findingsAboveThreshold.some((f) => f.name === pathName);
              return (
                <div key={pathName} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className={`font-medium ${isTop ? "text-teal-400 font-bold" : "text-slate-300"}`}>
                      {getPathologyName(pathName)}
                      {isTop && " ★ Top"}
                      {isDetected && " [Above Threshold]"}
                    </span>
                    <span className="font-mono text-slate-400">{(score * 100).toFixed(1)}%</span>
                  </div>
                  <div
                    role="progressbar"
                    aria-valuenow={Math.round(score * 100)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={`Model score for ${pathName}`}
                    className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden"
                  >
                    <div
                      className={`h-full transition-all duration-300 ${
                        isTop ? "bg-teal-500" : isDetected ? "bg-amber-500" : "bg-slate-600"
                      }`}
                      style={{ width: `${Math.min(100, Math.max(0, score * 100))}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Patient-Friendly Explanation & Educational Guidance */}
      <ChestXrayPatientExplanation
        prediction={prediction}
        explanation={explanation}
      />

      {/* Mandatory Non-Diagnostic Disclaimer */}
      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start space-x-3 text-xs text-amber-300">
        <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5 text-amber-400" />
        <div className="space-y-1">
          <p className="font-semibold">{t("disclaimer")}</p>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            {prediction.calibration_notice}
          </p>
        </div>
      </div>

      {/* Reset Action Button */}
      <div className="flex justify-end pt-2">
        <button
          onClick={onReset}
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium transition-all cursor-pointer"
        >
          <RotateCcw className="w-4 h-4" />
          <span>{t("reset")}</span>
        </button>
      </div>
    </div>
  );
}
