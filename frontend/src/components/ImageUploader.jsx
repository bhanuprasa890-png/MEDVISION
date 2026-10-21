import React, { useRef, useState, useEffect } from "react";
import {
  UploadCloud,
  Image as ImageIcon,
  X,
  AlertCircle,
  Maximize2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Grid,
} from "lucide-react";

export function ImageUploader({
  selectedFile,
  previewUrl,
  error,
  isLoading,
  onFileSelect,
  onReset,
  modalityLabel = "Medical Image",
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isZoomModalOpen, setIsZoomModalOpen] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1.0);
  const [showTransparencyGrid, setShowTransparencyGrid] = useState(true);
  const fileInputRef = useRef(null);

  // Close zoom modal on Escape key press
  useEffect(() => {
    if (!isZoomModalOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        setIsZoomModalOpen(false);
        setZoomLevel(1.0);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isZoomModalOpen]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files[0]);
    }
  };

  return (
    <div className="w-full">
      {/* Client Error Notice */}
      {error && (
        <div
          role="alert"
          aria-live="assertive"
          className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-start space-x-2 text-rose-300 text-sm animate-fadeIn"
        >
          <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {!selectedFile ? (
        /* Drag & Drop Upload Zone */
        <div
          role="button"
          tabIndex={0}
          aria-label={`Upload ${modalityLabel}. Drag and drop your scan here, or press Enter to browse files`}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 ${
            isDragOver
              ? "border-teal-400 bg-teal-500/10 scale-[1.01]"
              : "border-slate-700 bg-slate-900/60 hover:border-slate-500 hover:bg-slate-900"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            aria-hidden="true"
            tabIndex={-1}
            onChange={handleInputChange}
          />

          <div className="w-16 h-16 rounded-2xl bg-teal-500/10 text-teal-400 flex items-center justify-center mx-auto mb-4 border border-teal-500/20">
            <UploadCloud className="w-8 h-8" />
          </div>

          <h3 className="text-base font-semibold text-white mb-1">
            Upload {modalityLabel}
          </h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
            Drag and drop your scan here, or click to browse files from your computer.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-2 text-[11px] text-slate-500">
            <span className="px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700">JPEG</span>
            <span className="px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700">PNG</span>
            <span className="px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700">WebP</span>
            <span className="px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700">Max 10 MB</span>
          </div>
        </div>
      ) : (
        /* Aspect-Ratio-Aware Responsive Image Preview Box */
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 sm:p-5">
          {/* Header Bar */}
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
            <div className="flex items-center space-x-2 text-sm text-slate-300 truncate mr-2">
              <ImageIcon className="w-4 h-4 text-teal-400 flex-shrink-0" />
              <span className="font-medium truncate">{selectedFile.name}</span>
              <span className="text-xs text-slate-500 hidden sm:inline">
                ({(selectedFile.size / 1024).toFixed(1)} KB)
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setIsZoomModalOpen(true)}
                className="hidden sm:inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-colors cursor-pointer"
                title="Open high-resolution inspection modal"
                data-testid="zoom-button"
              >
                <Maximize2 className="w-3.5 h-3.5 text-teal-400" />
                <span>Inspect Scan</span>
              </button>

              <button
                type="button"
                onClick={onReset}
                disabled={isLoading}
                className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
                title="Remove image"
                aria-label="Remove image"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Aspect-Ratio-Aware Centered Preview Frame */}
          <div className="flex flex-col items-center justify-center py-1">
            <div className="relative inline-flex flex-col items-center justify-center max-w-full rounded-2xl p-2 sm:p-3 bg-slate-950/70 border border-slate-800 shadow-xl">
              {/* Image Frame with Transparency Grid */}
              <div
                className="relative rounded-xl overflow-hidden border border-slate-700/80 flex items-center justify-center max-w-full group"
                style={{
                  backgroundImage: showTransparencyGrid
                    ? "repeating-conic-gradient(#334155 0% 25%, #0f172a 0% 50%)"
                    : "none",
                  backgroundSize: "16px 16px",
                  backgroundColor: "#090d16",
                }}
              >
                <img
                  src={previewUrl}
                  alt="Scan preview"
                  data-testid="preview-image"
                  className="relative z-10 object-contain w-auto max-w-full rounded-lg select-none max-h-[360px] sm:max-h-[440px] md:max-h-[500px]"
                />

                {/* Inspect Overlay Trigger */}
                <div className="absolute top-2 right-2 z-20 flex items-center space-x-1.5 opacity-90 sm:opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    type="button"
                    onClick={() => setIsZoomModalOpen(true)}
                    className="p-1.5 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 shadow-lg backdrop-blur text-xs flex items-center space-x-1 transition-all cursor-pointer"
                    title="Inspect larger scan"
                  >
                    <Maximize2 className="w-3.5 h-3.5 text-teal-400" />
                    <span className="hidden sm:inline font-medium">Inspect</span>
                  </button>
                </div>
              </div>

              {/* Viewport Control Bar */}
              <div className="w-full mt-2.5 pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400 px-1">
                <div className="flex items-center space-x-2 text-[11px]">
                  <span className="font-mono text-slate-300">{selectedFile.type || "image/unknown"}</span>
                  <span className="text-slate-600">•</span>
                  <span>Aspect ratio preserved (`object-contain`)</span>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => setShowTransparencyGrid((prev) => !prev)}
                    className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-[11px] font-medium border transition-colors cursor-pointer ${
                      showTransparencyGrid
                        ? "bg-teal-500/10 text-teal-300 border-teal-500/30"
                        : "bg-slate-800 text-slate-400 border-slate-700"
                    }`}
                    title="Toggle background transparency checkerboard pattern"
                    data-testid="transparency-toggle"
                  >
                    <Grid className="w-3 h-3" />
                    <span>{showTransparencyGrid ? "Transparency Grid: ON" : "Transparency Grid: OFF"}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setIsZoomModalOpen(true)}
                    className="sm:hidden inline-flex items-center space-x-1 px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-colors cursor-pointer"
                    title="Open magnified inspection window"
                  >
                    <ZoomIn className="w-3.5 h-3.5 text-teal-400" />
                    <span>Zoom</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* High-Resolution Zoom & Inspection Modal */}
          {isZoomModalOpen && (
            <div
              className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md flex flex-col p-3 sm:p-6 animate-fadeIn"
              role="dialog"
              aria-modal="true"
              aria-label="High-resolution medical scan inspection"
              data-testid="inspection-modal"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800 text-slate-200">
                <div className="flex items-center space-x-2 truncate mr-4">
                  <ImageIcon className="w-4 h-4 text-teal-400 flex-shrink-0" />
                  <span className="font-semibold text-sm truncate">{selectedFile.name}</span>
                  <span className="text-xs text-slate-400 hidden sm:inline">
                    ({(selectedFile.size / 1024).toFixed(1)} KB • {selectedFile.type})
                  </span>
                </div>

                <div className="flex items-center space-x-2 flex-shrink-0">
                  {/* Zoom Controls */}
                  <div className="flex items-center space-x-1 bg-slate-900 border border-slate-800 rounded-lg p-1 text-xs">
                    <button
                      type="button"
                      onClick={() => setZoomLevel((z) => Math.max(0.5, Number((z - 0.25).toFixed(2))))}
                      disabled={zoomLevel <= 0.5}
                      className="p-1.5 text-slate-400 hover:text-white disabled:opacity-30 rounded hover:bg-slate-800 transition-colors cursor-pointer"
                      title="Zoom out (min 50%)"
                      aria-label="Zoom out"
                      data-testid="zoom-out"
                    >
                      <ZoomOut className="w-3.5 h-3.5" />
                    </button>
                    <span className="px-1.5 font-mono text-[11px] text-teal-300 min-w-[44px] text-center">
                      {Math.round(zoomLevel * 100)}%
                    </span>
                    <button
                      type="button"
                      onClick={() => setZoomLevel((z) => Math.min(3.0, Number((z + 0.25).toFixed(2))))}
                      disabled={zoomLevel >= 3.0}
                      className="p-1.5 text-slate-400 hover:text-white disabled:opacity-30 rounded hover:bg-slate-800 transition-colors cursor-pointer"
                      title="Zoom in (max 300%)"
                      aria-label="Zoom in"
                      data-testid="zoom-in"
                    >
                      <ZoomIn className="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setZoomLevel(1.0)}
                      className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition-colors ml-1 cursor-pointer"
                      title="Reset zoom to 100%"
                      aria-label="Reset zoom to 100%"
                      data-testid="zoom-reset"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Close Modal Button */}
                  <button
                    type="button"
                    onClick={() => {
                      setIsZoomModalOpen(false);
                      setZoomLevel(1.0);
                    }}
                    className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
                    title="Close modal (Esc)"
                    aria-label="Close modal"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Modal Body Canvas */}
              <div className="flex-1 overflow-auto flex items-center justify-center p-2 rounded-xl bg-slate-950 border border-slate-800/80">
                <div
                  className="relative inline-flex items-center justify-center max-w-full rounded-xl overflow-hidden border border-slate-700/60"
                  style={{
                    backgroundImage: showTransparencyGrid
                      ? "repeating-conic-gradient(#334155 0% 25%, #0f172a 0% 50%)"
                      : "none",
                    backgroundSize: "16px 16px",
                    backgroundColor: "#090d16",
                  }}
                >
                  <img
                    src={previewUrl}
                    alt="Enlarged scan inspection"
                    className="object-contain max-h-[75vh] max-w-[85vw] select-none rounded-lg"
                    style={{
                      transform: `scale(${zoomLevel})`,
                      transformOrigin: "center center",
                      transition: "transform 0.15s ease-out",
                    }}
                  />
                </div>
              </div>

              {/* Modal Footer */}
              <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-500 px-1">
                <span>Use magnification controls to inspect pulmonary opacities or fine anatomical borders. Press Esc to exit.</span>
                <span className="font-medium text-slate-400">Aspect Ratio Preserved (`object-contain`)</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
