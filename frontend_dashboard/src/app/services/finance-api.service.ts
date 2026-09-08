import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

export interface FinanceSummary {
  totalSpent: number;
  currency: string;
  expensesByCategory: Array<{
    category: string;
    amount: number;
  }>;
  recentTransactions: Array<{
    id: string;
    date: string;
    description: string;
    amount: number;
    category: string;
  }>;
}

@Injectable({
  providedIn: 'root'
})
export class FinanceApiService {
  private apiUrl = 'https://dam-backend-557716987299.us-central1.run.app/api/v1/finance';

  constructor(private http: HttpClient, private authService: AuthService) {}

  getMonthlySummary(year: number, month: number): Observable<FinanceSummary> {
    const userId = this.authService.getCurrentUser()?.userId || 'daniel';
    const headers = new HttpHeaders({ 'X-User-Id': userId });
    return this.http.get<FinanceSummary>(`${this.apiUrl}/monthly-summary?year=${year}&month=${month}&userId=${userId}`, { headers });
  }
}