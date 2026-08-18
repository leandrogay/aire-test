'use client';

import { useState, useCallback, useRef } from 'react';

export default function IngestPage() {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [duplicate, setDuplicate] = useState(null);
  const [pendingFile, setPendingFile] = useState(null);
  const dragDepth = useRef(0);

  const uploadFile = useCallback(async (file, { overwrite = false } = {}) => {
    setUploading(true);
    setError(null);
    setResult(null);
    setDuplicate(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('overwrite', overwrite);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/ingest`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (res.status === 409) {
        setPendingFile(file);
        setDuplicate(data);
        return;
      }

      if (!res.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setPendingFile(null);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }, []);

  const handleFile = useCallback((file) => {
    if (!file) return;
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      setError('Please upload an Excel file (.xlsx or .xls)');
      return;
    }
    uploadFile(file);
  }, [uploadFile]);

  const handleConfirmOverwrite = () => {
    if (pendingFile) uploadFile(pendingFile, { overwrite: true });
  };

  const handleCancelOverwrite = () => {
    setDuplicate(null);
    setPendingFile(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    dragDepth.current = 0;
    setDragActive(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    dragDepth.current += 1;
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    dragDepth.current = Math.max(0, dragDepth.current - 1);
    if (dragDepth.current === 0) setDragActive(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4 py-16">
      <div className="w-full max-w-xl">
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">Ingest Sales Data</h1>
        <p className="text-gray-500 mb-8">
          Drag and drop an Excel file with sales data. It will be automatically mapped and standardised.
        </p>

        <div
          data-testid="drop-zone"
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
            dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'
          }`}
        >
          <input
            type="file"
            id="file-upload"
            accept=".xlsx,.xls"
            onChange={(e) => handleFile(e.target.files?.[0])}
            className="hidden"
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <p className="text-gray-700 font-medium">
              {dragActive ? 'Drop the file here' : 'Drag and drop your Excel file here'}
            </p>
            <p className="text-gray-400 text-sm mt-1">or click to browse (.xlsx, .xls)</p>
          </label>
        </div>

        {uploading && <p className="text-blue-600 mt-4 text-sm">Uploading and processing...</p>}

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {duplicate && (
          <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm">
            <p>{duplicate.message}</p>
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                onClick={handleConfirmOverwrite}
                className="px-3 py-1.5 text-xs font-medium rounded bg-amber-600 text-white"
              >
                Overwrite existing data
              </button>
              <button
                type="button"
                onClick={handleCancelOverwrite}
                className="px-3 py-1.5 text-xs font-medium rounded border border-amber-300 text-amber-700"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {result && (
          <div className="mt-6 p-5 bg-white border border-gray-200 rounded-lg">
            <h2 className="font-medium text-gray-900 mb-3">Ingestion Summary</h2>
            {result.overwritten && (
              <p className="text-xs text-gray-400 mb-2">Existing data for this file was replaced.</p>
            )}
            <ul className="text-sm text-gray-600 space-y-1">
              <li>File: {result.filename}</li>
              <li>Total rows: {result.rows_total}</li>
              <li className="text-green-600">Rows ingested: {result.rows_ingested}</li>
              <li className="text-amber-600">Rows skipped: {result.rows_skipped}</li>
            </ul>

            {result.unmapped_fields?.length > 0 && (
              <p className="text-amber-600 text-sm mt-3">
                Could not detect columns for: {result.unmapped_fields.join(', ')}
              </p>
            )}

            {result.errors?.length > 0 && (
              <div className="mt-3">
                <p className="text-sm font-medium text-gray-700">First few errors:</p>
                <ul className="text-xs text-gray-500 mt-1 space-y-1">
                  {result.errors.map((e, i) => (
                    <li key={i}>Row {e.row}: {e.field ? `${e.field} — ` : ''}{e.reason}</li>
                  ))}
                </ul>
              </div>
            )}

            <a href="/dashboard" className="inline-block mt-4 text-blue-600 text-sm font-medium">
              View dashboard →
            </a>
          </div>
        )}
      </div>
    </main>
  );
}