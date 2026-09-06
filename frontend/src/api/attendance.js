import apiClient from './client';

/**
 * Returns today's date formatted as YYYY-MM-DD in Asia/Kolkata timezone.
 * @returns {string}
 */
export function getTodayKolkataDateString() {
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
  return formatter.format(new Date());
}

/**
 * Formats a timezone-aware ISO string to readable local time in Asia/Kolkata (e.g. "09:30 AM").
 * @param {string|null} dateString
 * @returns {string}
 */
export function formatTimeInKolkata(dateString) {
  if (!dateString) return '—';
  try {
    const d = new Date(dateString);
    return d.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
      timeZone: 'Asia/Kolkata',
    });
  } catch {
    return '—';
  }
}

/**
 * Formats a date string to readable format in Asia/Kolkata (e.g. "Sep 5, 2026").
 * @param {string|null} dateString
 * @returns {string}
 */
export function formatDateInKolkata(dateString) {
  if (!dateString) return '—';
  try {
    const d = new Date(dateString.includes('T') ? dateString : `${dateString}T00:00:00`);
    return d.toLocaleDateString([], {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      timeZone: 'Asia/Kolkata',
    });
  } catch {
    return dateString;
  }
}

/**
 * Fetches paginated, filtered attendance records.
 * @param {Object} params
 * @param {number} [params.page=1]
 * @param {number} [params.pageSize=10]
 * @param {string} [params.attendanceDate='']
 * @param {string} [params.startDate='']
 * @param {string} [params.endDate='']
 * @param {string} [params.employeeId='']
 * @param {number|string} [params.departmentId='']
 * @param {boolean} [params.includeAbsent=false]
 * @param {string} [params.sortBy='attendance_date']
 * @param {string} [params.sortOrder='desc']
 * @returns {Promise<{ items: Array, total: number, page: number, page_size: number, total_pages: number }>}
 */
export async function getAttendanceApi({
  page = 1,
  pageSize = 10,
  attendanceDate = '',
  startDate = '',
  endDate = '',
  employeeId = '',
  departmentId = '',
  includeAbsent = false,
  sortBy = 'attendance_date',
  sortOrder = 'desc',
} = {}) {
  const queryParams = {
    page,
    page_size: pageSize,
    sort_by: sortBy,
    sort_order: sortOrder,
  };

  if (attendanceDate) queryParams.attendance_date = attendanceDate;
  if (startDate) queryParams.start_date = startDate;
  if (endDate) queryParams.end_date = endDate;
  if (employeeId && employeeId.trim()) queryParams.employee_id = employeeId.trim();
  if (departmentId && Number(departmentId) > 0) queryParams.department_id = Number(departmentId);
  if (includeAbsent) queryParams.include_absent = true;

  const response = await apiClient.get('/attendance', { params: queryParams });
  return response.data;
}

/**
 * Marks attendance check-in for an active employee.
 * @param {Object} payload
 * @param {string} payload.employee_id
 * @param {string} [payload.attendance_date]
 * @param {string} [payload.check_in]
 * @returns {Promise<Object>}
 */
export async function checkInApi({ employee_id, attendance_date, check_in }) {
  const payload = {
    employee_id: employee_id.trim(),
  };

  if (attendance_date) payload.attendance_date = attendance_date;
  if (check_in) payload.check_in = check_in;

  const response = await apiClient.post('/attendance', payload);
  return response.data;
}

/**
 * Records check-out for an existing attendance record by primary key ID.
 * @param {number} attendanceId
 * @param {Object} [payload={}]
 * @param {string} [payload.check_out]
 * @returns {Promise<Object>}
 */
export async function checkOutApi(attendanceId, { check_out } = {}) {
  const payload = {};
  if (check_out) payload.check_out = check_out;

  const response = await apiClient.put(`/attendance/${attendanceId}/checkout`, payload);
  return response.data;
}

/**
 * Retrieves daily attendance summary for active employees with computed PRESENT and ABSENT counts.
 * @param {Object} [params={}]
 * @param {string} [params.attendanceDate='']
 * @param {number|string} [params.departmentId='']
 * @param {number} [params.page=1]
 * @param {number} [params.pageSize=10]
 * @returns {Promise<{ attendance_date: string, total_active_employees: number, present_count: number, absent_count: number, items: Array, total: number, page: number, page_size: number, total_pages: number }>}
 */
export async function getDailyStatusApi({
  attendanceDate = '',
  departmentId = '',
  page = 1,
  pageSize = 10,
} = {}) {
  const queryParams = {
    page,
    page_size: pageSize,
  };

  if (attendanceDate) queryParams.attendance_date = attendanceDate;
  if (departmentId && Number(departmentId) > 0) queryParams.department_id = Number(departmentId);

  const response = await apiClient.get('/attendance/daily-status', { params: queryParams });
  return response.data;
}

/**
 * Retrieves chronological attendance history for an employee.
 * @param {string} employeeIdentifier
 * @param {Object} [params={}]
 * @param {number} [params.page=1]
 * @param {number} [params.pageSize=10]
 * @param {string} [params.startDate='']
 * @param {string} [params.endDate='']
 * @param {string} [params.sortOrder='desc']
 * @returns {Promise<{ items: Array, total: number, page: number, page_size: number, total_pages: number }>}
 */
export async function getEmployeeAttendanceHistoryApi(
  employeeIdentifier,
  { page = 1, pageSize = 10, startDate = '', endDate = '', sortOrder = 'desc' } = {}
) {
  const queryParams = {
    page,
    page_size: pageSize,
    sort_order: sortOrder,
  };

  if (startDate) queryParams.start_date = startDate;
  if (endDate) queryParams.end_date = endDate;

  const response = await apiClient.get(
    `/employees/${encodeURIComponent(employeeIdentifier.trim())}/attendance`,
    { params: queryParams }
  );
  return response.data;
}

/**
 * Calculates human-readable shift duration between check-in and check-out timestamps.
 * @param {string|null} checkInStr
 * @param {string|null} checkOutStr
 * @returns {string}
 */
export function calculateShiftDuration(checkInStr, checkOutStr) {
  if (!checkInStr || !checkOutStr) return '—';
  try {
    const start = new Date(checkInStr).getTime();
    const end = new Date(checkOutStr).getTime();
    if (isNaN(start) || isNaN(end) || end < start) return '—';
    const totalMinutes = Math.floor((end - start) / 60000);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    if (hours === 0) return `${minutes}m`;
    return `${hours}h ${minutes}m`;
  } catch {
    return '—';
  }
}
