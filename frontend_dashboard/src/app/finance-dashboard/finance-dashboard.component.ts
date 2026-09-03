import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgxEchartsModule } from 'ngx-echarts';
import type { EChartsOption } from 'echarts';
import { FinanceApiService, FinanceSummary } from '../services/finance-api.service';
import { catchError, of } from 'rxjs';

@Component({
  selector: 'app-finance-dashboard',
  standalone: true,
  imports: [CommonModule, NgxEchartsModule],
  templateUrl: './finance-dashboard.component.html',
  styleUrl: './finance-dashboard.component.scss'
})
export class FinanceDashboardComponent implements OnInit {
  summary: FinanceSummary | null = null;
  loading = true;
  chartOption: EChartsOption = {};

  constructor(private financeApi: FinanceApiService) {}

  ngOnInit(): void {
    const now = new Date();
    
    this.financeApi.getMonthlySummary(now.getFullYear(), now.getMonth() + 1)
      .pipe(
        catchError(err => {
          console.error('Erro ao buscar dados financeiros do Firestore:', err);
          return of({
            totalSpent: 0.0,
            currency: 'BRL',
            expensesByCategory: [],
            recentTransactions: []
          });
        })
      )
      .subscribe(data => {
        this.summary = data;
        this.initChart(data);
        this.loading = false;
      });
  }

  initChart(data: FinanceSummary) {
    if (!data.expensesByCategory || data.expensesByCategory.length === 0) {
      this.chartOption = {
        title: {
          text: 'Nenhuma despesa registrada',
          subtext: 'Cadastre gastos pelo WhatsApp para visualizar o gráfico',
          left: 'center',
          top: 'center',
          textStyle: { color: '#94a3b8', fontSize: 14 }
        }
      };
      return;
    }

    const pieData = data.expensesByCategory.map(e => ({
      name: e.category,
      value: e.amount
    }));

    this.chartOption = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)',
        backgroundColor: 'rgba(30, 41, 59, 0.9)',
        borderColor: 'rgba(255,255,255,0.1)',
        textStyle: { color: '#fff' }
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        textStyle: { color: '#94a3b8' }
      },
      series: [
        {
          name: 'Despesas',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: 'rgba(30, 41, 59, 1)',
            borderWidth: 2
          },
          label: { show: false, position: 'center' },
          emphasis: {
            label: { show: true, fontSize: 20, fontWeight: 'bold', color: '#fff' }
          },
          labelLine: { show: false },
          data: pieData
        }
      ]
    };
  }
}
