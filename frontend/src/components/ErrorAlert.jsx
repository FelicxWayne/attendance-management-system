import React from 'react';
import { AlertCircle, X } from 'lucide-react';

export default function ErrorAlert({ message, onDismiss, className = '' }) {
  if (!message) return null;

  return (
    <div
      role="alert"
      className={`flex items-start justify-between p-3.5 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm ${className}`}
    >
      <div className="flex items-start gap-2.5">
        <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" aria-hidden="true" />
        <span className="leading-snug">{message}</span>
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="text-red-400 hover:text-red-700 p-0.5 rounded transition-colors ml-2"
          aria-label="Dismiss alert"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
