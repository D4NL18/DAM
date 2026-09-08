import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgxEchartsModule } from 'ngx-echarts';
import type { EChartsOption } from 'echarts';
import { HealthApiService, HealthSummary } from '../services/health-api.service';
import { catchError, of } from 'rxjs';

@Component({
  selector: 'app-health-dashboard',
  standalone: true,
  imports: [CommonModule, NgxEchartsModule],
  templateUrl: './health-dashboard.component.html',
  styleUrl: './health-dashboard.component.scss'
})
export class HealthDashboardComponent implements OnInit {
  summary: HealthSummary | null = null;
  loading = true;
  chartOption: EChartsOption = {};

  constructor(private healthApi: HealthApiService) {}

  ngOnInit(): void {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - 7);
    
    const startStr = start.toISOString().split('T')[0];
    const endStr = end.toISOString().split('T')[0];

    this.healthApi.getSummary(startStr, endStr)
      .pipe(
        catchError(err => {
          console.warn('Erro ao consultar Firestore health_metrics, retornando zerado:', err);
          return of({
            totalSteps: 0,
            avgHeartRate: 0,
            totalActiveEnergyBurned: 0,
            dailyRecords: []
          });
        })
      )
      .subscribe(data => {
        this.summary = data;
        this.initChart(data);
        this.loading = false;
      });
  }

  initChart(data: HealthSummary) {
    if (!data.dailyRecords || data.dailyRecords.length === 0) {
      this.chartOption = {
        title: {
          text: 'Sem dados de saúde recentes',
          subtext: 'Envie métricas pelo webhook do Health Auto Export para visualizar',
          left: 'center',
          top: 'center',
          textStyle: { color: '#94a3b8', fontSize: 14 }
        }
      };
      return;
    }

    const dates = data.dailyRecords.map(r => r.date);
    const steps = data.dailyRecords.map(r => r.steps);
    const energy = data.dailyRecords.map(r => r.activeEnergyBurned);

    this.chartOption = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(30, 41, 59, 0.9)',
        borderColor: 'rgba(255,255,255,0.1)',
        textStyle: { color: '#fff' }
      },
      legend: {
        data: ['Passos', 'Calorias (kcal)'],
        textStyle: { color: '#94a3b8' },
        bottom: 0
      },
      grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { color: '#94a3b8' }
      },
      yAxis: [
        {
          type: 'value',
          name: 'Passos',
          nameTextStyle: { color: '#94a3b8' },
          splitLine: { lineStyle: { color: '#334155', type: 'dashed' } },
          axisLabel: { color: '#94a3b8' }
        },
        {
          type: 'value',
          name: 'Calorias',
          nameTextStyle: { color: '#94a3b8' },
          splitLine: { show: false },
          axisLabel: { color: '#94a3b8' }
        }
      ],
      series: [
        {
          name: 'Passos',
          type: 'bar',
          data: steps,
          itemStyle: { color: '#6366f1', borderRadius: [4, 4, 0, 0] }
        },
        {
          name: 'Calorias (kcal)',
          type: 'line',
          yAxisIndex: 1,
          data: energy,
          smooth: true,
          lineStyle: { color: '#ec4899', width: 3 },
          itemStyle: { color: '#ec4899' },
          areaStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(236, 72, 153, 0.5)' },
                { offset: 1, color: 'rgba(236, 72, 153, 0)' }
              ]
            }
          }
        }
      ]
    };
  }
}
