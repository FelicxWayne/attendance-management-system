import React, { useState, useEffect, useCallback } from 'react';
import {
  Users,
  UserCheck,
  CalendarCheck,
  UserX,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import { getDashboardApi } from '../api/dashboard';
import { getTodayKolkataDateString } from '../api/attendance';
import DashboardStatCard from '../components/dashboard/DashboardStatCard';
import AttendanceOverview from '../components/dashboard/AttendanceOverview';
import DepartmentEmployeeCount from '../components/dashboard/DepartmentEmployeeCount';

export default function DashboardPage() {
  // Date state defaulting to today in Asia/Kolkata
  const [selectedDate, setSelectedDate] = useState(getTodayKolkataDateString());

  // Data state
  const [dashboardData, setDashboardData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  // Fetch dashboard metrics from FastAPI backend
  const fetchDashboard = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage('');

    try {
      const data = await getDashboardApi(selectedDate);
      setDashboardData(data);
    } catch (err) {
      if (err.response?.status === 403) {
        setErrorMessage('Access forbidden. Dashboard access is restricted to Administrator and HR roles.');
      } else if (err.response?.status === 422) {
        setErrorMessage('Invalid date specified. Please select a valid calendar date.');
      } else if (err.response?.data?.detail) {
        setErrorMessage(String(err.response.data.detail));
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        setErrorMessage('Unable to load dashboard data. Please check your network connection.');
      } else {
        setErrorMessage('Unable to load dashboard data. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [selectedDate]);

  // Refetch when selected date changes
  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const handleDateChange = (newDate) => {
    setSelectedDate(newDate);
  };

  const totalEmployees = dashboardData?.total_employees ?? 0;
  const activeEmployees = dashboardData?.active_employees ?? 0;
  const presentToday = dashboardData?.present_today ?? 0;
  const absentToday = dashboardData?.absent_today ?? 0;
  const departmentCounts = dashboardData?.department_counts ?? [];

  // Attendance rate for subtitle
  const attendanceRate =
    activeEmployees > 0 ? Math.round((presentToday / activeEmployees) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Overview of employees and attendance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            id="refresh-dashboard-btn"
            onClick={fetchDashboard}
            disabled={isLoading}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 disabled:opacity-50"
            title="Refresh dashboard metrics"
            aria-label="Refresh dashboard metrics"
          >
            <RefreshCw className={`w-4 h-4 text-slate-600 ${isLoading ? 'animate-spin text-blue-600' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {/* Error Alert with Retry */}
      {errorMessage && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-800">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              id="retry-dashboard-btn"
              onClick={fetchDashboard}
              className="px-3 py-1.5 text-xs font-semibold text-rose-700 bg-white border border-rose-200 rounded-lg hover:bg-rose-100/50 transition-colors focus:outline-none focus:ring-2 focus:ring-rose-400"
            >
              Retry
            </button>
            <button
              type="button"
              onClick={() => setErrorMessage('')}
              className="text-xs font-medium text-rose-500 hover:text-rose-700 ml-1"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Row 1: 4 Key Metric / KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Employees */}
        <DashboardStatCard
          title="Total Employees"
          value={totalEmployees}
          icon={Users}
          colorScheme="blue"
          subtitle="All registered workforce"
          isLoading={isLoading}
        />

        {/* Active Employees */}
        <DashboardStatCard
          title="Active Employees"
          value={activeEmployees}
          icon={UserCheck}
          colorScheme="indigo"
          subtitle="Current active roster"
          isLoading={isLoading}
        />

        {/* Present Today */}
        <DashboardStatCard
          title="Present Today"
          value={presentToday}
          icon={CalendarCheck}
          colorScheme="emerald"
          subtitle={activeEmployees > 0 ? `${attendanceRate}% turnout rate` : 'No active employees'}
          isLoading={isLoading}
        />

        {/* Absent Today */}
        <DashboardStatCard
          title="Absent Today"
          value={absentToday}
          icon={UserX}
          colorScheme="rose"
          subtitle="Active employees not checked in"
          isLoading={isLoading}
        />
      </div>

      {/* Row 2: Attendance Overview & Department Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Attendance Overview Section with Date Selector */}
        <AttendanceOverview
          presentCount={presentToday}
          absentCount={absentToday}
          activeEmployees={activeEmployees}
          selectedDate={selectedDate}
          onDateChange={handleDateChange}
          isLoading={isLoading}
        />

        {/* Employees by Department Section */}
        <DepartmentEmployeeCount
          departmentCounts={departmentCounts}
          totalEmployees={totalEmployees}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
