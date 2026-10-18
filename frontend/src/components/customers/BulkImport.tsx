import { useState, type ChangeEvent } from 'react';
import { FileUp, Upload } from 'lucide-react';
import { previewCsvImport, type ImportResult } from '../../api/imports';
import { getApiErrorMessage } from '../../api/errors';

const instructions = {
  customers: 'CSV columns: name,email,company. Email must be unique. Existing emails are skipped.',
  tickets: 'CSV columns: external_id,customer_email,title,description,priority,status. Include a stable source ticket ID; repeated IDs are skipped. Customer emails must already exist. Priority and status are optional.',
};
const templates = {
  customers: 'name,email,company\n',
  tickets: 'external_id,customer_email,title,description,priority,status\n',
};

export default function BulkImport({ kind, onImported }: { kind: ImportResult['kind']; onImported: () => void }) {
  const singular = kind === 'customers' ? 'customer' : 'ticket';
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function selectFile(event: ChangeEvent<HTMLInputElement>) {
    const next = event.target.files?.[0] ?? null;
    setFile(next); setResult(null); setError(null);
    if (!next) return;
    if (!next.name.toLowerCase().endsWith('.csv')) { setError('Choose a .csv file.'); return; }
    setBusy(true);
    try { setResult(await previewCsvImport(kind, next)); }
    catch (err) { setError(getApiErrorMessage(err, 'Could not preview this CSV.')); }
    finally { setBusy(false); }
  }

  async function confirmImport() {
    if (!file || !result || result.errors.length) return;
    setBusy(true); setError(null);
    try {
      const imported = await previewCsvImport(kind, file, true);
      setResult(imported);
      setFile(null);
      onImported();
    } catch (err) { setError(getApiErrorMessage(err, 'Import failed. Preview the file again before retrying.')); }
    finally { setBusy(false); }
  }

  return <section className="mt-5 rounded-xl border border-slate-200 bg-white p-4 sm:p-5">
    <div className="flex items-center gap-2"><span className="grid h-9 w-9 place-items-center rounded-lg bg-sky-50 text-sky-800"><FileUp size={17}/></span><div><h2 className="text-sm font-semibold text-slate-900">Bulk import {kind}</h2><p className="mt-0.5 text-xs text-slate-500">Up to 5,000 rows and 10 MB per CSV.</p></div></div>
    <p className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">{instructions[kind]}</p>
    <a download={`${kind}-template.csv`} href={`data:text/csv;charset=utf-8,${encodeURIComponent(templates[kind])}`} className="mt-2 inline-block text-xs font-medium text-emerald-800 underline">Download CSV template</a>
    <label className="mt-3 flex cursor-pointer flex-wrap items-center gap-3"><span className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700"><Upload size={14}/>Choose CSV</span><span className="text-xs text-slate-500">{file?.name ?? 'No file selected'}</span><input type="file" accept=".csv,text/csv" onChange={(event) => void selectFile(event)} className="sr-only"/></label>
    {busy && <p role="status" className="mt-3 text-sm text-slate-500">{result ? 'Importing…' : 'Checking rows…'}</p>}
    {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
    {result && <div className="mt-3 rounded-lg border border-slate-200 p-3"><p role="status" className="text-sm font-medium text-slate-800">{result.imported !== null ? `Imported ${result.imported} ${result.imported === 1 ? singular : `${singular}s`}.` : result.total_rows === 0 ? 'No data rows found. Add records below the header row, save the CSV, and choose it again.' : `${result.total_rows} rows checked · ${result.ready_to_import} ready · ${result.skipped_duplicates} duplicates skipped · ${result.errors.length} errors`}</p>
      {result.preview.length > 0 && <pre className="mt-2 max-h-32 overflow-auto rounded bg-slate-50 p-2 text-[11px] text-slate-600">{JSON.stringify(result.preview, null, 2)}</pre>}
      {result.errors.length > 0 && <ul className="mt-2 max-h-36 space-y-1 overflow-auto text-xs text-red-700">{result.errors.map((item) => <li key={`${item.row}-${item.message}`}>Row {item.row}: {item.message}</li>)}</ul>}
      {result.errors.length === 0 && result.imported === null && result.total_rows > 0 && result.ready_to_import > 0 && <button type="button" disabled={busy} onClick={() => void confirmImport()} className="mt-3 rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50">{busy ? 'Importing…' : `Import ${result.ready_to_import} ${result.ready_to_import === 1 ? singular : `${singular}s`}`}</button>}
      {result.errors.length === 0 && result.imported === null && result.total_rows > 0 && result.ready_to_import === 0 && <p className="mt-2 text-xs text-slate-500">No new records to import.</p>}
    </div>}
  </section>;
}
