import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ message = 'Loading...', size = 'default', fullScreen = false }) {
  const sizeClasses = {
    small: 'w-4 h-4',
    default: 'w-8 h-8',
    large: 'w-12 h-12',
  };

  const content = (
    <div className="flex flex-col items-center justify-center p-6 text-slate-500" role="status" aria-live="polite">
      <Loader2 className={`${sizeClasses[size] || sizeClasses.default} animate-spin text-blue-600 mb-2`} aria-hidden="true" />
      {message && <span className="text-sm font-medium text-slate-600">{message}</span>}
      <span className="sr-only">Loading</span>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        {content}
      </div>
    );
  }

  return content;
}
