import { Building2, Mail, User } from 'lucide-react';
import type { Customer } from '../../types/customer';

export default function CustomerCard({ customer }: { customer: Customer }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-900 text-white">
          <User size={18} />
        </div>
        <div>
          <p className="text-sm font-bold text-slate-900">{customer.name}</p>
          <p className="text-xs text-slate-500">Customer #{customer.id}</p>
        </div>
      </div>
      <div className="mt-3 space-y-1.5 text-sm text-slate-600">
        <p className="flex items-center gap-2 text-xs">
          <Mail size={14} className="text-slate-400" /> {customer.email}
        </p>
        {customer.company && (
          <p className="flex items-center gap-2 text-xs">
            <Building2 size={14} className="text-slate-400" /> {customer.company}
          </p>
        )}
      </div>
    </div>
  );
}
