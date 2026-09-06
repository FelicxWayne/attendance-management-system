import React from 'react';
import { Users, UserCheck, UserX, Calendar, Clock, RotateCcw } from 'lucide-react';
import { formatDateInKolkata, getTodayKolkataDateString } from '../../api/attendance';

export default function DailyStatusSummary({
  summary,
  selectedDate,
  onDateChange,
  isLoading,
}) {
  const todayStr = getTodayKolkataDateString();
  const isToday = selectedDate === todayStr;

  const totalActive = summary?.total_active_employees ?? 0;
  const presentCount = summary?.present_count ?? 0;
  const absentCount = summary?.absent_count ?? 0;

  // Calculate attendance rate percentage
  const attendanceRate = totalActive > 0 
    ? Math.round((presentCount / totalActive) * 100) 
    : 0;

  return (
    <div className="space-y-4">
      {/* Top controls: Date Selector & Info */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <Calendar className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-slate-900">
                Daily Attendance Roster
              </h2>
              {isToday && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                  Today
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1.5">
              <span>{formatDateInKolkata(selectedDate)}</span>
              <span>•</span>
              <span className="inline-flex items-center gap-1 text-slate-500">
                <Clock className="w-3.5 h-3.5" /> Asia/Kolkata (IST)
              </span>
            </p>
          </div>
        </div>

        {/* Date Selector input and Today button */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <label htmlFor="daily-status-date" className="sr-only">
              Select Attendance Date
            </label>
            <input
              type="date"
              id="daily-status-date"
              value={selectedDate}
              onChange={(e) => onDateChange(e.target.value)}
              max={todayStr}
              className="px-3 py-2 text-sm text-slate-800 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-colors"
            />
          </div>

          {!isToday && (
            <button
              type="button"
              id="reset-today-btn"
              onClick={() => onDateChange(todayStr)}
              className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
              title="Jump to today"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Today</span>
            </button>
          )}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Total Active Employees */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center gap-4 transition-all hover:border-slate-300">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <Users className="w-6 h-6" aria-hidden="true" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Total Active Employees
            </p>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold text-slate-900 tracking-tight">
                {isLoading ? '—' : totalActive}
              </span>
              <span className="text-xs text-slate-400">on roster</span>
            </div>
          </div>
        </div>

        {/* Present Employees */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center gap-4 transition-all hover:border-emerald-300 border-l-4 border-l-emerald-500">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
            <UserCheck className="w-6 h-6" aria-hidden="true" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Present Today
            </p>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold text-emerald-700 tracking-tight">
                {isLoading ? '—' : presentCount}
              </span>
              <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                {isLoading ? '...' : `${attendanceRate}% rate`}
              </span>
            </div>
          </div>
        </div>

        {/* Absent Employees */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center gap-4 transition-all hover:border-rose-300 border-l-4 border-l-rose-500">
          <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
            <UserX className="w-6 h-6" aria-hidden="true" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Absent Today
            </p>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold text-rose-700 tracking-tight">
                {isLoading ? '—' : absentCount}
              </span>
              <span className="text-xs text-slate-400">not checked in</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
