import { useEffect, useState } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import ErrorBoundary from './components/common/ErrorBoundary';
import Dashboard from './pages/Dashboard';
import Assistant from './pages/Assistant';
import KnowledgeBase from './pages/KnowledgeBase';
import Customers from './pages/Customers';
import Tickets from './pages/Tickets';
import Actions from './pages/Actions';
import NotFound from './pages/NotFound';
import SignIn from './pages/SignIn';
import { checkSession, type WorkspaceSession } from './api/auth';
import TeamAdmin from './pages/TeamAdmin';

export default function App() {
  const [session, setSession] = useState<WorkspaceSession | false | null>(null);
  useEffect(() => {
    const expired = () => setSession(false);
    window.addEventListener('support-agent:session-expired', expired);
    void checkSession().then((value) => setSession(value ?? false));
    return () => window.removeEventListener('support-agent:session-expired', expired);
  }, []);

  return (
    <BrowserRouter>
      {session === null ? <div className="grid min-h-screen place-items-center text-sm text-slate-500">Checking secure session…</div> : !session ? <SignIn onSignedIn={() => { void checkSession().then((value) => setSession(value ?? false)); }} /> :
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar isAdmin={session.role === 'admin'} canOperate={session.role !== 'viewer'} />
        <div className="flex min-w-0 flex-1 flex-col">
          <Header session={session} />
          <main className="flex-1">
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/assistant" element={session.role !== 'viewer' ? <Assistant /> : <NotFound />} />
                <Route path="/knowledge" element={<KnowledgeBase canManage={session.role !== 'viewer'} />} />
                <Route path="/customers" element={<Customers canManage={session.role !== 'viewer'} />} />
                <Route path="/tickets" element={<Tickets canManage={session.role !== 'viewer'} />} />
                <Route path="/team" element={session.role === 'admin' ? <TeamAdmin /> : <NotFound />} />
                <Route path="/actions" element={<Actions canManage={session.role !== 'viewer'} />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </ErrorBoundary>
          </main>
        </div>
      </div>
      }
    </BrowserRouter>
  );
}
