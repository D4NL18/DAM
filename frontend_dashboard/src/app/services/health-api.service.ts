import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

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
  private apiUrl = 'http://35.254.233.21:8000/api/v1/health';

  constructor(private http: HttpClient) {}

  getSummary(startDate: string, endDate: string): Observable<HealthSummary> {
    return this.http.get<HealthSummary>(`${this.apiUrl}/summary?startDate=${startDate}&endDate=${endDate}`);
  }
}
