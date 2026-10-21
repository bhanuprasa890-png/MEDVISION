import React from "react";
import { CheckCircle2, Info, Hash, Clock, FileText, EyeOff, Layers } from "lucide-react";

export function AnalysisResultCard({ result, onReset }) {
  if (!result) return null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mt-6 shadow-xl animate-fadeIn">
      {/* Development Status Banner */}
      <div className="p-4 bg-teal-500/10 border border-teal-500/30 rounded-xl mb-6 flex items-start space-x-3">
        <CheckCircle2 className="w-5 h-5 text-teal-400 flex-shrink-0 mt-0.5" />
        <div>
          <div className="flex items-center space-x-2">
            <h4 className="text-sm font-semibold text-teal-300">
              Pipeline Validation Succeeded
            </h4>
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-teal-400/20 text-teal-300">
              {result.status}
            </span>
          </div>
          <p className="text-xs text-slate-300 mt-1 leading-relaxed">
            {result.message}
          </p>
        </div>
      </div>

      {/* Grid: Session Info & Technical Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Session Ledger Card */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80">
          <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
            <FileText className="w-3.5 h-3.5 text-teal-400" />
            <span>Anonymous Audit Session</span>
          </h5>

          <dl className="space-y-2 text-xs">
            <div className="flex justify-between">
              <dt className="text-slate-500">Session ID:</dt>
              <dd className="font-mono text-slate-200 select-all text-[11px] truncate max-w-[200px]" title={result.session_id}>
                {result.session_id}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Modality:</dt>
              <dd className="font-medium text-teal-400 uppercase text-[11px]">
                {result.modality}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Pipeline Version:</dt>
              <dd className="font-mono text-slate-300 text-[11px]">
                {result.model_version}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Timestamp:</dt>
              <dd className="text-slate-300 text-[11px] flex items-center space-x-1">
                <Clock className="w-3 h-3 text-slate-500" />
                <span>{new Date(result.created_at).toLocaleString()}</span>
              </dd>
            </div>
          </dl>
        </div>

        {/* In-Memory Technical Metadata */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80">
          <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
            <Hash className="w-3.5 h-3.5 text-teal-400" />
            <span>Technical Image Metadata</span>
          </h5>

          <dl className="space-y-2 text-xs">
            <div className="flex justify-between">
              <dt className="text-slate-500">Dimensions:</dt>
              <dd className="font-mono text-slate-200">
                {result.metadata?.image_width} × {result.metadata?.image_height} px
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">File Size:</dt>
              <dd className="text-slate-200">
                {(result.metadata?.file_size_bytes / 1024).toFixed(1)} KB
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">MIME Type:</dt>
              <dd className="font-mono text-slate-300 text-[11px]">
                {result.metadata?.mime_type}
              </dd>
            </div>
            <div className="flex justify-between items-center">
              <dt className="text-slate-500">SHA-256 Digest:</dt>
              <dd className="font-mono text-slate-400 text-[10px] truncate max-w-[170px]" title={result.metadata?.file_hash}>
                {result.metadata?.file_hash?.substring(0, 16)}...
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Model Output Placeholders - Honest & Transparent */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Prediction Card */}
        <div className="border border-slate-800 bg-slate-950/60 p-4 rounded-xl flex items-start space-x-3">
          <EyeOff className="w-5 h-5 text-slate-500 flex-shrink-0 mt-0.5" />
          <div>
            <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Inference Prediction
            </h5>
            <p className="text-xs text-slate-400 mt-1">
              Status: <span className="text-amber-400 font-medium">Not Available</span>
            </p>
            <p className="text-[11px] text-slate-500 mt-1">
              Deep learning weights are intentionally omitted during this initial architecture milestone. No clinical inference occurred.
            </p>
          </div>
        </div>

        {/* Explainability Card */}
        <div className="border border-slate-800 bg-slate-950/60 p-4 rounded-xl flex items-start space-x-3">
          <Layers className="w-5 h-5 text-slate-500 flex-shrink-0 mt-0.5" />
          <div>
            <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Visual Explainability (Grad-CAM)
            </h5>
            <p className="text-xs text-slate-400 mt-1">
              Heatmap: <span className="text-amber-400 font-medium">Pending Neural Integration</span>
            </p>
            <p className="text-[11px] text-slate-500 mt-1">
              Attribution heatmaps will be generated once gradient hooks are linked to model backbones.
            </p>
          </div>
        </div>
      </div>

      {/* Reset Action */}
      <div className="flex justify-end pt-2">
        <button
          onClick={onReset}
          className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
        >
          Analyze Another Scan
        </button>
      </div>
    </div>
  );
}
