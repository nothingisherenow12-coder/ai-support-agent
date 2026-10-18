import { Component } from 'react';
import type { ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  failed: boolean;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return (
        <div className="mx-auto w-full max-w-6xl px-4 py-16 text-center">
          <p className="text-lg font-bold text-slate-900">Something went wrong</p>
          <p className="mt-1 text-sm text-slate-500">
            The page ran into an unexpected error.
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
          >
            Reload the page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
