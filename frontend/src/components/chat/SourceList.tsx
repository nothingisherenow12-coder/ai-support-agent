import { FileText } from 'lucide-react';
import type { KnowledgeQueryResponse } from '../../types/knowledge';

export default function SourceList({ response }: { response: KnowledgeQueryResponse }) {
  if (response.sources.length === 0) return null;
  return (
    <div className="mt-3 border-t border-slate-100 pt-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        Sources {response.answerable ? '' : '(unanswered)'}
      </p>
      <ul className="mt-1.5 space-y-1">
        {response.sources.map((s) => (
          <li
            key={s.chunk_id}
            className="flex items-center gap-1.5 text-xs text-slate-600"
          >
            <FileText size={13} className="shrink-0 text-slate-400" />
            <span className="font-medium">{s.filename}</span>
            <span className="text-slate-400">
              · chunk {s.chunk_index} · distance {s.distance.toFixed(3)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
