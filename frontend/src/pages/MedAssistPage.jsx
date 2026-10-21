import React, { useState, useEffect } from "react";
import {
  MessageSquare,
  ShieldCheck,
  BookOpen,
  AlertTriangle,
} from "lucide-react";
import { MedAssistChatPanel } from "../components/MedAssistChatPanel";
import { getChatStatus } from "../services/api";

export function MedAssistPage({ activeScanContext = null, onClearScanContext = null }) {
  const [chatStatus, setChatStatus] = useState(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(true);

  const fetchStatus = async () => {
    try {
      setIsLoadingStatus(true);
      const statusData = await getChatStatus();
      setChatStatus(statusData);
    } catch (err) {
      console.warn("Unable to fetch MedAssist status:", err);
      setChatStatus({
        status: "unconfigured",
        provider: "none",
        model: "unconfigured",
        is_configured: false,
      });
    } finally {
      setIsLoadingStatus(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div className="space-y-8 py-6 max-w-6xl mx-auto">
      {/* 1. Header & Context */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-teal-500/10 text-teal-400 border border-teal-500/20">
              Conversational Engine
            </span>
            <span className="text-xs text-slate-400 font-medium">Health Education</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center space-x-3">
            <MessageSquare className="w-7 h-7 text-teal-400" />
            <span>MedAssist Health-Education Assistant</span>
          </h1>
          <p className="mt-1 text-sm text-slate-400 max-w-2xl">
            Interactive, grounded AI education for medical imaging terminology, diabetic
            retinopathy classifications, and explainability mechanisms.
          </p>
        </div>

        {/* Provider Readiness Badge */}
        <div className="flex items-center space-x-3 bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-2xl shadow-sm flex-shrink-0">
          <div
            className={`w-3 h-3 rounded-full ${
              chatStatus?.is_configured
                ? "bg-emerald-400 animate-pulse"
                : "bg-amber-400"
            }`}
          />
          <div>
            <div className="text-[11px] font-semibold text-slate-300">
              {isLoadingStatus
                ? "Checking status..."
                : chatStatus?.is_configured
                ? "AI Assistant: Ready"
                : "AI Assistant: Standby"}
            </div>
            <div className="text-[10px] text-slate-500">
              {chatStatus?.is_configured
                ? `Active model: ${chatStatus.model}`
                : "Educational service standby"}
            </div>
          </div>
        </div>
      </div>

      {/* 2. Main Chat Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Chat Interface */}
        <div className="lg:col-span-2">
          <MedAssistChatPanel
            chatStatus={chatStatus}
            onRefreshStatus={fetchStatus}
            activeScanContext={activeScanContext}
            onClearScanContext={onClearScanContext}
          />
        </div>

        {/* Right Column: Educational Scope & Safety Pillars */}
        <div className="space-y-6">
          {/* Guide Card 1: What MedAssist Does */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center space-x-2 text-teal-400">
              <BookOpen className="w-4 h-4" />
              <h3 className="text-sm font-bold text-white">What You Can Ask</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              MedAssist explains imaging and medical concepts in clear, patient-friendly language:
            </p>
            <ul className="text-xs text-slate-400 space-y-2">
              <li className="flex items-start space-x-2">
                <span className="text-teal-400 font-bold">•</span>
                <span>
                  <strong className="text-slate-300">Retinal & Chest Scan Findings:</strong> Understand what grading categories, severity levels, and clinical classifications mean.
                </span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-teal-400 font-bold">•</span>
                <span>
                  <strong className="text-slate-300">AI Heatmaps (Grad-CAM):</strong> Learn what highlighted image regions indicate, and what heatmaps cannot prove.
                </span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-teal-400 font-bold">•</span>
                <span>
                  <strong className="text-slate-300">Model Scores & Limits:</strong> Understand how confidence scores work and why in-person clinical exams are essential.
                </span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-teal-400 font-bold">•</span>
                <span>
                  <strong className="text-slate-300">General Health Topics:</strong> Ask about diabetes eye health, cardiovascular risks, or common terminology.
                </span>
              </li>
            </ul>
          </div>

          {/* Guide Card 2: Medical Safety Boundaries */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center space-x-2 text-amber-400">
              <AlertTriangle className="w-4 h-4" />
              <h3 className="text-sm font-bold text-white">Ethical Safety Guardrails</h3>
            </div>
            <ul className="text-xs text-slate-400 space-y-2 leading-relaxed">
              <li className="flex items-start space-x-2">
                <span className="text-rose-400 font-bold">•</span>
                <span>
                  <strong className="text-slate-300">Non-Diagnostic:</strong> Informational only; does not diagnose conditions or replace evaluation by a licensed healthcare professional.
                </span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-rose-400 font-bold">•</span>
                <span>
                  <strong className="text-slate-300">No Prescriptions:</strong> Cannot recommend medications, dosages, or specific treatment plans.
                </span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-amber-400 font-bold">•</span>
                <span>
                  <strong className="text-slate-300">Urgent Symptoms:</strong> For sudden vision loss, acute eye pain, or severe symptoms, seek emergency professional medical care immediately.
                </span>
              </li>
            </ul>
          </div>

          {/* Guide Card 3: Privacy by Architecture */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center space-x-2 text-cyan-400">
              <ShieldCheck className="w-4 h-4" />
              <h3 className="text-sm font-bold text-white">Privacy by Architecture</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Designed with privacy-first data handling:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 text-[11px]">
              <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                <div className="font-semibold text-slate-300 mb-0.5">Ephemeral Session</div>
                <div className="text-slate-500 text-[10px]">Active browser tab only; clears on refresh</div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                <div className="font-semibold text-slate-300 mb-0.5">No Chat Persistence</div>
                <div className="text-slate-500 text-[10px]">Conversations are not saved to database or logs</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

