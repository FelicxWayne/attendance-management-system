import React, { useState, useEffect } from 'react';
import { LogOut, Loader2, X, Clock, AlertCircle } from 'lucide-react';
import ErrorAlert from '../ErrorAlert';
import { formatTimeInKolkata, formatDateInKolkata } from '../../api/attendance';

export default function CheckOutModal({
  isOpen,
  onClose,
  onConfirm,
  record,
}) {
  const [useCustomTime, setUseCustomTime] = useState(false);
  const [customTime, setCustomTime] = useState('18:00');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setError('');
      setIsSubmitting(false);
      setUseCustomTime(false);
      setCustomTime('18:00');
    }
  }, [isOpen, record]);

  // Handle ESC key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen && !isSubmitting) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isSubmitting, onClose]);

  if (!isOpen || !record) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    try {
      const payload = {};
      if (useCustomTime && customTime) {
        const timeParts = customTime.split(':');
        const hh = timeParts[0].padStart(2, '0');
        const mm = (timeParts[1] || '00').padStart(2, '0');
        payload.check_out = `${record.attendance_date}T${hh}:${mm}:00+05:30`;
      }

      await onConfirm(record.id, payload);
      onClose();
    } catch (err) {
      if (err.response?.status === 409) {
        setError(err.response?.data?.detail || 'This attendance record has already been checked out.');
      } else if (err.response?.status === 400) {
        setError(err.response?.data?.detail || 'Check-out time must be after check-in time.');
      } else if (err.response?.data?.detail) {
        setError(String(err.response.data.detail));
      } else {
        setError('Failed to record check-out. Please try again.');
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
      aria-labelledby="checkout-modal-title"
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
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
              <LogOut className="w-5 h-5" aria-hidden="true" />
            </div>
            <div>
              <h2 id="checkout-modal-title" className="text-base font-bold text-slate-900">
                Confirm Check-Out
              </h2>
              <p className="text-xs text-slate-500">
                Complete shift and record check-out time.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <ErrorAlert message={error} onDismiss={() => setError('')} />
          )}

          {/* Record Summary Box */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-sm">
            <div className="flex justify-between items-center">
              <span className="text-slate-500 text-xs font-medium uppercase">Employee</span>
              <span className="font-semibold text-slate-900">{record.employee_name}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-500 text-xs font-medium uppercase">Employee ID</span>
              <span className="font-mono text-xs text-slate-700 bg-white px-2 py-0.5 rounded border border-slate-200">
                {record.employee_id}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-500 text-xs font-medium uppercase">Date</span>
              <span className="font-medium text-slate-800">
                {formatDateInKolkata(record.attendance_date)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-500 text-xs font-medium uppercase">Check-In Time</span>
              <div className="flex items-center gap-1 font-semibold text-emerald-700">
                <Clock className="w-3.5 h-3.5" />
                <span>{formatTimeInKolkata(record.check_in)}</span>
              </div>
            </div>
          </div>

          {/* Custom Time Toggle */}
          <div className="pt-2 border-t border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <label htmlFor="custom-checkout-toggle" className="text-sm font-medium text-slate-700 cursor-pointer">
                Specify Custom Check-Out Time
              </label>
              <input
                type="checkbox"
                id="custom-checkout-toggle"
                checked={useCustomTime}
                onChange={(e) => setUseCustomTime(e.target.checked)}
                className="w-4 h-4 text-amber-600 rounded border-slate-300 focus:ring-amber-500"
              />
            </div>

            {useCustomTime ? (
              <div>
                <label htmlFor="modal-checkout-time" className="block text-xs font-medium text-slate-500 mb-1">
                  Check-Out Time (Asia/Kolkata)
                </label>
                <input
                  type="time"
                  id="modal-checkout-time"
                  value={customTime}
                  onChange={(e) => setCustomTime(e.target.value)}
                  className="block w-full px-3 py-2 text-sm text-slate-900 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 focus:outline-none transition-colors"
                />
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>Default: Current server timestamp in Asia/Kolkata timezone will be recorded.</span>
              </div>
            )}
          </div>

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-slate-400 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              id="confirm-checkout-btn"
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg shadow-xs transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Recording...</span>
                </>
              ) : (
                <>
                  <LogOut className="w-4 h-4" />
                  <span>Check Out</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
