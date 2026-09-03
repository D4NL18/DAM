import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  startTime: string;
  endTime: string;
  location?: string;
  meetUrl?: string;
  category: 'trabalho' | 'pessoal' | 'saude' | 'reuniao';
  status: 'confirmed' | 'in_progress' | 'pending';
}

export interface AgendaSummary {
  todayTotalEvents: number;
  totalMeetingHours: number;
  nextEvent: CalendarEvent;
  upcomingEvents: CalendarEvent[];
  insights: Array<{
    type: 'traffic' | 'focus' | 'reminder';
    icon: string;
    title: string;
    text: string;
  }>;
  reminders: Array<{
    id: string;
    text: string;
    dueTime: string;
    completed: boolean;
  }>;
}

@Injectable({
  providedIn: 'root'
})
export class AgendaApiService {
  private apiUrl = 'https://dam-backend-557716987299.us-central1.run.app/api/v1/agenda';

  constructor(private http: HttpClient) {}

  getAgendaSummary(): Observable<AgendaSummary> {
    const emptyState: AgendaSummary = {
      todayTotalEvents: 0,
      totalMeetingHours: 0,
      nextEvent: null as any,
      upcomingEvents: [],
      insights: [],
      reminders: []
    };

    return this.http.get<AgendaSummary>(`${this.apiUrl}/summary`).pipe(
      catchError(err => {
        console.warn('Erro ao consultar API de agenda, retornando estado real zerado:', err);
        return of(emptyState);
      })
    );
  }
}
