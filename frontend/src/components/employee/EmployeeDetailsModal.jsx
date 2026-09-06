import React, { useEffect } from 'react';
import { X, User, Mail, Phone, Building2, Briefcase, Calendar, Edit2 } from 'lucide-react';

export default function EmployeeDetailsModal({
  isOpen,
  onClose,
  employee,
  onEdit,
}) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !employee) return null;

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    try {
      return new Date(dateString).toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  const isActive = employee.status === 'ACTIVE';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="employee-details-title"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Card */}
      <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-xl border border-slate-200 z-10 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50/50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
              <User className="w-4 h-4" />
            </div>
            <div>
              <h2 id="employee-details-title" className="text-lg font-bold text-slate-900 leading-tight">
                {employee.name}
              </h2>
              <span className="text-xs font-mono font-medium text-slate-500">
                {employee.employee_id}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Details */}
        <div className="p-6 overflow-y-auto space-y-5">
          {/* Status Banner */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
              Employment Status
            </span>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                isActive
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-slate-100 text-slate-600 border-slate-200'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
                  isActive ? 'bg-emerald-500' : 'bg-slate-400'
                }`}
              />
              {employee.status}
            </span>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div className="space-y-1">
              <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
                <Briefcase className="w-3.5 h-3.5" /> Designation
              </span>
              <p className="font-semibold text-slate-800">{employee.designation}</p>
            </div>

            <div className="space-y-1">
              <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5" /> Department
              </span>
              <p className="font-semibold text-slate-800">
                {employee.department_name || employee.department?.name || '—'}
              </p>
            </div>

            <div className="space-y-1">
              <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5" /> Email
              </span>
              <p className="font-medium text-slate-800 break-all">{employee.email}</p>
            </div>

            <div className="space-y-1">
              <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
                <Phone className="w-3.5 h-3.5" /> Mobile
              </span>
              <p className="font-medium text-slate-800">{employee.mobile || 'Not provided'}</p>
            </div>
          </div>

          {/* Audit Timestamps */}
          <div className="pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-slate-500">
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>Created: {formatDate(employee.created_at)}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>Updated: {formatDate(employee.updated_at)}</span>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 bg-slate-50/50">
          <button
            type="button"
            onClick={() => {
              onClose();
              if (onEdit) onEdit(employee);
            }}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-sm font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg transition-colors"
          >
            <Edit2 className="w-4 h-4" />
            <span>Edit Profile</span>
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
