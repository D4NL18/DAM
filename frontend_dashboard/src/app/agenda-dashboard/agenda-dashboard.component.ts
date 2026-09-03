import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AgendaApiService, AgendaSummary, CalendarEvent } from '../services/agenda-api.service';

@Component({
  selector: 'app-agenda-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './agenda-dashboard.component.html',
  styleUrl: './agenda-dashboard.component.scss'
})
export class AgendaDashboardComponent implements OnInit {
  summary: AgendaSummary | null = null;
  loading = true;
  selectedFilter: 'todos' | 'trabalho' | 'pessoal' | 'saude' | 'reuniao' = 'todos';
  selectedPeriod: 'hoje' | 'semana' | 'mes' = 'hoje';
  todayFormatted: string = '';

  daysOfWeek: Array<{ dayName: string; dayNumber: number; active: boolean; hasEvents: boolean }> = [];

  constructor(private agendaApi: AgendaApiService) {}

  ngOnInit(): void {
    const today = new Date();
    const options: Intl.DateTimeFormatOptions = { weekday: 'long', day: 'numeric', month: 'long' };
    this.todayFormatted = today.toLocaleDateString('pt-BR', options);

    this.setupWeekDays(today);

    this.agendaApi.getAgendaSummary().subscribe({
      next: (data) => {
        this.summary = data;
        this.loading = false;
      },
      error: (err) => {
        console.error('Erro ao buscar dados da agenda:', err);
        this.loading = false;
      }
    });
  }

  private setupWeekDays(today: Date): void {
    const dayOfWeek = today.getDay(); // 0 (Dom) a 6 (Sáb)
    const sunday = new Date(today);
    sunday.setDate(today.getDate() - dayOfWeek);

    const weekNames = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];

    this.daysOfWeek = [];
    for (let i = 0; i < 7; i++) {
      const current = new Date(sunday);
      current.setDate(sunday.getDate() + i);
      this.daysOfWeek.push({
        dayName: weekNames[i],
        dayNumber: current.getDate(),
        active: current.toDateString() === today.toDateString(),
        hasEvents: false
      });
    }
  }

  get filteredEvents(): CalendarEvent[] {
    if (!this.summary) return [];
    if (this.selectedFilter === 'todos') {
      return this.summary.upcomingEvents;
    }
    return this.summary.upcomingEvents.filter(ev => ev.category === this.selectedFilter);
  }

  setFilter(filter: 'todos' | 'trabalho' | 'pessoal' | 'saude' | 'reuniao'): void {
    this.selectedFilter = filter;
  }

  setPeriod(period: 'hoje' | 'semana' | 'mes'): void {
    this.selectedPeriod = period;
  }

  toggleReminder(id: string): void {
    if (!this.summary) return;
    const reminder = this.summary.reminders.find(r => r.id === id);
    if (reminder) {
      reminder.completed = !reminder.completed;
    }
  }

  selectDay(selectedDay: { dayName: string; dayNumber: number; active: boolean; hasEvents: boolean }): void {
    this.daysOfWeek.forEach(d => d.active = false);
    selectedDay.active = true;
  }
}
