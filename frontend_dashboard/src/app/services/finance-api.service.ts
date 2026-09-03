import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

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
  private apiUrl = 'http://35.254.233.21:8000/api/v1/finance';

  constructor(private http: HttpClient) {}

  getMonthlySummary(year: number, month: number): Observable<FinanceSummary> {
    return this.http.get<FinanceSummary>(`${this.apiUrl}/monthly-summary?year=${year}&month=${month}`);
  }
}
