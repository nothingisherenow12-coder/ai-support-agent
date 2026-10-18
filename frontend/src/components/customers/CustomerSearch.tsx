import { useState } from 'react';
import type { FormEvent } from 'react';
import { Search } from 'lucide-react';

export default function CustomerSearch({
  onSearch,
  loading,
}: {
  onSearch: (id: number) => void;
  loading: boolean;
}) {
  const [value, setValue] = useState('');

  function submit(e: FormEvent) {
    e.preventDefault();
    const id = Number(value.trim());
    if (Number.isInteger(id) && id > 0) onSearch(id);
  }

  return (
    <form onSubmit={submit} className="flex gap-2">
      <div className="relative flex-1">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Enter customer ID, e.g. 1"
          aria-label="Customer ID"
          inputMode="numeric"
          className="w-full rounded-lg border border-slate-300 py-2 pl-9 pr-3 text-sm outline-none focus:border-slate-500"
        />
      </div>
      <button
        type="submit"
        disabled={loading || !value.trim()}
        className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
      >
        {loading ? 'Loading…' : 'Search'}
      </button>
    </form>
  );
}
