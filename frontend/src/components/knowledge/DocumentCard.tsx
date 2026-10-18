import { FileText, Trash2 } from 'lucide-react';
import type { UploadedDocument } from '../../types/knowledge';

export default function DocumentCard({ doc, onDelete, deleting }: { doc: UploadedDocument; onDelete?: (doc: UploadedDocument) => void; deleting: boolean }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3">
      <FileText size={20} className="shrink-0 text-slate-400" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-slate-800">{doc.filename}</p>
        <p className="text-xs text-slate-500">
          ID {doc.id} · {doc.chunks_created} chunks · {new Date(doc.created_at).toLocaleString()}
        </p>
      </div>
      <span className="rounded-full border border-green-200 bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">Indexed</span>
      {onDelete && <button type="button" disabled={deleting} aria-label={`Delete ${doc.filename}`} onClick={() => onDelete(doc)} className="rounded-lg p-2 text-slate-500 hover:bg-red-50 hover:text-red-700 disabled:opacity-50"><Trash2 size={16}/></button>}
    </div>
  );
}
