import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

export interface FinanceCategory {
  id: string;
  name: string;
  color: string;
}

export interface FinanceCard {
  id: string;
  name: string;
  type: string; // 'credito' | 'debito' | 'beneficio' | 'outro'
}

export interface FinanceTransaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  category: string;
  categoryColor?: string;
  type: 'expense_variable' | 'expense_fixed' | 'income';
  paymentMethod?: string;
  installment?: string;
  owner?: string;
}

export interface CategoryBreakdown {
  category: string;
  amount: number;
  percentage: number;
  color: string;
}

export interface FinanceDashboardData {
  totalSpent: number;
  totalIncome: number;
  totalFixed: number;
  totalVariable: number;
  balance: number;
  currency: string;
  expensesByCategory: CategoryBreakdown[];
  transactions: FinanceTransaction[];
}

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

export interface FinanceTrendSeriesItem {
  label: string;
  year: number;
  month: number;
  income: number;
  expenses: number;
  balance: number;
}

export interface FinanceTrendComparison {
  hasPreviousPeriod: boolean;
  incomeChangePct: number;
  expenseChangePct: number;
  comparisonText: string;
}

export interface FinanceTrendData {
  period: string;
  periodLabel: string;
  totalIncome: number;
  totalExpenses: number;
  periodBalance: number;
  currency: string;
  comparison: FinanceTrendComparison;
  series: FinanceTrendSeriesItem[];
}

@Injectable({
  providedIn: 'root'
})
export class FinanceApiService {
  private apiUrl = 'https://dam-backend-557716987299.us-central1.run.app/api/v1/finance';

  constructor(private http: HttpClient, private authService: AuthService) {}

  private getHeaders(): HttpHeaders {
    const userId = this.authService.getCurrentUser()?.userId || 'daniel';
    return new HttpHeaders({ 'X-User-Id': userId });
  }

  getDashboard(year: number, month: number, type?: string, category?: string): Observable<FinanceDashboardData> {
    const userId = this.authService.getCurrentUser()?.userId || 'daniel';
    let url = `${this.apiUrl}/dashboard?year=${year}&month=${month}&userId=${userId}`;
    if (type) {
      url += `&type=${encodeURIComponent(type)}`;
    }
    if (category) {
      url += `&category=${encodeURIComponent(category)}`;
    }
    return this.http.get<FinanceDashboardData>(url, { headers: this.getHeaders() });
  }

  getMonthlySummary(year: number, month: number): Observable<FinanceSummary> {
    const userId = this.authService.getCurrentUser()?.userId || 'daniel';
    return this.http.get<FinanceSummary>(`${this.apiUrl}/monthly-summary?year=${year}&month=${month}&userId=${userId}`, { headers: this.getHeaders() });
  }

  createTransaction(tx: Partial<FinanceTransaction>): Observable<FinanceTransaction> {
    return this.http.post<FinanceTransaction>(`${this.apiUrl}/transactions`, tx, { headers: this.getHeaders() });
  }

  updateTransaction(id: string, tx: Partial<FinanceTransaction>): Observable<any> {
    return this.http.put(`${this.apiUrl}/transactions/${id}`, tx, { headers: this.getHeaders() });
  }

  deleteTransaction(id: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/transactions/${id}`, { headers: this.getHeaders() });
  }

  getCategories(): Observable<FinanceCategory[]> {
    return this.http.get<FinanceCategory[]>(`${this.apiUrl}/categories`, { headers: this.getHeaders() });
  }

  createCategory(cat: { name: string; color: string }): Observable<FinanceCategory> {
    return this.http.post<FinanceCategory>(`${this.apiUrl}/categories`, cat, { headers: this.getHeaders() });
  }

  updateCategory(id: string, cat: { name: string; color: string }): Observable<any> {
    return this.http.put(`${this.apiUrl}/categories/${id}`, cat, { headers: this.getHeaders() });
  }

  deleteCategory(id: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/categories/${id}`, { headers: this.getHeaders() });
  }

  getCards(): Observable<FinanceCard[]> {
    return this.http.get<FinanceCard[]>(`${this.apiUrl}/cards`, { headers: this.getHeaders() });
  }

  createCard(card: { name: string; type: string }): Observable<FinanceCard> {
    return this.http.post<FinanceCard>(`${this.apiUrl}/cards`, card, { headers: this.getHeaders() });
  }

  updateCard(id: string, card: { name: string; type: string }): Observable<any> {
    return this.http.put(`${this.apiUrl}/cards/${id}`, card, { headers: this.getHeaders() });
  }

  deleteCard(id: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/cards/${id}`, { headers: this.getHeaders() });
  }

  getTrends(period: string = '12m', startDate?: string, endDate?: string): Observable<FinanceTrendData> {
    const userId = this.authService.getCurrentUser()?.userId || 'daniel';
    let url = `${this.apiUrl}/trends?period=${period}&userId=${userId}`;
    if (startDate) url += `&startDate=${startDate}`;
    if (endDate) url += `&endDate=${endDate}`;
    return this.http.get<FinanceTrendData>(url, { headers: this.getHeaders() });
  }
}