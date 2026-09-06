import React, { useState, useEffect } from 'react';
import { LogIn, Loader2, X, AlertCircle } from 'lucide-react';
import ErrorAlert from '../ErrorAlert';
import { getTodayKolkataDateString } from '../../api/attendance';
import { getEmployeesApi } from '../../api/employees';

export default function CheckInModal({
  isOpen,
  onClose,
  onSubmit,
  preselectedEmployee = null,
}) {
  const [employees, setEmployees] = useState([]);
  const [isLoadingEmployees, setIsLoadingEmployees] = useState(false);

  // Form fields
  const [employeeId, setEmployeeId] = useState('');
  const [attendanceDate, setAttendanceDate] = useState(getTodayKolkataDateString());
  const [useCustomTime, setUseCustomTime] = useState(false);
  const [customTime, setCustomTime] = useState('09:00');

  // Form submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Fetch active employees when modal opens
  useEffect(() => {
    if (isOpen) {
      setError('');
      setIsSubmitting(false);
      setAttendanceDate(getTodayKolkataDateString());
      setUseCustomTime(false);
      setCustomTime('09:00');

      if (preselectedEmployee?.employee_id) {
        setEmployeeId(preselectedEmployee.employee_id);
      } else {
        setEmployeeId('');
      }

      const fetchActiveEmployees = async () => {
        setIsLoadingEmployees(true);
        try {
          const res = await getEmployeesApi({ status: 'ACTIVE', pageSize: 100 });
          setEmployees(res.items || []);
        } catch {
          // If fetching active employees fails, user can still type employee ID manually
          setEmployees([]);
        } finally {
          setIsLoadingEmployees(false);
        }
      };

      fetchActiveEmployees();
    }
  }, [isOpen, preselectedEmployee]);

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

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!employeeId.trim()) {
      setError('Please select or enter an Employee ID.');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      let checkInTimestamp = undefined;
      if (useCustomTime && customTime) {
        // Build timezone-aware ISO string for Asia/Kolkata (+05:30)
        // Format: YYYY-MM-DDTHH:mm:00+05:30
        const timeParts = customTime.split(':');
        const hh = timeParts[0].padStart(2, '0');
        const mm = (timeParts[1] || '00').padStart(2, '0');
        checkInTimestamp = `${attendanceDate}T${hh}:${mm}:00+05:30`;
      }

      await onSubmit({
        employee_id: employeeId.trim(),
        attendance_date: attendanceDate,
        check_in: checkInTimestamp,
      });

      onClose();
    } catch (err) {
      if (err.response?.status === 409) {
        setError(
          err.response?.data?.detail ||
          `Employee '${employeeId}' has already checked in on ${attendanceDate}. Duplicate attendance is not allowed.`
        );
      } else if (err.response?.status === 400) {
        setError(
          err.response?.data?.detail ||
          'Cannot record attendance. Please ensure the employee is ACTIVE and date is valid.'
        );
      } else if (err.response?.status === 404) {
        setError(err.response?.data?.detail || `Employee '${employeeId}' not found.`);
      } else if (err.response?.data?.detail) {
        setError(String(err.response.data.detail));
      } else {
        setError('Failed to record check-in. Please try again.');
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
      aria-labelledby="checkin-modal-title"
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
      <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-xl border border-slate-200 z-10 overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center shrink-0">
              <LogIn className="w-5 h-5" aria-hidden="true" />
            </div>
            <div>
              <h2 id="checkin-modal-title" className="text-base font-bold text-slate-900">
                Record Employee Check-In
              </h2>
              <p className="text-xs text-slate-500">
                Mark attendance for an active employee (Asia/Kolkata timezone).
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

          {/* Employee Selection */}
          <div>
            <label htmlFor="modal-employee-select" className="block text-sm font-medium text-slate-700 mb-1">
              Select Active Employee <span className="text-rose-500">*</span>
            </label>
            {employees.length > 0 ? (
              <select
                id="modal-employee-select"
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                required
                className="block w-full px-3 py-2 text-sm text-slate-900 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-colors"
              >
                <option value="">-- Choose an employee --</option>
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.employee_id}>
                    {emp.name} ({emp.employee_id}) - {emp.department_name || 'No Dept'}
                  </option>
                ))}
              </select>
            ) : isLoadingEmployees ? (
              <div className="text-xs text-slate-500 flex items-center gap-1.5 py-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                Loading active employees...
              </div>
            ) : (
              <input
                type="text"
                id="modal-employee-select"
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                placeholder="Enter Employee ID (e.g. EMP101)"
                required
                className="block w-full px-3 py-2 text-sm text-slate-900 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-colors"
              />
            )}
          </div>

          {/* Attendance Date */}
          <div>
            <label htmlFor="modal-attendance-date" className="block text-sm font-medium text-slate-700 mb-1">
              Attendance Date <span className="text-rose-500">*</span>
            </label>
            <input
              type="date"
              id="modal-attendance-date"
              value={attendanceDate}
              onChange={(e) => setAttendanceDate(e.target.value)}
              required
              max={getTodayKolkataDateString()}
              className="block w-full px-3 py-2 text-sm text-slate-900 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-colors"
            />
          </div>

          {/* Check-In Timing Option */}
          <div className="pt-2 border-t border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <label htmlFor="custom-time-toggle" className="text-sm font-medium text-slate-700 cursor-pointer">
                Specify Custom Check-In Time
              </label>
              <input
                type="checkbox"
                id="custom-time-toggle"
                checked={useCustomTime}
                onChange={(e) => setUseCustomTime(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
              />
            </div>

            {useCustomTime ? (
              <div>
                <label htmlFor="modal-custom-time" className="block text-xs font-medium text-slate-500 mb-1">
                  Check-In Time (Asia/Kolkata)
                </label>
                <input
                  type="time"
                  id="modal-custom-time"
                  value={customTime}
                  onChange={(e) => setCustomTime(e.target.value)}
                  className="block w-full px-3 py-2 text-sm text-slate-900 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-colors"
                />
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                <AlertCircle className="w-4 h-4 text-blue-500 shrink-0" />
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
              id="confirm-checkin-btn"
              disabled={isSubmitting || !employeeId}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-xs transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Recording...</span>
                </>
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>Check In</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
