import { useRef, useState } from 'react';
import type { DragEvent } from 'react';
import { UploadCloud } from 'lucide-react';

export default function UploadDropzone({
  uploading,
  onFile,
}: {
  uploading: boolean;
  onFile: (file: File) => void;
}) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) onFile(file);
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!uploading) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={uploading ? (e) => e.preventDefault() : handleDrop}
      onClick={() => !uploading && inputRef.current?.click()}
      className={`${uploading ? 'cursor-wait opacity-60' : 'cursor-pointer'} rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
        dragging ? 'border-slate-900 bg-slate-100' : 'border-slate-300 bg-white hover:border-slate-400'
      }`}
    >
      <UploadCloud size={32} className="mx-auto text-slate-400" />
      <p className="mt-3 text-sm font-semibold text-slate-800">
        {uploading ? 'Uploading document…' : 'Drag & drop a PDF here, or click to browse'}
      </p>
      <p className="mt-1 text-xs text-slate-500">Only PDF files are supported by the backend.</p>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        aria-label="Upload a PDF knowledge document"
        className="hidden"
        disabled={uploading}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFile(file);
          e.target.value = '';
        }}
      />
    </div>
  );
}
