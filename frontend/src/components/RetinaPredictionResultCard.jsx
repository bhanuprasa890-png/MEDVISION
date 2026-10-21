import React, { useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock,
  Eye,
  FileText,
  Hash,
  Info,
  Layers,
  Sparkles,
  MessageSquare,
} from "lucide-react";
import { PatientFriendlyExplanation } from "./PatientFriendlyExplanation";

/**
 * Visual styling configuration for Diabetic Retinopathy clinical grades.
 */
const CLASS_STYLE_MAP = {
  0: {
    badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
    bar: "bg-emerald-500",
    text: "text-emerald-400",
  },
  1: {
    badge: "bg-yellow-500/20 text-yellow-300 border-yellow-500/40",
    bar: "bg-yellow-500",
    text: "text-yellow-400",
  },
  2: {
    badge: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    bar: "bg-amber-500",
    text: "text-amber-400",
  },
  3: {
    badge: "bg-orange-500/20 text-orange-300 border-orange-500/40",
    bar: "bg-orange-500",
    text: "text-orange-400",
  },
  4: {
    badge: "bg-rose-500/20 text-rose-300 border-rose-500/40",
    bar: "bg-rose-500",
    text: "text-rose-400",
  },
};

const CLASS_DESCRIPTIONS = {
  0: "No Diabetic Retinopathy (No DR)",
  1: "Mild Non-Proliferative DR (Mild NPDR)",
  2: "Moderate Non-Proliferative DR (Moderate NPDR)",
  3: "Severe Non-Proliferative DR (Severe NPDR)",
  4: "Proliferative Diabetic Retinopathy (PDR)",
};

