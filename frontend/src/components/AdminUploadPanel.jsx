import { useRef, useState } from "react";
import { uploadAdminDocument } from "../services/api";

export default function AdminUploadPanel({ domain }) {
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const uploadFile = async (file) => {
    if (!file) return;
    setError("");
    setStatus("Ingesting document...");
    setIsUploading(true);
    try {
      const result = await uploadAdminDocument(domain, file);
      setStatus(`Done! ${result.chunks_indexed} chunks indexed.`);
    } catch (err) {
      setStatus("");
      setError(err.message || "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = async (event) => {
    event.preventDefault();
    setIsDragging(false);
    const droppedFile = event.dataTransfer.files?.[0];
    await uploadFile(droppedFile);
  };

  const handleFileChange = async (event) => {
    const selectedFile = event.target.files?.[0];
    await uploadFile(selectedFile);
    if (event.target) {
      event.target.value = "";
    }
  };

  return (
    <section className="mb-2 shrink-0 rounded-xl border border-emerald-300 bg-emerald-50/70 p-2.5 shadow-sm dark:border-emerald-800/70 dark:bg-emerald-950/20 md:mb-3 md:p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="text-xs font-bold uppercase tracking-wide text-emerald-900 dark:text-emerald-200">
          Admin Document Upload
        </p>
        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
          {domain}
        </span>
      </div>

      <div
        onDragOver={(event) => {
          event.preventDefault();
          if (!isUploading) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`rounded-lg border-2 border-dashed p-3 text-center transition md:p-4 ${
          isDragging
            ? "border-emerald-500 bg-emerald-100/80 dark:border-emerald-400 dark:bg-emerald-900/30"
            : "border-emerald-300 bg-white dark:border-emerald-800 dark:bg-[#2b2d31]"
        }`}
      >
        <p className="text-xs text-slate-700 dark:text-[#b5bac1]">
          Drag and drop a PDF/TXT/MD file here, or{" "}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="font-semibold text-emerald-700 underline hover:text-emerald-600 disabled:opacity-60 dark:text-emerald-300 dark:hover:text-emerald-200"
          >
            browse
          </button>
          .
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {isUploading && (
        <p className="mt-2 text-xs font-semibold text-emerald-700 dark:text-emerald-300">
          Ingesting document...
        </p>
      )}
      {!!status && !isUploading && (
        <p className="mt-2 text-xs font-semibold text-emerald-700 dark:text-emerald-300">{status}</p>
      )}
      {!!error && (
        <p className="mt-2 text-xs font-semibold text-rose-700 dark:text-rose-300">{error}</p>
      )}
    </section>
  );
}
