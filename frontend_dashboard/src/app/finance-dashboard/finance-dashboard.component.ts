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
          console.error('Erro ao buscar dados financeiros', err);
          return of({
            totalSpent: 3500.75,
            currency: 'BRL',
            expensesByCategory: [
              { category: 'Alimentação', amount: 1200.00 },
              { category: 'Transporte', amount: 400.00 },
              { category: 'Lazer', amount: 600.00 },
              { category: 'Moradia', amount: 1300.75 }
            ],
            recentTransactions: [
              { id: 'tx_1', date: '2024-03-05T14:30:00Z', description: 'Supermercado Extra', amount: 250.00, category: 'Alimentação' },
              { id: 'tx_2', date: '2024-03-06T09:15:00Z', description: 'Uber', amount: 45.50, category: 'Transporte' },
              { id: 'tx_3', date: '2024-03-08T20:00:00Z', description: 'Cinema', amount: 80.00, category: 'Lazer' }
            ]
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
