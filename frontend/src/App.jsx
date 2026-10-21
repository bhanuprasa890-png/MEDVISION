import React, { useState } from "react";
import { Header } from "./components/Header";
import { Footer } from "./components/Footer";
import { HomePage } from "./pages/HomePage";
import { RetinaAnalysisPage } from "./pages/RetinaAnalysisPage";
import { ChestXrayAnalysisPage } from "./pages/ChestXrayAnalysisPage";
import { MedAssistPage } from "./pages/MedAssistPage";
import { LanguageProvider } from "./context/LanguageContext";

export default function App() {
  const [activeTab, setActiveTab] = useState("home");
  const [sharedScanContext, setSharedScanContext] = useState(null);

  const handleAskMedAssist = (scanContext) => {
    setSharedScanContext(scanContext);
    setActiveTab("medassist");
  };

  const handleClearScanContext = () => {
    setSharedScanContext(null);
  };

  return (
    <LanguageProvider>
      <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 selection:bg-teal-500 selection:text-white">
        {/* Navigation Header */}
        <Header activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Main Content Area */}
        <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full" id="main-content">
          <div className={activeTab === "home" ? "block" : "hidden"} role="region" aria-label="Overview tab">
            <HomePage setActiveTab={setActiveTab} />
          </div>
          <div className={activeTab === "retina" ? "block" : "hidden"} role="region" aria-label="Retina Analysis tab">
            <RetinaAnalysisPage onAskMedAssist={handleAskMedAssist} />
          </div>
          <div className={activeTab === "chest-xray" ? "block" : "hidden"} role="region" aria-label="Chest X-Ray Analysis tab">
            <ChestXrayAnalysisPage />
          </div>
          <div className={activeTab === "medassist" ? "block" : "hidden"} role="region" aria-label="MedAssist Chat tab">
            <MedAssistPage
              activeScanContext={sharedScanContext}
              onClearScanContext={handleClearScanContext}
            />
          </div>
        </main>

        {/* Global Disclaimer Footer */}
        <Footer />
      </div>
    </LanguageProvider>
  );
}