export function RetinaPredictionResultCard({ result, originalPreviewUrl, onReset, onAskMedAssist }) {
  if (!result) return null;

  const [activeVisualMode, setActiveVisualMode] = useState("overlay"); // 'overlay' | 'raw' | 'original'

  const prediction = result.prediction;
  const explanation = result.explanation;
  const metadata = result.metadata;

  const predClass = prediction?.predicted_class ?? 0;
  const classStyle = CLASS_STYLE_MAP[predClass] || CLASS_STYLE_MAP[0];
  const confidencePercent = ((prediction?.confidence_score ?? 0) * 100).toFixed(1);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mt-6 shadow-2xl animate-fadeIn">
      {/* 1. Header & Status Banner */}
      <div className="p-4 bg-teal-500/10 border border-teal-500/30 rounded-xl mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-start space-x-3">
          <CheckCircle2 className="w-5 h-5 text-teal-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="flex items-center space-x-2">
              <h4 className="text-sm font-semibold text-teal-300">
                RetinaGuard Neural Classification Completed
              </h4>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-teal-400/20 text-teal-300">
                {result.status || "SUCCESS"}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              Architecture: <span className="font-mono text-teal-300">{result.model_version}</span> | Transfer Learning ResNet-18
            </p>
          </div>
        </div>
        <div className="text-xs text-slate-400 flex items-center space-x-1 sm:self-center">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span>{result.created_at ? new Date(result.created_at).toLocaleTimeString() : "Just now"}</span>
        </div>
      </div>

      {/* 2. Primary Classification Results Card */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 mb-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Predicted Diabetic Retinopathy Category
            </span>
            <div className="flex items-center space-x-3 mt-1.5">
              <span className={`text-xl sm:text-2xl font-bold tracking-tight ${classStyle.text}`}>
                {prediction?.class_label || "Classification Unavailable"}
              </span>
              <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${classStyle.badge}`}>
                Grade {predClass} • {prediction?.severity_level}
              </span>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 min-w-[200px]">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Model Output Score:</span>
              <span className="text-base font-bold text-white font-mono">{confidencePercent}%</span>
            </div>
            <p className="text-[10px] text-amber-400/90 mt-1 leading-tight flex items-start space-x-1">
              <AlertTriangle className="w-3 h-3 flex-shrink-0 mt-0.5" />
              <span>Uncalibrated model score, not a true clinical probability.</span>
            </p>
          </div>
        </div>

        {/* Clinical Category Description */}
        {prediction?.clinical_description && (
          <div className="mt-4 p-3 bg-slate-900/60 rounded-lg border border-slate-800/60 text-xs text-slate-300 flex items-start space-x-2">
            <Info className="w-4 h-4 text-teal-400 flex-shrink-0 mt-0.5" />
            <div className="leading-relaxed">
              <span className="font-semibold text-slate-200">Clinical Overview: </span>
              {prediction.clinical_description}
            </div>
          </div>
        )}

        {/* 3. Five-Class Score Distribution Bars */}
        {prediction?.all_class_scores && (
          <div className="mt-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                <BarChart3 className="w-3.5 h-3.5 text-teal-400" />
                <span>Multi-Class Score Distribution (5 Grades)</span>
              </span>
              <span className="text-[10px] text-slate-500">Softmax Activation Spread</span>
            </div>

            <div className="space-y-2">
              {[0, 1, 2, 3, 4].map((clsIdx) => {
                const score = prediction.all_class_scores[String(clsIdx)] ?? 0;
                const pct = (score * 100).toFixed(1);
                const isTop = clsIdx === predClass;
                const style = CLASS_STYLE_MAP[clsIdx];

                return (
                  <div key={clsIdx} className="text-xs">
                    <div className="flex justify-between items-center mb-1 text-[11px]">
                      <span className={`${isTop ? "font-bold text-white" : "text-slate-400"}`}>
                        Class {clsIdx}: {CLASS_DESCRIPTIONS[clsIdx]}
                      </span>
                      <span className={`font-mono ${isTop ? "font-bold text-teal-300" : "text-slate-400"}`}>
                        {pct}% ({score.toFixed(4)})
                      </span>
                    </div>
                    <div
                      role="progressbar"
                      aria-valuenow={Math.round(Number(pct))}
                      aria-valuemin="0"
                      aria-valuemax="100"
                      aria-label={`Class ${clsIdx} score: ${pct}%`}
                      className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden"
                    >
                      <div
                        className={`h-full rounded-full transition-all duration-500 motion-reduce:transition-none ${
                          isTop ? style.bar : "bg-slate-600"
                        }`}
                        style={{ width: `${Math.max(Number(pct), 1)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 4. Grad-CAM Visual Explainability Section */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
          <div>
            <h5 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Layers className="w-4 h-4 text-teal-400" />
              <span>Grad-CAM Visual Attribution Heatmap</span>
            </h5>
            <p className="text-xs text-slate-400 mt-0.5">
              Target Layer: <span className="font-mono text-teal-400">{explanation?.target_layer || "layer4"}</span> | Explaining Grade {explanation?.target_class ?? predClass}
            </p>
          </div>

          {/* Visual Mode Selector */}
          {explanation && (
            <div
              role="tablist"
              aria-label="Visual attribution display mode"
              className="inline-flex rounded-lg bg-slate-900 p-1 border border-slate-800 self-start sm:self-auto text-xs"
            >
              <button
                role="tab"
                aria-selected={activeVisualMode === "overlay"}
                onClick={() => setActiveVisualMode("overlay")}
                className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                  activeVisualMode === "overlay"
                    ? "bg-teal-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Blended Overlay
              </button>
              <button
                role="tab"
                aria-selected={activeVisualMode === "raw"}
                onClick={() => setActiveVisualMode("raw")}
                className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                  activeVisualMode === "raw"
                    ? "bg-teal-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Raw Heatmap
              </button>
              {originalPreviewUrl && (
                <button
                  role="tab"
                  aria-selected={activeVisualMode === "original"}
                  onClick={() => setActiveVisualMode("original")}
                  className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                    activeVisualMode === "original"
                      ? "bg-teal-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Original Scan
                </button>
              )}
            </div>
          )}
        </div>

        {/* Visualizer Display Box */}
        {explanation ? (
          <div className="mt-5 grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
            {/* Image Canvas */}
            <div className="md:col-span-7 flex justify-center bg-black/40 rounded-xl p-3 border border-slate-800/80">
              <div className="relative max-w-[340px] aspect-square rounded-lg overflow-hidden shadow-2xl bg-black">
                {activeVisualMode === "overlay" && (
                  <img
                    src={explanation.heatmap_overlay_base64}
                    alt="Grad-CAM Blended Heatmap Overlay on Retinal Fundus Scan"
                    className="w-full h-full object-cover transition-opacity duration-300"
                  />
                )}
                {activeVisualMode === "raw" && (
                  <img
                    src={explanation.raw_heatmap_base64}
                    alt="Grad-CAM Raw Heatmap Colorized with Jet Palette"
                    className="w-full h-full object-cover transition-opacity duration-300"
                  />
                )}
                {activeVisualMode === "original" && originalPreviewUrl && (
                  <img
                    src={originalPreviewUrl}
                    alt="Original Uploaded Retinal Fundus Photograph"
                    className="w-full h-full object-cover transition-opacity duration-300"
                  />
                )}
              </div>
            </div>

            {/* Salient Attention Telemetry */}
            <div className="md:col-span-5 space-y-3 text-xs">
              <h6 className="font-semibold text-slate-200 text-xs uppercase tracking-wider flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5 text-teal-400" />
                <span>Salient Attention Telemetry</span>
              </h6>

              <div className="space-y-2 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/60">
                <div className="flex justify-between">
                  <span className="text-slate-400">Peak Focus Coordinate:</span>
                  <span className="font-mono text-slate-200">
                    X: {explanation.salient_region_summary?.peak_x ?? "N/A"}, Y:{" "}
                    {explanation.salient_region_summary?.peak_y ?? "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Peak Attention Intensity:</span>
                  <span className="font-mono text-teal-300">
                    {explanation.salient_region_summary?.peak_intensity ?? "1.0000"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Mean Feature Activation:</span>
                  <span className="font-mono text-slate-200">
                    {explanation.salient_region_summary?.mean_intensity ?? "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Salient Area Ratio (&gt;50%):</span>
                  <span className="font-mono text-slate-200">
                    {explanation.salient_region_summary?.active_area_ratio !== undefined
                      ? `${(explanation.salient_region_summary.active_area_ratio * 100).toFixed(1)}%`
                      : "N/A"}
                  </span>
                </div>
              </div>

              {/* Jet Colormap Legend */}
              <div className="pt-1">
                <span className="text-[11px] text-slate-400 block mb-1">Grad-CAM Jet Colormap Scale:</span>
                <div className="h-3 w-full rounded bg-gradient-to-r from-blue-600 via-cyan-400 via-green-400 via-yellow-400 to-red-600 border border-slate-700" />
                <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                  <span>Low Influence (0.0)</span>
                  <span>Moderate (0.5)</span>
                  <span>Peak Attention (1.0)</span>
                </div>
              </div>

              {/* Interpretability Note */}
              <p className="text-[11px] text-slate-400 leading-relaxed bg-slate-900/40 p-2.5 rounded-lg border border-slate-800/40">
                <strong className="text-slate-300">Interpretability Notice: </strong>
                {explanation.interpretability_note}
              </p>
            </div>
          </div>
        ) : (
          <div className="p-4 bg-slate-900/60 rounded-lg text-center text-xs text-slate-400 mt-4 border border-slate-800">
            Grad-CAM heatmap visual attribution was not generated for this inference run.
          </div>
        )}
      </div>

      {/* 5. Understand Your Result (Patient-Friendly & Plain Language Guidance) */}
      <PatientFriendlyExplanation prediction={prediction} explanation={explanation} />

      {/* 6. Session Audit Ledger & In-Memory Technical Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 text-xs">
          <h5 className="font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
            <FileText className="w-3.5 h-3.5 text-teal-400" />
            <span>Audit Session Record</span>
          </h5>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="text-slate-500">Session ID:</dt>
              <dd className="font-mono text-slate-200 select-all text-[11px] truncate max-w-[200px]" title={result.session_id}>
                {result.session_id}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Modality:</dt>
              <dd className="font-medium text-teal-400 uppercase text-[11px]">{result.modality}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Model Pipeline:</dt>
              <dd className="font-mono text-slate-300 text-[11px]">{result.model_version}</dd>
            </div>
          </dl>
        </div>

        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 text-xs">
          <h5 className="font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
            <Hash className="w-3.5 h-3.5 text-teal-400" />
            <span>Technical Image Attributes</span>
          </h5>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="text-slate-500">Input Resolution:</dt>
              <dd className="font-mono text-slate-200">
                {metadata?.image_width} × {metadata?.image_height} px
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">File Size:</dt>
              <dd className="text-slate-200">
                {metadata?.file_size_bytes ? (metadata.file_size_bytes / 1024).toFixed(1) : 0} KB
              </dd>
            </div>
            <div className="flex justify-between items-center">
              <dt className="text-slate-500">SHA-256 Digest:</dt>
              <dd className="font-mono text-slate-400 text-[10px] truncate max-w-[170px]" title={metadata?.file_hash}>
                {metadata?.file_hash ? `${metadata.file_hash.substring(0, 16)}...` : "N/A"}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/* 6. Clinical Guidance & Diagnostic Boundaries */}
      <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 mb-4 text-xs space-y-2">
        <h5 className="font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
          <Info className="w-3.5 h-3.5 text-teal-400" />
          <span>Clinical Consultation Guidance &amp; Diagnostic Boundaries</span>
        </h5>
        <p className="text-slate-300 leading-relaxed">
          This AI model output represents an experimental pattern classification across 5 Diabetic Retinopathy grades. It is <strong>not a clinical diagnosis</strong>. Softmax confidence reflects model activation spread and must not be interpreted as calibrated epidemiological risk.
        </p>
        <div className="text-slate-400 leading-relaxed space-y-1 pt-1">
          <div className="flex items-start space-x-2">
            <span className="text-teal-400 font-bold">•</span>
            <span>
              <strong>Professional Examination Required:</strong> Definitive evaluation of diabetic eye disease requires a comprehensive dilated ophthalmic exam by a licensed ophthalmologist or optometrist.
            </span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="text-teal-400 font-bold">•</span>
            <span>
              <strong>Supported Scope:</strong> RetinaGuard evaluates Diabetic Retinopathy severity only and does not detect or rule out other eye conditions (glaucoma, macular degeneration) or systemic diseases.
            </span>
          </div>
        </div>
      </div>

      {/* 7. Mandatory Medical Research Disclaimer */}
      <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl mb-6 text-xs text-rose-300 flex items-start space-x-2.5">
        <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-bold text-rose-200">Medical Research Prototype Notice: </span>
          {result.disclaimer ||
            "This software is an educational research prototype. It is not certified as a medical device and must never be used for actual clinical diagnosis, patient screening, or treatment selection."}
        </div>
      </div>

      {/* 7. Actions: Ask MedAssist & Reset */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
        {onAskMedAssist && (
          <button
            onClick={() => {
              const scanContext = {
                modality: "retina",
                predicted_class: prediction?.predicted_class ?? null,
                class_label: prediction?.class_label ?? null,
                severity_level: prediction?.severity_level ?? null,
                model_version: result?.model_version ?? null,
                confidence_score: prediction?.confidence_score ?? null,
                all_class_scores: prediction?.all_class_scores ?? null,
                session_id: result?.session_id ?? null,
              };
              onAskMedAssist(scanContext);
            }}
            className="inline-flex items-center justify-center space-x-2 px-5 py-2.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-500 rounded-xl transition-all cursor-pointer shadow-lg shadow-teal-500/20"
          >
            <MessageSquare className="w-4 h-4" />
            <span>Ask MedAssist About This Result</span>
          </button>
        )}
        <button
          onClick={onReset}
          className="px-5 py-2.5 text-xs font-semibold text-slate-200 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition-all cursor-pointer shadow-md text-center"
        >
          Analyze Another Retinal Fundus Scan
        </button>
      </div>
    </div>
  );
}
