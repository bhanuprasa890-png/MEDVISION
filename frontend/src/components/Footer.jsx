import React from "react";
import { AlertTriangle, Lock, FileText, Database } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-slate-800 bg-slate-950 mt-16 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mb-8 flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-amber-200/90 leading-relaxed">
            <strong className="font-semibold text-amber-300">
              Mandatory Research Protocol Disclaimer:
            </strong>{" "}
            MedVision AI is an exploratory research testbed developed for hackathon benchmarking.
            It is not FDA approved, CE marked, or clinically certified. Never use this system or its placeholder responses
            for real clinical patient diagnoses, treatment planning, or medical decisions.
          </div>
        </div>

        <div className="flex flex-col md:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <Lock className="w-3.5 h-3.5 text-slate-400" />
              <span>Zero PII Stored</span>
            </span>
            <span className="flex items-center space-x-1">
              <Database className="w-3.5 h-3.5 text-slate-400" />
              <span>SQLite Metadata Ledger</span>
            </span>
            <span className="flex items-center space-x-1">
              <FileText className="w-3.5 h-3.5 text-slate-400" />
              <span>FastAPI REST Contract</span>
            </span>
          </div>

          <div>
            MedVision AI Architecture Milestone • Strictly Separated Full-Stack System
          </div>
        </div>
      </div>
    </footer>
  );
}
