import React, { useState, useEffect, useCallback } from 'react';
import {
  LogIn,
  RefreshCw,
  CheckCircle2,
  CalendarCheck,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import {
  getAttendanceApi,
  getDailyStatusApi,
  checkInApi,
  checkOutApi,
  getTodayKolkataDateString,
} from '../api/attendance';
import DailyStatusSummary from '../components/attendance/DailyStatusSummary';
import AttendanceFilters from '../components/attendance/AttendanceFilters';
import AttendanceTable from '../components/attendance/AttendanceTable';
import CheckInModal from '../components/attendance/CheckInModal';
import CheckOutModal from '../components/attendance/CheckOutModal';
import EmployeeHistoryModal from '../components/attendance/EmployeeHistoryModal';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';
import EmptyState from '../components/EmptyState';

export default function AttendancePage() {
  // Mode: 'daily' (Daily Status Roster) or 'all' (Chronological Attendance Logs)
  const [viewMode, setViewMode] = useState('daily');

  // Selected date for daily status (defaults to today in Asia/Kolkata)
  const [selectedDate, setSelectedDate] = useState(getTodayKolkataDateString());

  // Filter states
  const [search, setSearch] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Data states
  const [summary, setSummary] = useState(null);
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);

  // UI status
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshingSummary, setIsRefreshingSummary] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Modal states
  const [isCheckInOpen, setIsCheckInOpen] = useState(false);
  const [preselectedEmployee, setPreselectedEmployee] = useState(null);

  const [isCheckOutOpen, setIsCheckOutOpen] = useState(false);
  const [activeCheckOutRecord, setActiveCheckOutRecord] = useState(null);

  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [historyTarget, setHistoryTarget] = useState({ id: '', name: '' });

  // Auto-dismiss success message
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  // Fetch daily summary stats
  const fetchSummary = useCallback(async () => {
    setIsRefreshingSummary(true);
    try {
      const data = await getDailyStatusApi({
        attendanceDate: selectedDate,
        departmentId,
        page: 1,
        pageSize: 1, // Summary metrics total_active_employees, present_count, absent_count are in root
      });
      setSummary({
        attendance_date: data.attendance_date,
        total_active_employees: data.total_active_employees,
        present_count: data.present_count,
        absent_count: data.absent_count,
      });
    } catch (err) {
      // Non-blocking summary fetch
      console.error('Failed to load daily status summary', err);
    } finally {
      setIsRefreshingSummary(false);
    }
  }, [selectedDate, departmentId]);

  // Fetch table data based on active view mode
  const fetchData = useCallback(
    async (currentPage = page) => {
      setIsLoading(true);
      setErrorMessage('');

      try {
        if (viewMode === 'daily') {
          // In daily mode, fetch from daily-status endpoint
          const data = await getDailyStatusApi({
            attendanceDate: selectedDate,
            departmentId,
            page: currentPage,
            pageSize,
          });

          setSummary({
            attendance_date: data.attendance_date,
            total_active_employees: data.total_active_employees,
            present_count: data.present_count,
            absent_count: data.absent_count,
          });

          let items = data.items || [];

          // Apply client-side search filter if query is provided
          if (search.trim()) {
            const query = search.trim().toLowerCase();
            items = items.filter(
              (item) =>
                item.employee_id.toLowerCase().includes(query) ||
                item.employee_name.toLowerCase().includes(query)
            );
          }

          // Apply client-side status filter if specified
          if (statusFilter && statusFilter !== 'ALL') {
            items = items.filter((item) => item.status === statusFilter);
          }

          setAttendanceRecords(items);
          setTotal(data.total || 0);
          setPage(data.page || 1);
          setTotalPages(data.total_pages || 1);
        } else {
          // In all logs mode, fetch from attendance logs endpoint
          const data = await getAttendanceApi({
            page: currentPage,
            pageSize,
            attendanceDate: selectedDate || undefined,
            employeeId: search.trim() || undefined,
            departmentId: departmentId || undefined,
            includeAbsent: statusFilter === 'ABSENT' || statusFilter === 'ALL',
            sortBy: 'attendance_date',
            sortOrder: 'desc',
          });

          let items = data.items || [];
          if (statusFilter === 'PRESENT') {
            items = items.filter((item) => item.status === 'PRESENT');
          } else if (statusFilter === 'ABSENT') {
            items = items.filter((item) => item.status === 'ABSENT');
          }

          setAttendanceRecords(items);
          setTotal(data.total || 0);
          setPage(data.page || 1);
          setTotalPages(data.total_pages || 1);

          // Keep summary metrics synchronized in background
          fetchSummary();
        }
      } catch (err) {
        if (err.response?.data?.detail) {
          setErrorMessage(String(err.response.data.detail));
        } else if (err.code === 'ERR_NETWORK' || !err.response) {
          setErrorMessage('Unable to connect to the backend server. Please verify network connection.');
        } else {
          setErrorMessage('Failed to load attendance records. Please try again.');
        }
      } finally {
        setIsLoading(false);
      }
    },
    [viewMode, selectedDate, departmentId, search, statusFilter, page, pageSize, fetchSummary]
  );

  // Trigger fetch when dependency parameters change
  useEffect(() => {
    fetchData(page);
  }, [fetchData, page]);

  // Handlers for filter controls
  const handleDateChange = (newDate) => {
    setSelectedDate(newDate);
    setPage(1);
  };

  const handleSearchChange = (val) => {
    setSearch(val);
    setPage(1);
  };

  const handleDepartmentChange = (val) => {
    setDepartmentId(val);
    setPage(1);
  };

  const handleStatusFilterChange = (val) => {
    setStatusFilter(val);
    setPage(1);
  };

  const handleViewModeChange = (newMode) => {
    setViewMode(newMode);
    setPage(1);
  };

  const handleResetFilters = () => {
    setSearch('');
    setDepartmentId('');
    setStatusFilter('ALL');
    setPage(1);
  };

  // Check-In modal actions
  const handleOpenCheckIn = (employee = null) => {
    setPreselectedEmployee(employee);
    setIsCheckInOpen(true);
  };

  const handleCheckInSubmit = async (payload) => {
    await checkInApi(payload);
    setSuccessMessage(
      `Attendance check-in successfully recorded for employee '${payload.employee_id}'.`
    );
    fetchData(page);
    fetchSummary();
  };

  // Check-Out modal actions
  const handleOpenCheckOut = (record) => {
    setActiveCheckOutRecord(record);
    setIsCheckOutOpen(true);
  };

  const handleCheckOutConfirm = async (attendanceId, payload) => {
    await checkOutApi(attendanceId, payload);
    setSuccessMessage(
      `Check-out successfully recorded for '${activeCheckOutRecord?.employee_name || 'employee'}'.`
    );
    fetchData(page);
    fetchSummary();
  };

  // View history modal action
  const handleOpenHistory = (empId, empName) => {
    setHistoryTarget({ id: empId, name: empName });
    setIsHistoryOpen(true);
  };

  // Pagination bounds
  const hasActiveFilters = Boolean(search || departmentId || (statusFilter && statusFilter !== 'ALL'));

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Attendance</h1>
          <p className="text-sm text-slate-500 mt-1">
            Monitor daily employee attendance, record check-ins and check-outs in Asia/Kolkata timezone.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            id="refresh-attendance-btn"
            onClick={() => {
              fetchData(page);
              fetchSummary();
            }}
            disabled={isLoading}
            className="p-2 text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400"
            title="Refresh attendance data"
            aria-label="Refresh attendance data"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-blue-600' : ''}`} />
          </button>

          <button
            type="button"
            id="mark-attendance-btn"
            onClick={() => handleOpenCheckIn(null)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-xs transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <LogIn className="w-4 h-4" />
            <span>Mark Attendance</span>
          </button>
        </div>
      </div>

      {/* Success Notification Alert */}
      {successMessage && (
        <div
          role="status"
          className="flex items-center justify-between p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-sm"
        >
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setSuccessMessage('')}
            className="text-emerald-500 hover:text-emerald-800 text-sm font-medium ml-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Error Alert */}
      {errorMessage && (
        <ErrorAlert message={errorMessage} onDismiss={() => setErrorMessage('')} />
      )}

      {/* Daily Status KPI Summary */}
      <DailyStatusSummary
        summary={summary}
        selectedDate={selectedDate}
        onDateChange={handleDateChange}
        isLoading={isRefreshingSummary}
      />

      {/* Filter and View Mode Switcher */}
      <AttendanceFilters
        search={search}
        departmentId={departmentId}
        statusFilter={statusFilter}
        viewMode={viewMode}
        onSearchChange={handleSearchChange}
        onDepartmentChange={handleDepartmentChange}
        onStatusFilterChange={handleStatusFilterChange}
        onViewModeChange={handleViewModeChange}
        onResetFilters={handleResetFilters}
      />

      {/* Main Table / Data View */}
      {isLoading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12">
          <LoadingSpinner message="Loading attendance records..." />
        </div>
      ) : attendanceRecords.length === 0 ? (
        <EmptyState
          icon={CalendarCheck}
          title={hasActiveFilters ? 'No matching attendance records' : 'No attendance records found'}
          description={
            hasActiveFilters
              ? 'Try modifying your search or filter parameters.'
              : `No attendance records have been registered for ${selectedDate}. Click 'Mark Attendance' above to check in an employee.`
          }
        />
      ) : (
        <div className="space-y-4">
          <AttendanceTable
            items={attendanceRecords}
            onCheckOut={handleOpenCheckOut}
            onQuickCheckIn={handleOpenCheckIn}
            onViewHistory={handleOpenHistory}
          />

          {/* Pagination bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm text-slate-600">
            <div>
              Showing <strong className="text-slate-900">{attendanceRecords.length}</strong> of{' '}
              <strong className="text-slate-900">{total}</strong> records
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                id="pagination-prev"
                onClick={() => {
                  const prev = Math.max(1, page - 1);
                  setPage(prev);
                  fetchData(prev);
                }}
                disabled={page <= 1 || isLoading}
                className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-40"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>

              <span className="text-xs font-medium text-slate-700 px-2">
                Page {page} of {Math.max(1, totalPages)}
              </span>

              <button
                type="button"
                id="pagination-next"
                onClick={() => {
                  const next = Math.min(totalPages, page + 1);
                  setPage(next);
                  fetchData(next);
                }}
                disabled={page >= totalPages || isLoading}
                className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-40"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Check-In Modal */}
      <CheckInModal
        isOpen={isCheckInOpen}
        onClose={() => {
          setIsCheckInOpen(false);
          setPreselectedEmployee(null);
        }}
        onSubmit={handleCheckInSubmit}
        preselectedEmployee={preselectedEmployee}
      />

      {/* Check-Out Modal */}
      <CheckOutModal
        isOpen={isCheckOutOpen}
        onClose={() => {
          setIsCheckOutOpen(false);
          setActiveCheckOutRecord(null);
        }}
        onConfirm={handleCheckOutConfirm}
        record={activeCheckOutRecord}
      />

      {/* Employee History Modal */}
      <EmployeeHistoryModal
        isOpen={isHistoryOpen}
        onClose={() => {
          setIsHistoryOpen(false);
          setHistoryTarget({ id: '', name: '' });
        }}
        employeeId={historyTarget.id}
        employeeName={historyTarget.name}
      />
    </div>
  );
}
