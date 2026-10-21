import React from "react";
import { Eye, Activity, ShieldCheck, ArrowRight, MessageSquare } from "lucide-react";

export function HomePage({ setActiveTab }) {
  return (
    <div className="space-y-12 py-6">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 p-8 sm:p-12 text-center">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/10 text-teal-400 text-xs font-semibold mb-6 border border-teal-500/20">
          <ShieldCheck className="w-4 h-4" />
          <span>Hackathon Milestone: Core Architecture Separation</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight max-w-3xl mx-auto leading-tight">
          Explainable Medical Imaging <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-teal-400 to-cyan-400 bg-clip-text text-transparent">
            Research Assistant
          </span>
        </h1>

        <p className="mt-4 text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
          MedVision AI decouples frontend client interfaces, backend REST validation, relational audit tracking, and machine learning pipelines with zero patient health information persistence.
        </p>

        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <button
            onClick={() => setActiveTab("retina")}
            className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-medium shadow-lg shadow-teal-500/20 transition-all cursor-pointer"
          >
            <Eye className="w-5 h-5" />
            <span>Retinal Module</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={() => setActiveTab("chest-xray")}
            className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium border border-slate-700 transition-all cursor-pointer"
          >
            <Activity className="w-5 h-5" />
            <span>Chest X-Ray Module</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={() => setActiveTab("medassist")}
            className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-teal-400 font-medium border border-teal-500/30 transition-all cursor-pointer"
          >
            <MessageSquare className="w-5 h-5" />
            <span>MedAssist AI</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

