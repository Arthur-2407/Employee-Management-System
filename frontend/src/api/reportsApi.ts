import api from '@services/api';
import { AxiosResponse } from 'axios';

export interface ReportStats {
  totalCheckins: number;
  averageHours: string;
  geoFenceCompliance: string;
  lateArrivals: number;
}

export interface ReportLeaveStats {
  totalRequests: number;
  approved: number;
  pending: number;
  rejected: number;
  vacationDaysUsed: number;
  sickDaysUsed: number;
  totalApprovedDays: number;
}

export interface WeeklyReportData {
  week: string;
  hours: number;
  lateArrivals: number;
}

export interface DepartmentReportData {
  department: string;
  employees: number;
  attendanceRate: number;
}

export interface ReportsResponse {
  success: boolean;
  period: {
    startDate: string;
    endDate: string;
  };
  stats: ReportStats;
  leave: ReportLeaveStats;
  weekly: WeeklyReportData[];
  departments: DepartmentReportData[];
}

export const reportsApi = {
  getReports: async (period: string = 'month'): Promise<AxiosResponse<ReportsResponse>> => {
    const response = await api.get<ReportsResponse>('/reports', { params: { period } });
    return response;
  },

  getAttendanceReport: async (params: { startDate?: string; endDate?: string; employeeId?: string; limit?: number; offset?: number }): Promise<AxiosResponse<{ success: boolean; count: number; data: any[] }>> => {
    const response = await api.get('/reports/attendance', { params });
    return response;
  },

  getManagedEmployees: async (): Promise<AxiosResponse<{ success: boolean; data: any[] }>> => {
    const response = await api.get('/reports/managed-employees');
    return response;
  },

  downloadAttendanceExcel: async (params: { startDate?: string; endDate?: string; department?: string; employeeId?: string }): Promise<AxiosResponse<Blob>> => {
    const response = await api.get('/excel/attendance', {
      params: {
        start_date: params.startDate,
        end_date: params.endDate,
        department: params.department,
        employee_id: params.employeeId,
      },
      responseType: 'blob'
    });
    return response;
  },

  downloadLeaveExcel: async (params: { startDate?: string; endDate?: string; employeeId?: string }): Promise<AxiosResponse<Blob>> => {
    const response = await api.get('/excel/leave', {
      params: {
        start_date: params.startDate,
        end_date: params.endDate,
        employee_id: params.employeeId,
      },
      responseType: 'blob'
    });
    return response;
  },
};
