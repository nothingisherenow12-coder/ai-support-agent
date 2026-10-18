import { Link } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer';

export default function NotFound() {
  return (
    <PageContainer>
      <div className="py-16 text-center">
        <p className="text-lg font-bold text-slate-900">Page not found</p>
        <p className="mt-1 text-sm text-slate-500">
          The page you are looking for does not exist.
        </p>
        <Link
          to="/"
          className="mt-4 inline-block rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
        >
          Back to dashboard
        </Link>
      </div>
    </PageContainer>
  );
}
