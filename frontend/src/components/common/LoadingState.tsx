import { Loader2 } from 'lucide-react';

export default function LoadingState({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
      <Loader2 size={16} className="animate-spin text-slate-500" />
      {message}
    </div>
  );
}
