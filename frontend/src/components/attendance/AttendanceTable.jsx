import React from 'react';
import {
  CheckCircle2,
  XCircle,
  Clock,
  LogOut,
  LogIn,
  History,
  Timer,
} from 'lucide-react';
import {
  formatDateInKolkata,
  formatTimeInKolkata,
  calculateShiftDuration,
} from '../../api/attendance';

export default function AttendanceTable({
  items = [],
  onCheckOut,
  onQuickCheckIn,
  onViewHistory,
}) {
  return (
    <div>
      {/* Desktop Table View (visible on md screens and larger) */}
      <div className="hidden md:block overflow-hidden bg-white rounded-xl border border-slate-200 shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/80 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                <th scope="col" className="py-3.5 px-4">Employee</th>
                <th scope="col" className="py-3.5 px-4">Department</th>
                <th scope="col" className="py-3.5 px-4">Date</th>
                <th scope="col" className="py-3.5 px-4">Check-In</th>
                <th scope="col" className="py-3.5 px-4">Check-Out</th>
                <th scope="col" className="py-3.5 px-4">Duration</th>
                <th scope="col" className="py-3.5 px-4 text-center">Status</th>
                <th scope="col" className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {items.map((item, idx) => {
                const isPresent = item.status === 'PRESENT';
                const hasCheckedIn = Boolean(item.check_in);
                const hasCheckedOut = Boolean(item.check_out);
                const isOnShift = isPresent && hasCheckedIn && !hasCheckedOut;
                const duration = calculateShiftDuration(item.check_in, item.check_out);

                return (
                  <tr
                    key={item.id ? `att-${item.id}` : `emp-${item.employee_id}-${idx}`}
                    className="hover:bg-slate-50/60 transition-colors"
                  >
                    {/* Employee info */}
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">
                        {item.employee_name}
                      </div>
                      <div className="font-mono text-xs text-slate-500 mt-0.5">
                        {item.employee_id}
                      </div>
                    </td>

                    {/* Department */}
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-700">
                        {item.department_name || 'Unassigned'}
                      </span>
                    </td>

                    {/* Date */}
                    <td className="py-3 px-4 font-medium text-slate-900 whitespace-nowrap">
                      {formatDateInKolkata(item.attendance_date)}
                    </td>

                    {/* Check-In */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      {hasCheckedIn ? (
                        <div className="flex items-center gap-1.5 font-medium text-slate-900">
                          <Clock className="w-3.5 h-3.5 text-emerald-600" />
                          <span>{formatTimeInKolkata(item.check_in)}</span>
                        </div>
                      ) : (
                        <span className="text-slate-400 font-mono">—</span>
                      )}
                    </td>

                    {/* Check-Out */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      {hasCheckedOut ? (
                        <div className="flex items-center gap-1.5 font-medium text-slate-900">
                          <Clock className="w-3.5 h-3.5 text-blue-600" />
                          <span>{formatTimeInKolkata(item.check_out)}</span>
                        </div>
                      ) : isOnShift ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 animate-pulse">
                          <Timer className="w-3 h-3" />
                          On Shift
                        </span>
                      ) : (
                        <span className="text-slate-400 font-mono">—</span>
                      )}
                    </td>

                    {/* Shift Duration */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className={`text-xs ${duration !== '—' ? 'font-medium text-slate-800' : 'text-slate-400 font-mono'}`}>
                        {duration}
                      </span>
                    </td>

                    {/* Status Badge */}
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      {isPresent ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/20">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                          PRESENT
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 ring-1 ring-rose-600/20">
                          <XCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                          ABSENT
                        </span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1.5">
                        {/* Check-Out Action Button */}
                        {isOnShift && item.id && (
                          <button
                            type="button"
                            onClick={() => onCheckOut(item)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-300 rounded-lg shadow-2xs transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500"
                            title="Record check-out"
                          >
                            <LogOut className="w-3.5 h-3.5" />
                            <span>Check-Out</span>
                          </button>
                        )}

                        {/* Quick Check-In for Absent Employees */}
                        {!isPresent && onQuickCheckIn && (
                          <button
                            type="button"
                            onClick={() => onQuickCheckIn(item)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg shadow-2xs transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                            title="Mark attendance for this employee"
                          >
                            <LogIn className="w-3.5 h-3.5" />
                            <span>Check In</span>
                          </button>
                        )}

                        {/* View History Button */}
                        <button
                          type="button"
                          onClick={() => onViewHistory(item.employee_id, item.employee_name)}
                          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
                          title={`View ${item.employee_name}'s attendance history`}
                          aria-label={`View history for ${item.employee_name}`}
                        >
                          <History className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mobile Card View (visible on screens smaller than md) */}
      <div className="md:hidden space-y-3">
        {items.map((item, idx) => {
          const isPresent = item.status === 'PRESENT';
          const hasCheckedIn = Boolean(item.check_in);
          const hasCheckedOut = Boolean(item.check_out);
          const isOnShift = isPresent && hasCheckedIn && !hasCheckedOut;
          const duration = calculateShiftDuration(item.check_in, item.check_out);

          return (
            <div
              key={item.id ? `card-att-${item.id}` : `card-emp-${item.employee_id}-${idx}`}
              className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-3"
            >
              {/* Header: Employee Name, ID, and Status */}
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-semibold text-slate-900 text-base">
                    {item.employee_name}
                  </h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="font-mono text-xs font-medium text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                      {item.employee_id}
                    </span>
                    <span className="text-xs text-slate-500">
                      {item.department_name || 'No Dept'}
                    </span>
                  </div>
                </div>

                {/* Status Badge */}
                {isPresent ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/20">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    PRESENT
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 ring-1 ring-rose-600/20">
                    <XCircle className="w-3.5 h-3.5 text-rose-600" />
                    ABSENT
                  </span>
                )}
              </div>

              {/* Timing Grid */}
              <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-100">
                <div>
                  <span className="text-slate-400 block font-medium">Date</span>
                  <span className="font-semibold text-slate-800">
                    {formatDateInKolkata(item.attendance_date)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block font-medium">Duration</span>
                  <span className="font-semibold text-slate-800">
                    {duration}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block font-medium">Check-In</span>
                  <span className="font-medium text-slate-800">
                    {formatTimeInKolkata(item.check_in)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block font-medium">Check-Out</span>
                  {isOnShift ? (
                    <span className="text-amber-700 font-semibold">On Shift</span>
                  ) : (
                    <span className="font-medium text-slate-800">
                      {formatTimeInKolkata(item.check_out)}
                    </span>
                  )}
                </div>
              </div>

              {/* Card Footer Actions */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => onViewHistory(item.employee_id, item.employee_name)}
                  className="inline-flex items-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-800"
                >
                  <History className="w-3.5 h-3.5" />
                  <span>View History</span>
                </button>

                <div className="flex items-center gap-2">
                  {isOnShift && item.id && (
                    <button
                      type="button"
                      onClick={() => onCheckOut(item)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-300 rounded-lg shadow-2xs"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Check-Out</span>
                    </button>
                  )}

                  {!isPresent && onQuickCheckIn && (
                    <button
                      type="button"
                      onClick={() => onQuickCheckIn(item)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg shadow-2xs"
                    >
                      <LogIn className="w-3.5 h-3.5" />
                      <span>Check In</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
