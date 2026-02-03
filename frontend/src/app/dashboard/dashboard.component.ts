import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Router } from '@angular/router';

import { AuthService } from '../core/auth.service';
import { DashboardCharts, DashboardService, DashboardStats } from '../core/dashboard.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  stats: DashboardStats | null = null;
  charts: DashboardCharts | null = null;
  isLoading = false;
  calendarMonth = new Date();
  calendarDays: Array<{
    label: number | null;
    date: Date | null;
    isToday: boolean;
    isSelected: boolean;
  }> = [];
  selectedDate: Date | null = null;

  private readonly monthNames = [
    'Enero',
    'Febrero',
    'Marzo',
    'Abril',
    'Mayo',
    'Junio',
    'Julio',
    'Agosto',
    'Septiembre',
    'Octubre',
    'Noviembre',
    'Diciembre',
  ];

  private dashboardService = inject(DashboardService);
  private authService = inject(AuthService);
  private router = inject(Router);

  ngOnInit() {
    this.loadStats();
    this.loadCharts();
    this.buildCalendar();
  }

  loadStats() {
    this.isLoading = true;
    this.dashboardService.getStats().subscribe({
      next: (stats) => {
        this.stats = stats;
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      },
    });
  }

  loadCharts() {
    this.dashboardService.getCharts().subscribe({
      next: (charts) => {
        this.charts = charts;
      },
    });
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  getMonthlyMax() {
    if (!this.charts?.monthly?.length) {
      return 1;
    }
    return Math.max(
      1,
      ...this.charts.monthly.map((item) => Math.max(item.ingreso, item.egreso))
    );
  }

  getDistributionMax() {
    if (!this.charts?.distribution?.length) {
      return 1;
    }
    return Math.max(1, ...this.charts.distribution.map((item) => item.total));
  }

  getTrendMax() {
    if (!this.charts?.trend?.length) {
      return 1;
    }
    return Math.max(1, ...this.charts.trend.map((item) => item.total));
  }

  getMonthLabel() {
    const month = this.calendarMonth.getMonth();
    const year = this.calendarMonth.getFullYear();
    return `${this.monthNames[month]} ${year}`;
  }

  prevMonth() {
    this.calendarMonth = new Date(
      this.calendarMonth.getFullYear(),
      this.calendarMonth.getMonth() - 1,
      1
    );
    this.buildCalendar();
  }

  nextMonth() {
    this.calendarMonth = new Date(
      this.calendarMonth.getFullYear(),
      this.calendarMonth.getMonth() + 1,
      1
    );
    this.buildCalendar();
  }

  selectDay(day: { date: Date | null }) {
    if (!day.date) {
      return;
    }
    this.selectedDate = day.date;
    this.buildCalendar();
  }

  private buildCalendar() {
    const year = this.calendarMonth.getFullYear();
    const month = this.calendarMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const totalDays = lastDay.getDate();
    const startOffset = (firstDay.getDay() + 6) % 7;
    const today = new Date();

    const days: Array<{
      label: number | null;
      date: Date | null;
      isToday: boolean;
      isSelected: boolean;
    }> = [];

    for (let i = 0; i < startOffset; i += 1) {
      days.push({ label: null, date: null, isToday: false, isSelected: false });
    }

    for (let day = 1; day <= totalDays; day += 1) {
      const date = new Date(year, month, day);
      const isToday =
        date.getFullYear() === today.getFullYear() &&
        date.getMonth() === today.getMonth() &&
        date.getDate() === today.getDate();
      const isSelected =
        !!this.selectedDate &&
        date.getFullYear() === this.selectedDate.getFullYear() &&
        date.getMonth() === this.selectedDate.getMonth() &&
        date.getDate() === this.selectedDate.getDate();

      days.push({ label: day, date, isToday, isSelected });
    }

    this.calendarDays = days;
  }
}
