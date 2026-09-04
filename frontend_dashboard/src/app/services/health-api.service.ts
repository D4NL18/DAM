import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

export interface HealthSummary {
  totalSteps: number;
  avgHeartRate: number;
  totalActiveEnergyBurned: number;
  dailyRecords: Array<{
    date: string;
    steps: number;
    activeEnergyBurned: number;
  }>;
}

@Injectable({
  providedIn: 'root'
})
export class HealthApiService {
  private apiUrl = 'https://dam-backend-557716987299.us-central1.run.app/api/v1/health';

  constructor(private http: HttpClient, private authService: AuthService) {}

  getSummary(startDate: string, endDate: string): Observable<HealthSummary> {
    const userId = this.authService.getCurrentUser()?.userId || 'daniel';
    const headers = new HttpHeaders({ 'X-User-Id': userId });
    return this.http.get<HealthSummary>(`${this.apiUrl}/summary?startDate=${startDate}&endDate=${endDate}&userId=${userId}`, { headers });
  }
}