import type { UploadedDocument } from '../../types/knowledge';
import DocumentCard from './DocumentCard';
import EmptyState from '../common/EmptyState';

export default function DocumentList({ docs, onDelete, deletingId }: { docs: UploadedDocument[]; onDelete?: (doc: UploadedDocument) => void; deletingId: number | null }) {
  if (docs.length === 0) {
    return (
      <EmptyState
        title="No knowledge documents yet."
        hint="Upload company policies, product documentation, FAQs, or internal support guides to make them searchable by the AI assistant."
      />
    );
  }
  return (
    <div className="space-y-2">
      {docs.map((d) => (
        <DocumentCard key={d.id} doc={d} onDelete={onDelete} deleting={deletingId === d.id} />
      ))}
    </div>
  );
}
