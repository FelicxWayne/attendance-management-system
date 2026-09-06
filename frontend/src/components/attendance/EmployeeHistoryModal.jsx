import React, { useState, useEffect, useCallback } from 'react';
import {
  History,
  X,
  Calendar,
  Clock,
  CheckCircle2,
  XCircle,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Filter,
} from 'lucide-react';
import {
  getEmployeeAttendanceHistoryApi,
  formatDateInKolkata,
  formatTimeInKolkata,
  calculateShiftDuration,
} from '../../api/attendance';
import LoadingSpinner from '../LoadingSpinner';
import ErrorAlert from '../ErrorAlert';
import EmptyState from '../EmptyState';

export default function EmployeeHistoryModal({
  isOpen,
  onClose,
  employeeId,
  employeeName,
}) {
  const [historyItems, setHistoryItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(8);
  const [totalPages, setTotalPages] = useState(1);

  // Filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [sortOrder, setSortOrder] = useState('desc');

  // Loading & error
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchHistory = useCallback(
    async (targetPage = page) => {
      if (!employeeId) return;
      setIsLoading(true);
      setError('');

      try {
        const data = await getEmployeeAttendanceHistoryApi(employeeId, {
          page: targetPage,
          pageSize,
          startDate,
          endDate,
          sortOrder,
        });

        setHistoryItems(data.items || []);
        setTotal(data.total || 0);
        setPage(data.page || 1);
        setTotalPages(data.total_pages || 1);
      } catch (err) {
        if (err.response?.data?.detail) {
          setError(String(err.response.data.detail));
        } else {
          setError('Failed to load employee attendance history.');
        }
      } finally {
        setIsLoading(false);
      }
    },
    [employeeId, page, pageSize, startDate, endDate, sortOrder]
  );

  useEffect(() => {
    if (isOpen && employeeId) {
      setPage(1);
      fetchHistory(1);
    }
  }, [isOpen, employeeId, startDate, endDate, sortOrder]);

  // Handle ESC key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !employeeId) return null;

  const handleResetDateFilters = () => {
    setStartDate('');
    setEndDate('');
    setPage(1);
  };

  const hasDateFilters = Boolean(startDate || endDate);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="history-modal-title"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog Card */}
      <div className="relative w-full max-w-3xl bg-white rounded-2xl shadow-xl border border-slate-200 z-10 flex flex-col max-h-[90vh] overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/70">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center shrink-0 font-bold">
              <History className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="history-modal-title" className="text-base font-bold text-slate-900">
                  Attendance History
                </h2>
                <span className="font-mono text-xs font-medium text-slate-600 bg-slate-200/80 px-2 py-0.5 rounded">
                  {employeeId}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {employeeName || 'Employee'} • Complete historical attendance logs
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Filters Toolbar */}
        <div className="p-4 border-b border-slate-100 bg-white flex flex-wrap items-center justify-between gap-3 text-sm">
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-500 font-medium">From</span>
              <input
                type="date"
                value={startDate}
                onChange={(e) => {
                  setStartDate(e.target.value);
                  setPage(1);
                }}
                className="px-2.5 py-1.5 text-xs text-slate-800 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-500 font-medium">To</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => {
                  setEndDate(e.target.value);
                  setPage(1);
                }}
                className="px-2.5 py-1.5 text-xs text-slate-800 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            {hasDateFilters && (
              <button
                type="button"
                onClick={handleResetDateFilters}
                className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
              >
                <Filter className="w-3 h-3" />
                <span>Reset Dates</span>
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                setSortOrder((prev) => (prev === 'desc' ? 'asc' : 'desc'));
                setPage(1);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
              title="Toggle sort order"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
              <span>{sortOrder === 'desc' ? 'Newest First' : 'Oldest First'}</span>
            </button>
          </div>
        </div>

        {/* Modal Body / History List */}
        <div className="p-6 overflow-y-auto flex-1">
          {error && (
            <div className="mb-4">
              <ErrorAlert message={error} onDismiss={() => setError('')} />
            </div>
          )}

          {isLoading ? (
            <div className="py-12">
              <LoadingSpinner message="Loading attendance history..." />
            </div>
          ) : historyItems.length === 0 ? (
            <div className="py-8">
              <EmptyState
                icon={Calendar}
                title="No attendance records found"
                description={
                  hasDateFilters
                    ? 'No attendance records match the selected date range.'
                    : `No attendance records recorded for ${employeeName} yet.`
                }
              />
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-slate-200 shadow-2xs">
              <table className="w-full text-left border-collapse text-xs sm:text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider text-2xs sm:text-xs">
                    <th scope="col" className="py-2.5 px-3">Date</th>
                    <th scope="col" className="py-2.5 px-3">Check-In</th>
                    <th scope="col" className="py-2.5 px-3">Check-Out</th>
                    <th scope="col" className="py-2.5 px-3">Duration</th>
                    <th scope="col" className="py-2.5 px-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {historyItems.map((item, idx) => {
                    const isPresent = item.status === 'PRESENT';
                    const duration = calculateShiftDuration(item.check_in, item.check_out);

                    return (
                      <tr
                        key={item.id ? `hist-${item.id}` : `hist-row-${idx}`}
                        className="hover:bg-slate-50/60 transition-colors"
                      >
                        {/* Date */}
                        <td className="py-2.5 px-3 font-semibold text-slate-900 whitespace-nowrap">
                          {formatDateInKolkata(item.attendance_date)}
                        </td>

                        {/* Check-In */}
                        <td className="py-2.5 px-3 whitespace-nowrap">
                          {item.check_in ? (
                            <div className="flex items-center gap-1 font-medium text-slate-800">
                              <Clock className="w-3.5 h-3.5 text-emerald-600" />
                              <span>{formatTimeInKolkata(item.check_in)}</span>
                            </div>
                          ) : (
                            <span className="text-slate-400 font-mono">—</span>
                          )}
                        </td>

                        {/* Check-Out */}
                        <td className="py-2.5 px-3 whitespace-nowrap">
                          {item.check_out ? (
                            <div className="flex items-center gap-1 font-medium text-slate-800">
                              <Clock className="w-3.5 h-3.5 text-blue-600" />
                              <span>{formatTimeInKolkata(item.check_out)}</span>
                            </div>
                          ) : isPresent && item.check_in ? (
                            <span className="text-amber-700 font-medium">On Shift</span>
                          ) : (
                            <span className="text-slate-400 font-mono">—</span>
                          )}
                        </td>

                        {/* Duration */}
                        <td className="py-2.5 px-3 whitespace-nowrap">
                          <span className={`text-xs ${duration !== '—' ? 'font-medium text-slate-800' : 'text-slate-400 font-mono'}`}>
                            {duration}
                          </span>
                        </td>

                        {/* Status Badge */}
                        <td className="py-2.5 px-3 text-right whitespace-nowrap">
                          {isPresent ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/20">
                              <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
                              PRESENT
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 ring-1 ring-rose-600/20">
                              <XCircle className="w-3 h-3 text-rose-600 shrink-0" />
                              ABSENT
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal Footer with Pagination */}
        <div className="px-6 py-3.5 border-t border-slate-100 bg-slate-50 flex items-center justify-between text-xs text-slate-600">
          <div>
            Showing <strong className="text-slate-900">{historyItems.length}</strong> of{' '}
            <strong className="text-slate-900">{total}</strong> records
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                const prev = Math.max(1, page - 1);
                setPage(prev);
                fetchHistory(prev);
              }}
              disabled={page <= 1 || isLoading}
              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors disabled:opacity-40"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Prev</span>
            </button>
            <span className="font-medium text-slate-700">
              Page {page} of {Math.max(1, totalPages)}
            </span>
            <button
              type="button"
              onClick={() => {
                const next = Math.min(totalPages, page + 1);
                setPage(next);
                fetchHistory(next);
              }}
              disabled={page >= totalPages || isLoading}
              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors disabled:opacity-40"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
