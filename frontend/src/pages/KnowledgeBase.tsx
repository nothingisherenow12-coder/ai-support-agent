import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { BookOpenCheck, RefreshCw, Search } from 'lucide-react';
import PageContainer from '../components/layout/PageContainer';
import UploadDropzone from '../components/knowledge/UploadDropzone';
import DocumentList from '../components/knowledge/DocumentList';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import { deleteDocument, listDocuments, queryKnowledge, uploadDocument } from '../api/knowledge';
import type { UploadedDocument } from '../types/knowledge';
import { getApiErrorMessage } from '../api/errors';

export default function KnowledgeBase({ canManage = true }: { canManage?: boolean }) {
  const [docs, setDocs] = useState<UploadedDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [question, setQuestion] = useState('');
  const [querying, setQuerying] = useState(false);
  const [queryResult, setQueryResult] = useState<Awaited<ReturnType<typeof queryKnowledge>> | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const refresh = useCallback(async () => {
    setLoading(true); setError(null);
    try { setDocs(await listDocuments()); }
    catch (err) { setError(getApiErrorMessage(err, 'Unable to load documents.')); }
    finally { setLoading(false); }
  }, []);

  async function handleQuery(event: FormEvent) {
    event.preventDefault(); setError(null); setQuerying(true);
    try { setQueryResult(await queryKnowledge(question)); }
    catch (err) { setError(getApiErrorMessage(err, 'Unable to search the knowledge base.')); }
    finally { setQuerying(false); }
  }

  async function handleDelete(doc: UploadedDocument) {
    if (!window.confirm(`Delete ${doc.filename} and its indexed passages?`)) return;
    setDeletingId(doc.id); setError(null);
    try { await deleteDocument(doc.id); setSuccess(`${doc.filename} was deleted.`); await refresh(); }
    catch (err) { setError(getApiErrorMessage(err, 'Unable to delete document.')); }
    finally { setDeletingId(null); }
  }
  useEffect(() => { void refresh(); }, [refresh]);

  async function handleFile(file: File) {
    setError(null); setSuccess(null);
    if (!file.name.toLowerCase().endsWith('.pdf')) { setError('Only PDF files are supported.'); return; }
    setUploading(true);
    try {
      const uploaded = await uploadDocument(file);
      setSuccess(`${uploaded.filename} is indexed and ready to search.`);
      await refresh();
    } catch (err) { setError(getApiErrorMessage(err, 'Unable to upload document.')); }
    finally { setUploading(false); }
  }

  return <PageContainer>
    <div className="mb-7 flex flex-wrap items-end justify-between gap-4"><div><p className="text-[10px] font-semibold uppercase tracking-[.18em] text-[#739269]">Company knowledge</p><h2 className="mt-2 text-2xl font-semibold tracking-tight text-[#182321]">Knowledge base</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Give the assistant trusted material to search. Uploaded PDFs are processed into searchable, cited passages.</p></div><div className="flex items-center gap-2 rounded-full border border-[#e3eae1] bg-white px-3 py-2 text-xs text-slate-500"><BookOpenCheck size={15} className="text-[#63834a]"/> {docs.length} {docs.length === 1 ? 'document' : 'documents'}</div></div>
    {canManage && <section className="rounded-2xl border border-[#e5ebe5] bg-white p-5 md:p-7"><div className="mb-4"><h3 className="text-sm font-semibold text-[#20302a]">Add a knowledge document</h3><p className="mt-1 text-xs text-slate-400">PDF files up to 20 MB. Scanned image-only files may not contain searchable text.</p></div><UploadDropzone uploading={uploading} onFile={handleFile}/>{uploading && <div className="mt-4"><LoadingState message="Extracting text and creating search embeddings…"/></div>}{error && <div className="mt-4"><ErrorState message={error}/></div>}{success && <p role="status" className="mt-4 rounded-xl border border-[#dbe9cf] bg-[#f4f8ef] px-4 py-3 text-sm text-[#42664c]">{success}</p>}</section>}
    <section className="mt-8 rounded-2xl border border-[#e5ebe5] bg-white p-5 md:p-7"><h3 className="text-sm font-semibold text-[#20302a]">Test a question</h3><p className="mt-1 text-xs text-slate-400">Check what the assistant can answer from indexed documents and review its citations.</p><form onSubmit={handleQuery} className="mt-4 flex flex-col gap-2 sm:flex-row"><input required value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about a policy, resume, or guide…" className="min-w-0 flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-[#739269]"/><button disabled={querying || !question.trim()} className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#203b32] px-4 py-3 text-sm font-medium text-white disabled:opacity-50"><Search size={15}/>{querying ? 'Searching…' : 'Search'}</button></form>{queryResult && <div className="mt-4 rounded-xl bg-[#f5f7f2] p-4"><p className="whitespace-pre-wrap text-sm leading-6 text-slate-700">{queryResult.answer}</p>{queryResult.sources.length > 0 && <div className="mt-3 border-t border-[#e1e8dc] pt-3"><p className="text-xs font-semibold text-slate-600">Sources</p><ul className="mt-1 space-y-1">{queryResult.sources.map((source) => <li key={`${source.document_id}-${source.chunk_id}`} className="text-xs text-slate-500">{source.filename} · chunk {source.chunk_index + 1}</li>)}</ul></div>}</div>}</section>
    <section className="mt-8"><div className="mb-3 flex items-center justify-between"><div><h3 className="text-sm font-semibold text-[#20302a]">Indexed documents</h3><p className="mt-1 text-xs text-slate-400">Documents stored in your workspace</p></div><button type="button" onClick={() => void refresh()} disabled={loading} className="flex items-center gap-2 rounded-lg border border-[#e3eae1] bg-white px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"><RefreshCw size={13} className={loading ? 'animate-spin' : ''}/>Refresh</button></div>{loading ? <LoadingState message="Loading knowledge documents…"/> : error ? <ErrorState message={error} onRetry={() => void refresh()}/> : <DocumentList docs={docs} onDelete={canManage ? handleDelete : undefined} deletingId={deletingId}/>}</section>
  </PageContainer>;
}
