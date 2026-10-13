import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="dp1-card max-w-xl mx-auto my-12 p-6 border-red-500/30 bg-red-950/20 text-center space-y-4">
          <div className="w-12 h-12 mx-auto rounded-full bg-red-900/40 border border-red-500/30 flex items-center justify-center text-red-400">
            <AlertCircle size={24} />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Something went wrong in this view</h3>
            <p className="text-xs text-red-200/80 font-mono mt-2 break-words bg-black/40 p-3 rounded border border-red-900/50">
              {this.state.error?.message || 'Unknown runtime error'}
            </p>
          </div>
          <button
            onClick={this.handleReset}
            className="dp1-btn dp1-btn-primary mx-auto inline-flex items-center gap-2"
          >
            <RefreshCw size={14} />
            <span>Try Again</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
