import type { FormEvent } from 'react';
import { useState } from 'react';
import { Send } from 'lucide-react';

export default function ChatInput({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void;
  disabled: boolean;
}) {
  const [value, setValue] = useState('');

  function submit(e: FormEvent) {
    e.preventDefault();
    const text = value.trim();
    if (!text || disabled) return;
    setValue('');
    onSend(text);
  }

  return (
    <form onSubmit={submit} className="flex gap-2 border-t border-slate-200 bg-white p-3">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder='Ask knowledge, customers, or request an action… e.g. "What is our refund policy?"'
        aria-label="Message the AI assistant"
        disabled={disabled}
        className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500 disabled:bg-slate-50"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
      >
        <Send size={15} />
        Send
      </button>
    </form>
  );
}
