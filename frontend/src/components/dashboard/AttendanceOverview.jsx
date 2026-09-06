import React from 'react';
import { Calendar, RotateCcw, Clock, CheckCircle2, XCircle } from 'lucide-react';
import {
  formatDateInKolkata,
  getTodayKolkataDateString,
} from '../../api/attendance';

export default function AttendanceOverview({
  presentCount = 0,
  absentCount = 0,
  activeEmployees = 0,
  selectedDate,
  onDateChange,
  isLoading = false,
}) {
  const todayStr = getTodayKolkataDateString();
  const isToday = selectedDate === todayStr;

  // Calculate percentage based on active workforce
  const presentRate =
    activeEmployees > 0 ? Math.round((presentCount / activeEmployees) * 100) : 0;
  const absentRate =
    activeEmployees > 0 ? Math.max(0, 100 - presentRate) : 0;

  return (
    <div className="bg-white p-5 sm:p-6 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
      {/* Top Header: Title & Date Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-900">Attendance Overview</h2>
            {isToday && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
                Today
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1.5">
            <span>{formatDateInKolkata(selectedDate)}</span>
            <span>•</span>
            <span className="inline-flex items-center gap-1 text-slate-400">
              <Clock className="w-3 h-3" /> Asia/Kolkata
            </span>
          </p>
        </div>

        {/* Date Selector & Today shortcut */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <label htmlFor="dashboard-date-picker" className="sr-only">
              Select Date
            </label>
            <input
              type="date"
              id="dashboard-date-picker"
              value={selectedDate}
              onChange={(e) => onDateChange(e.target.value)}
              max={todayStr}
              className="px-2.5 py-1.5 text-xs text-slate-800 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-colors"
            />
          </div>

          {!isToday && (
            <button
              type="button"
              id="dashboard-today-button"
              onClick={() => onDateChange(todayStr)}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
              title="Jump to today"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Today</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="py-5 space-y-6 flex-1 flex flex-col justify-center">
        {isLoading ? (
          <div className="space-y-4 animate-pulse">
            <div className="h-4 bg-slate-200 rounded w-1/3"></div>
            <div className="h-3.5 bg-slate-100 rounded w-full"></div>
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div className="h-14 bg-slate-100 rounded-lg"></div>
              <div className="h-14 bg-slate-100 rounded-lg"></div>
            </div>
          </div>
        ) : (
          <>
            {/* Visual Distribution Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-700">Daily Workforce Turnout</span>
                <span className="font-bold text-slate-900">
                  {activeEmployees > 0 ? `${presentRate}% Attendance` : 'No active employees'}
                </span>
              </div>

              {/* Progress Track */}
              <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden flex shadow-inner">
                {activeEmployees > 0 ? (
                  <>
                    <div
                      style={{ width: `${presentRate}%` }}
                      className="bg-emerald-500 transition-all duration-500 ease-out"
                      title={`Present: ${presentCount} (${presentRate}%)`}
                    />
                    <div
                      style={{ width: `${absentRate}%` }}
                      className="bg-rose-400 transition-all duration-500 ease-out"
                      title={`Absent: ${absentCount} (${absentRate}%)`}
                    />
                  </>
                ) : (
                  <div className="w-full h-full bg-slate-200" />
                )}
              </div>
            </div>

            {/* Present vs Absent Detailed Breakdown Cards */}
            <div className="grid grid-cols-2 gap-3 pt-1">
              {/* Present Box */}
              <div className="p-3.5 rounded-lg bg-emerald-50/70 border border-emerald-100 flex items-center justify-between">
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-800">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Present</span>
                  </div>
                  <div className="text-xl font-bold text-emerald-700 mt-1">
                    {presentCount}
                  </div>
                  <span className="text-2xs text-emerald-600">
                    {activeEmployees > 0 ? `${presentRate}% of active` : '0%'}
                  </span>
                </div>
              </div>

              {/* Absent Box */}
              <div className="p-3.5 rounded-lg bg-rose-50/70 border border-rose-100 flex items-center justify-between">
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-800">
                    <XCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                    <span>Absent</span>
                  </div>
                  <div className="text-xl font-bold text-rose-700 mt-1">
                    {absentCount}
                  </div>
                  <span className="text-2xs text-rose-600">
                    {activeEmployees > 0 ? `${absentRate}% not checked in` : '0%'}
                  </span>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Footer Info */}
      <div className="pt-3 border-t border-slate-100 text-xs text-slate-400 flex items-center justify-between">
        <span>Based on {activeEmployees} active workforce members</span>
        <span className="font-mono text-2xs uppercase">Strict Statuses: PRESENT / ABSENT</span>
      </div>
    </div>
  );
}
