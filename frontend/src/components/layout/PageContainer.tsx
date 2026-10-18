import type { ReactNode } from 'react';

export default function PageContainer({ children }: { children: ReactNode }) {
  return <div className="mx-auto w-full max-w-7xl px-5 py-7 md:px-8 md:py-9">{children}</div>;
}
