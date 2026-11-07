import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AgendaApiService, AgendaSummary, CalendarEvent, ReminderItem } from '../services/agenda-api.service';

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
    this.loadAgenda();
  }

  loadAgenda(): void {
    this.loading = true;
    this.agendaApi.getAgendaSummary(this.selectedPeriod).subscribe({
      next: (data) => {
        this.summary = data;
        this.loading = false;
        this.updateWeekDaysEvents();
      },
      error: (err) => {
        console.error('Erro ao buscar dados da agenda:', err);
        this.loading = false;
      }
    });
  }

  private updateWeekDaysEvents(): void {
    if (!this.summary || !this.summary.upcomingEvents) return;
    const eventTimes = this.summary.upcomingEvents.map(e => e.startTime);
    this.daysOfWeek.forEach(d => {
      const diaFormatado = d.dayNumber.toString().padStart(2, '0');
      d.hasEvents = eventTimes.some(t => t.startsWith(diaFormatado + '/') || (d.active && this.summary!.todayTotalEvents > 0));
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
        active: false,
        hasEvents: false
      });
    }
  }

  get selectedDay(): { dayName: string; dayNumber: number; active: boolean; hasEvents: boolean } | undefined {
    return this.daysOfWeek.find(d => d.active);
  }

  get filteredEvents(): CalendarEvent[] {
    if (!this.summary) return [];
    let list = this.summary.upcomingEvents || [];

    const activeDay = this.selectedDay;
    if (activeDay) {
      const diaPrefix = activeDay.dayNumber.toString().padStart(2, '0') + '/';
      list = list.filter(ev => {
        if (!ev.startTime) return false;
        if (ev.startTime.startsWith(diaPrefix)) return true;
        const isToday = this.isTodayNumber(activeDay.dayNumber);
        return !ev.startTime.includes('/') && isToday;
      });
    }

    if (this.selectedFilter === 'todos') {
      return list;
    }
    return list.filter(ev => ev.category === this.selectedFilter);
  }

  get filteredReminders(): ReminderItem[] {
    if (!this.summary) return [];
    const list = this.summary.reminders || [];
    const activeDay = this.selectedDay;
    if (!activeDay) return list;

    const diaPrefix = activeDay.dayNumber.toString().padStart(2, '0') + '/';
    return list.filter(r => {
      if (!r.dueTime) return true;
      if (r.dueTime.startsWith(diaPrefix)) return true;
      const isToday = this.isTodayNumber(activeDay.dayNumber);
      return !r.dueTime.includes('/') && isToday;
    });
  }

  get filteredReminderHistory(): ReminderItem[] {
    if (!this.summary) return [];
    const list = this.summary.reminderHistory || [];
    const activeDay = this.selectedDay;
    if (!activeDay) return list;

    const diaPrefix = activeDay.dayNumber.toString().padStart(2, '0') + '/';
    return list.filter(r => {
      if (!r.dueTime) return true;
      if (r.dueTime.startsWith(diaPrefix)) return true;
      const isToday = this.isTodayNumber(activeDay.dayNumber);
      return !r.dueTime.includes('/') && isToday;
    });
  }

  private isTodayNumber(dayNum: number): boolean {
    return new Date().getDate() === dayNum;
  }

  activeRemindersTab: 'ativos' | 'historico' = 'ativos';

  setFilter(filter: 'todos' | 'trabalho' | 'pessoal' | 'saude' | 'reuniao'): void {
    this.selectedFilter = filter;
  }

  setPeriod(period: 'hoje' | 'semana' | 'mes'): void {
    if (this.selectedPeriod === period) return;
    this.selectedPeriod = period;
    this.daysOfWeek.forEach(d => d.active = false);
    this.loadAgenda();
  }

  toggleReminder(id: string): void {
    if (!this.summary) return;
    const reminder = this.summary.reminders.find(r => r.id === id);
    if (reminder) {
      reminder.completed = !reminder.completed;
      this.agendaApi.toggleReminder(id).subscribe({
        next: () => {
          setTimeout(() => this.loadAgenda(), 400);
        }
      });
    } else {
      const hist = this.summary.reminderHistory?.find(r => r.id === id);
      if (hist) {
        hist.completed = !hist.completed;
        this.agendaApi.toggleReminder(id).subscribe({
          next: () => {
            setTimeout(() => this.loadAgenda(), 400);
          }
        });
      }
    }
  }

  selectDay(selectedDay: { dayName: string; dayNumber: number; active: boolean; hasEvents: boolean }): void {
    const wasActive = selectedDay.active;
    this.daysOfWeek.forEach(d => d.active = false);
    if (!wasActive) {
      selectedDay.active = true;
    }
  }
}
