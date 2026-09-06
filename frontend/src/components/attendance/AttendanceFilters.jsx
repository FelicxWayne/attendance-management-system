import React, { useState, useEffect } from 'react';
import { Search, X, Filter, CalendarDays, ListFilter } from 'lucide-react';
import { DEPARTMENTS } from '../../api/employees';

export default function AttendanceFilters({
  search,
  departmentId,
  statusFilter,
  viewMode,
  onSearchChange,
  onDepartmentChange,
  onStatusFilterChange,
  onViewModeChange,
  onResetFilters,
}) {
  const [searchInput, setSearchInput] = useState(search);

  // Sync internal search input if parent resets
  useEffect(() => {
    setSearchInput(search);
  }, [search]);

  // Debounce search input by 300ms
  useEffect(() => {
    const handler = setTimeout(() => {
      if (searchInput !== search) {
        onSearchChange(searchInput);
      }
    }, 300);

    return () => clearTimeout(handler);
  }, [searchInput, search, onSearchChange]);

  const hasActiveFilters = Boolean(search || departmentId || (statusFilter && statusFilter !== 'ALL'));

  return (
    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-4">
      {/* Top row: View Switcher (Daily Roster vs All Logs) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div className="inline-flex p-1 bg-slate-100 rounded-lg">
          <button
            type="button"
            id="view-mode-daily"
            onClick={() => onViewModeChange('daily')}
            className={`inline-flex items-center gap-2 px-3 py-1.5 text-xs sm:text-sm font-medium rounded-md transition-all ${
              viewMode === 'daily'
                ? 'bg-white text-blue-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <CalendarDays className="w-4 h-4" />
            <span>Daily Status Roster</span>
          </button>
          <button
            type="button"
            id="view-mode-all"
            onClick={() => onViewModeChange('all')}
            className={`inline-flex items-center gap-2 px-3 py-1.5 text-xs sm:text-sm font-medium rounded-md transition-all ${
              viewMode === 'all'
                ? 'bg-white text-blue-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <ListFilter className="w-4 h-4" />
            <span>All Attendance Logs</span>
          </button>
        </div>

        <p className="text-xs text-slate-500">
          {viewMode === 'daily'
            ? 'Showing complete active employee roster with Present & Absent statuses for chosen date.'
            : 'Showing chronological check-in and check-out logs across all dates.'}
        </p>
      </div>

      {/* Filter controls row */}
      <div className="flex flex-col md:flex-row md:items-center gap-3">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[200px]">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" aria-hidden="true" />
          </div>
          <input
            type="text"
            id="attendance-search-input"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by Employee ID or Name..."
            className="block w-full pl-9 pr-8 py-2 text-sm text-slate-900 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-colors"
          />
          {searchInput && (
            <button
              type="button"
              onClick={() => {
                setSearchInput('');
                onSearchChange('');
              }}
              className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-slate-400 hover:text-slate-600"
              aria-label="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-2.5 sm:gap-3">
          {/* Department Filter */}
          <div className="w-full sm:w-auto">
            <label htmlFor="attendance-dept-filter" className="sr-only">
              Filter by Department
            </label>
            <select
              id="attendance-dept-filter"
              value={departmentId}
              onChange={(e) => onDepartmentChange(e.target.value)}
              className="w-full sm:w-auto px-3 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-colors"
            >
              <option value="">All Departments</option>
              {DEPARTMENTS.map((dept) => (
                <option key={dept.id} value={dept.id}>
                  {dept.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="w-full sm:w-auto">
            <label htmlFor="attendance-status-filter" className="sr-only">
              Filter by Status
            </label>
            <select
              id="attendance-status-filter"
              value={statusFilter}
              onChange={(e) => onStatusFilterChange(e.target.value)}
              className="w-full sm:w-auto px-3 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-colors"
            >
              <option value="ALL">All Statuses</option>
              <option value="PRESENT">Present</option>
              <option value="ABSENT">Absent</option>
            </select>
          </div>

          {/* Reset Filters */}
          {hasActiveFilters && (
            <button
              type="button"
              id="reset-attendance-filters"
              onClick={() => {
                setSearchInput('');
                onResetFilters();
              }}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400"
            >
              <Filter className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
