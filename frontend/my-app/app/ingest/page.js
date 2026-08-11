'use client';

import { useState, useCallback } from 'react';

export default function IngestPage() {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFile = useCallback(async (file) => {
    if (!file) return;
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      setError('Please upload an Excel file (.xlsx or .xls)');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/ingest`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Upload failed');
      }

      setResult(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }, []);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4 py-16">
      <div className="w-full max-w-xl">
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">Ingest Sales Data</h1>
        <p className="text-gray-500 mb-8">
          Drag and drop an Excel file with sales data. It will be automatically mapped and standardised.
        </p>

        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
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

        {result && (
          <div className="mt-6 p-5 bg-white border border-gray-200 rounded-lg">
            <h2 className="font-medium text-gray-900 mb-3">Ingestion Summary</h2>
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