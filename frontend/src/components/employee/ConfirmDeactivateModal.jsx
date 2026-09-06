import React, { useState, useEffect } from 'react';
import { AlertTriangle, Loader2, X } from 'lucide-react';
import ErrorAlert from '../ErrorAlert';

export default function ConfirmDeactivateModal({
  isOpen,
  onClose,
  onConfirm,
  employee,
}) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setError('');
    setIsSubmitting(false);
  }, [isOpen, employee]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen && !isSubmitting) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isSubmitting, onClose]);

  if (!isOpen || !employee) return null;

  const handleDeactivate = async () => {
    setIsSubmitting(true);
    setError('');

    try {
      await onConfirm(employee.id);
      onClose();
    } catch (err) {
      if (err.response?.data?.detail) {
        setError(String(err.response.data.detail));
      } else {
        setError('Failed to deactivate employee. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="deactivate-dialog-title"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs transition-opacity"
        onClick={() => {
          if (!isSubmitting) onClose();
        }}
        aria-hidden="true"
      />

      {/* Dialog Card */}
      <div className="relative w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-200 z-10 overflow-hidden">
        <div className="p-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center shrink-0">
              <AlertTriangle className="w-5 h-5" aria-hidden="true" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 id="deactivate-dialog-title" className="text-base font-bold text-slate-900">
                Deactivate Employee
              </h2>
              <p className="text-sm text-slate-600 mt-2 leading-relaxed">
                Are you sure you want to deactivate{' '}
                <strong className="text-slate-900 font-semibold">{employee.name}</strong> (
                <span className="font-mono text-xs">{employee.employee_id}</span>)?
              </p>
              <div className="mt-3 p-3 rounded-lg bg-amber-50/70 border border-amber-200 text-xs text-amber-800 leading-relaxed">
                The employee lifecycle status will become <strong>INACTIVE</strong>. Existing database records and historical attendance records will be preserved.
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-4">
              <ErrorAlert message={error} onDismiss={() => setError('')} />
            </div>
          )}

          <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-slate-400 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDeactivate}
              disabled={isSubmitting}
              className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors disabled:opacity-60 shadow-xs"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" aria-hidden="true" />
                  <span>Deactivating...</span>
                </>
              ) : (
                <span>Deactivate Employee</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
