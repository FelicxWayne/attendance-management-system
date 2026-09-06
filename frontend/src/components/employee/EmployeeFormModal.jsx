import React, { useState, useEffect } from 'react';
import { X, Loader2, UserPlus, UserCheck } from 'lucide-react';
import { DEPARTMENTS } from '../../api/employees';
import ErrorAlert from '../ErrorAlert';

const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

export default function EmployeeFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialData = null,
}) {
  const isEditMode = Boolean(initialData);

  const [formData, setFormData] = useState({
    employee_id: '',
    name: '',
    email: '',
    mobile: '',
    department_id: '1',
    designation: '',
    status: 'ACTIVE',
  });

  const [fieldErrors, setFieldErrors] = useState({});
  const [apiError, setApiError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Populate form on open or change in initialData
  useEffect(() => {
    if (initialData) {
      setFormData({
        employee_id: initialData.employee_id || '',
        name: initialData.name || '',
        email: initialData.email || '',
        mobile: initialData.mobile || '',
        department_id: String(initialData.department_id || 1),
        designation: initialData.designation || '',
        status: initialData.status || 'ACTIVE',
      });
    } else {
      setFormData({
        employee_id: '',
        name: '',
        email: '',
        mobile: '',
        department_id: '1',
        designation: '',
        status: 'ACTIVE',
      });
    }
    setFieldErrors({});
    setApiError('');
  }, [initialData, isOpen]);

  // Handle ESC key to dismiss modal
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

  const validate = () => {
    const errors = {};

    if (!formData.employee_id.trim()) {
      errors.employee_id = 'Employee ID is required.';
    } else if (formData.employee_id.trim().length > 20) {
      errors.employee_id = 'Employee ID cannot exceed 20 characters.';
    }

    if (!formData.name.trim()) {
      errors.name = 'Full name is required.';
    } else if (formData.name.trim().length > 100) {
      errors.name = 'Name cannot exceed 100 characters.';
    }

    if (!formData.email.trim()) {
      errors.email = 'Email address is required.';
    } else if (!EMAIL_REGEX.test(formData.email.trim())) {
      errors.email = 'Please enter a valid email address (e.g. user@company.com).';
    }

    if (formData.mobile && formData.mobile.trim().length > 20) {
      errors.mobile = 'Mobile number cannot exceed 20 characters.';
    }

    if (!formData.department_id) {
      errors.department_id = 'Department is required.';
    }

    if (!formData.designation.trim()) {
      errors.designation = 'Designation is required.';
    } else if (formData.designation.trim().length > 100) {
      errors.designation = 'Designation cannot exceed 100 characters.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (fieldErrors[name]) {
      setFieldErrors((prev) => ({ ...prev, [name]: '' }));
    }
    if (apiError) {
      setApiError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    setApiError('');

    try {
      await onSubmit(formData);
      onClose();
    } catch (err) {
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === 'string') {
          setApiError(detail);
        } else if (Array.isArray(detail)) {
          setApiError(detail.map((d) => d.msg || d.message).join(', '));
        } else {
          setApiError('Validation error. Please verify the submitted data.');
        }
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        setApiError('Unable to connect to server. Please try again.');
      } else {
        setApiError('An unexpected error occurred. Please try again.');
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
      aria-labelledby="employee-form-title"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs transition-opacity"
        onClick={() => {
          if (!isSubmitting) onClose();
        }}
        aria-hidden="true"
      />

      {/* Modal Card */}
      <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-xl border border-slate-200 z-10 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50/50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
              {isEditMode ? <UserCheck className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
            </div>
            <h2 id="employee-form-title" className="text-lg font-bold text-slate-900">
              {isEditMode ? 'Edit Employee' : 'Add New Employee'}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors disabled:opacity-50"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Form Body */}
        <div className="p-6 overflow-y-auto space-y-4">
          {apiError && <ErrorAlert message={apiError} onDismiss={() => setApiError('')} />}

          <form id="employee-form" onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* Employee ID & Full Name in 2 columns on tablet+ */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="form-employee-id" className="block text-xs font-semibold text-slate-700 mb-1">
                  Employee ID <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="form-employee-id"
                  name="employee_id"
                  value={formData.employee_id}
                  onChange={handleChange}
                  disabled={isSubmitting}
                  placeholder="e.g. EMP001"
                  className={`block w-full px-3 py-2 text-sm bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors ${
                    fieldErrors.employee_id ? 'border-red-300 bg-red-50/30' : 'border-slate-300'
                  }`}
                />
                {fieldErrors.employee_id && (
                  <p className="mt-1 text-xs text-red-600">{fieldErrors.employee_id}</p>
                )}
              </div>

              <div>
                <label htmlFor="form-name" className="block text-xs font-semibold text-slate-700 mb-1">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="form-name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  disabled={isSubmitting}
                  placeholder="e.g. Jane Doe"
                  className={`block w-full px-3 py-2 text-sm bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors ${
                    fieldErrors.name ? 'border-red-300 bg-red-50/30' : 'border-slate-300'
                  }`}
                />
                {fieldErrors.name && (
                  <p className="mt-1 text-xs text-red-600">{fieldErrors.name}</p>
                )}
              </div>
            </div>

            {/* Email & Mobile in 2 columns */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="form-email" className="block text-xs font-semibold text-slate-700 mb-1">
                  Corporate Email <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  id="form-email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  disabled={isSubmitting}
                  placeholder="jane.doe@company.com"
                  className={`block w-full px-3 py-2 text-sm bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors ${
                    fieldErrors.email ? 'border-red-300 bg-red-50/30' : 'border-slate-300'
                  }`}
                />
                {fieldErrors.email && (
                  <p className="mt-1 text-xs text-red-600">{fieldErrors.email}</p>
                )}
              </div>

              <div>
                <label htmlFor="form-mobile" className="block text-xs font-semibold text-slate-700 mb-1">
                  Mobile Number <span className="text-slate-400 font-normal">(Optional)</span>
                </label>
                <input
                  type="tel"
                  id="form-mobile"
                  name="mobile"
                  value={formData.mobile}
                  onChange={handleChange}
                  disabled={isSubmitting}
                  placeholder="+1-555-0199"
                  className={`block w-full px-3 py-2 text-sm bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors ${
                    fieldErrors.mobile ? 'border-red-300 bg-red-50/30' : 'border-slate-300'
                  }`}
                />
                {fieldErrors.mobile && (
                  <p className="mt-1 text-xs text-red-600">{fieldErrors.mobile}</p>
                )}
              </div>
            </div>

            {/* Department & Designation in 2 columns */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="form-department" className="block text-xs font-semibold text-slate-700 mb-1">
                  Department <span className="text-red-500">*</span>
                </label>
                <select
                  id="form-department"
                  name="department_id"
                  value={formData.department_id}
                  onChange={handleChange}
                  disabled={isSubmitting}
                  className="block w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                >
                  {DEPARTMENTS.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name}
                    </option>
                  ))}
                </select>
                {fieldErrors.department_id && (
                  <p className="mt-1 text-xs text-red-600">{fieldErrors.department_id}</p>
                )}
              </div>

              <div>
                <label htmlFor="form-designation" className="block text-xs font-semibold text-slate-700 mb-1">
                  Designation <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="form-designation"
                  name="designation"
                  value={formData.designation}
                  onChange={handleChange}
                  disabled={isSubmitting}
                  placeholder="e.g. Software Engineer"
                  className={`block w-full px-3 py-2 text-sm bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors ${
                    fieldErrors.designation ? 'border-red-300 bg-red-50/30' : 'border-slate-300'
                  }`}
                />
                {fieldErrors.designation && (
                  <p className="mt-1 text-xs text-red-600">{fieldErrors.designation}</p>
                )}
              </div>
            </div>

            {/* Status (Only in Edit mode) */}
            {isEditMode && (
              <div>
                <label htmlFor="form-status" className="block text-xs font-semibold text-slate-700 mb-1">
                  Lifecycle Status <span className="text-red-500">*</span>
                </label>
                <select
                  id="form-status"
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  disabled={isSubmitting}
                  className="block w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                >
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="INACTIVE">INACTIVE</option>
                </select>
                <p className="mt-1 text-xs text-slate-500">
                  Setting to INACTIVE preserves historical attendance records.
                </p>
              </div>
            )}
          </form>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50/50">
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
            form="employee-form"
            disabled={isSubmitting}
            className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-60 shadow-xs"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" aria-hidden="true" />
                <span>{isEditMode ? 'Saving Changes...' : 'Creating Employee...'}</span>
              </>
            ) : (
              <span>{isEditMode ? 'Save Changes' : 'Create Employee'}</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
