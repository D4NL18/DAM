import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgxEchartsModule } from 'ngx-echarts';
import type { EChartsOption } from 'echarts';
import {
  FinanceApiService,
  FinanceDashboardData,
  FinanceTransaction,
  FinanceCategory,
  FinanceCard,
  CategoryBreakdown,
  FinanceTrendData,
  FinanceTrendSeriesItem
} from '../services/finance-api.service';
import { AuthService } from '../services/auth.service';
import { catchError, of } from 'rxjs';

@Component({
  selector: 'app-finance-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, NgxEchartsModule],
  templateUrl: './finance-dashboard.component.html',
  styleUrl: './finance-dashboard.component.scss'
})
export class FinanceDashboardComponent implements OnInit {
  dashboardData: FinanceDashboardData | null = null;
  loading = true;
  chartOption: EChartsOption = {};

  // Modo de visualização principal: 'monthly' (visão do mês detalhada) ou 'trends' (andamento/evolução por períodos)
  activeView: 'monthly' | 'trends' = 'monthly';

  // --- Evolução Temporal (FG-07) ---
  trendPeriod: 'current_month' | '3m' | '6m' | '12m' | 'custom' = '12m';
  trendData: FinanceTrendData | null = null;
  trendLoading = false;
  trendChartOption: EChartsOption = {};
  showCustomDateModal = false;
  customStartDate = '';
  customEndDate = '';

  // Controles de data e visualização mensal
  currentYear: number = new Date().getFullYear();
  currentMonth: number = new Date().getMonth() + 1; // 1-indexed
  currentTab: 'total' | 'expense_variable' | 'expense_fixed' | 'income' = 'total';
  hideValues: boolean = false;
  sortAscending: boolean = false;

  // Filtros
  selectedCategoryFilter: string = '';
  isFilterOpen: boolean = false;

  // Modais
  showManageModal: boolean = false;
  manageActiveTab: 'categories' | 'cards' = 'categories';
  showTransactionModal: boolean = false;
  editingTransaction: FinanceTransaction | null = null;
  showImportModal: boolean = false;

  // Modal de Confirmação Personalizado (substitui window.confirm)
  confirmModal = {
    isOpen: false,
    title: '',
    message: '',
    confirmButtonText: 'Confirmar',
    cancelButtonText: 'Cancelar',
    isDanger: true,
    action: () => {}
  };

  // Notificações Toast de Sucesso e Erro (substitui window.alert)
  toastNotification = {
    show: false,
    type: 'success' as 'success' | 'error' | 'warning' | 'info',
    title: '',
    message: ''
  };
  private toastTimer: any = null;

  // Categorias e Cartões
  categories: FinanceCategory[] = [];
  cards: FinanceCard[] = [];

  // Formulários inline
  newCategoryName: string = '';
  newCategoryColor: string = '#3B82F6';
  editingCategory: FinanceCategory | null = null;

  newCardName: string = '';
  newCardType: string = 'credito';
  editingCard: FinanceCard | null = null;

  // Formulário de Transação
  txForm: {
    description: string;
    amount: number | null;
    category: string;
    type: 'expense_variable' | 'expense_fixed' | 'income';
    paymentMethod: string;
    installment: string;
    owner: string;
    date: string;
  } = {
    description: '',
    amount: null,
    category: 'Mercado',
    type: 'expense_variable',
    paymentMethod: 'Cartão de Crédito Pessoal',
    installment: '',
    owner: '',
    date: new Date().toISOString().substring(0, 10)
  };

  // Paleta de cores para categorias
  colorPalette: string[] = [
    '#2563eb', '#eab308', '#86efac', '#15803d', '#22c55e', '#1e3a8a',
    '#a855f7', '#f472b6', '#7e22ce', '#06b6d4', '#f97316', '#ef4444',
    '#10b981', '#6366f1', '#64748b', '#ec4899', '#84cc16', '#0ea5e9'
  ];

  monthNames: string[] = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];

  constructor(
    private financeApi: FinanceApiService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadCategoriesAndCards();
    this.loadDashboard();
    this.loadTrends();
  }

  get userDisplayName(): string {
    const user = this.authService.getCurrentUser();
    return user?.name || 'Daniel';
  }

  get currentMonthLabel(): string {
    return `${this.monthNames[this.currentMonth - 1]} de ${this.currentYear}`;
  }

  get tabTitle(): string {
    if (this.currentTab === 'total') return 'Todas as transações';
    if (this.currentTab === 'expense_variable') return 'Despesas variáveis';
    if (this.currentTab === 'expense_fixed') return 'Despesas fixas';
    return 'Receitas';
  }

  get filteredTransactions(): FinanceTransaction[] {
    if (!this.dashboardData?.transactions) return [];
    let list = [...this.dashboardData.transactions];

    if (this.selectedCategoryFilter) {
      list = list.filter(t => t.category.toLowerCase() === this.selectedCategoryFilter.toLowerCase());
    }

    list.sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return this.sortAscending ? dateA - dateB : dateB - dateA;
    });

    return list;
  }

  get periodTotalDisplay(): number {
    if (!this.dashboardData) return 0;
    if (this.currentTab === 'total') {
      return this.dashboardData.totalSpent + this.dashboardData.totalIncome;
    }
    if (this.currentTab === 'expense_variable') {
      return this.dashboardData.totalVariable;
    }
    if (this.currentTab === 'expense_fixed') {
      return this.dashboardData.totalFixed;
    }
    return this.dashboardData.totalIncome;
  }

  get netBalance(): number {
    return this.dashboardData?.balance || 0;
  }

  loadDashboard(): void {
    this.loading = true;
    this.financeApi.getDashboard(this.currentYear, this.currentMonth, this.currentTab, this.selectedCategoryFilter)
      .pipe(
        catchError(err => {
          console.error('Erro ao carregar dados do dashboard de finanças:', err);
          return of({
            totalSpent: 0,
            totalIncome: 0,
            totalFixed: 0,
            totalVariable: 0,
            balance: 0,
            currency: 'BRL',
            expensesByCategory: [],
            transactions: []
          });
        })
      )
      .subscribe(data => {
        this.dashboardData = data;
        this.initChart(data.expensesByCategory);
        this.loading = false;
      });
  }

  loadTrends(): void {
    this.trendLoading = true;
    this.financeApi.getTrends(this.trendPeriod, this.customStartDate, this.customEndDate)
      .pipe(
        catchError(err => {
          console.error('Erro ao carregar evolução temporal:', err);
          return of({
            period: this.trendPeriod,
            periodLabel: 'Período',
            totalIncome: 0,
            totalExpenses: 0,
            periodBalance: 0,
            currency: 'BRL',
            comparison: {
              hasPreviousPeriod: false,
              incomeChangePct: 0,
              expenseChangePct: 0,
              comparisonText: 'Sem período anterior'
            },
            series: []
          });
        })
      )
      .subscribe(data => {
        this.trendData = data;
        this.initTrendChart(data);
        this.trendLoading = false;
      });
  }

  setTrendPeriod(period: 'current_month' | '3m' | '6m' | '12m' | 'custom'): void {
    this.trendPeriod = period;
    if (period === 'custom') {
      this.showCustomDateModal = true;
    } else {
      this.loadTrends();
    }
  }

  applyCustomDates(): void {
    this.showCustomDateModal = false;
    this.loadTrends();
  }

  initTrendChart(data: FinanceTrendData): void {
    if (!data || !data.series || data.series.length === 0) {
      this.trendChartOption = {
        title: {
          text: 'Sem dados para o período',
          left: 'center',
          top: 'center',
          textStyle: { color: '#94a3b8', fontSize: 13 }
        }
      };
      return;
    }

    const xLabels = data.series.map(s => s.label);
    const incomeData = data.series.map(s => s.income);
    const expenseData = data.series.map(s => s.expenses);

    this.trendChartOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'line',
          lineStyle: { color: '#cbd5e1', width: 1, type: 'dashed' }
        },
        backgroundColor: 'rgba(15, 23, 42, 0.92)',
        borderWidth: 0,
        textStyle: { color: '#ffffff', fontSize: 12 },
        formatter: (params: any) => {
          if (!params || !params.length) return '';
          const monthTitle = params[0].axisValue;
          let html = `<div style="font-family: inherit; padding: 2px;"><strong>${monthTitle}</strong><br/>`;
          params.forEach((p: any) => {
            const valFormatted = this.hideValues
              ? '*****'
              : new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(p.value);
            html += `<span style="display:inline-block;margin-right:6px;width:8px;height:8px;border-radius:50%;background-color:${p.color};"></span>` +
                    `${p.seriesName}: <strong>${valFormatted}</strong><br/>`;
          });
          html += `</div>`;
          return html;
        }
      },
      grid: {
        top: 24,
        right: 16,
        bottom: 28,
        left: 56,
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: xLabels,
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisTick: { show: false },
        axisLabel: { color: '#64748b', fontSize: 11, margin: 12 }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: {
          show: true,
          lineStyle: { color: '#f1f5f9', type: 'dashed' }
        },
        axisLabel: {
          color: '#64748b',
          fontSize: 11,
          formatter: (value: number) => {
            if (value >= 1000) {
              return `${(value / 1000).toFixed(0)} mil`;
            }
            return `${value}`;
          }
        }
      },
      series: [
        {
          name: 'Receita',
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: { color: '#15803d', width: 3 },
          itemStyle: { color: '#15803d' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(21, 128, 61, 0.35)' },
                { offset: 1, color: 'rgba(21, 128, 61, 0.01)' }
              ]
            }
          },
          data: incomeData
        },
        {
          name: 'Gastos',
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: { color: '#dc2626', width: 2.5 },
          itemStyle: { color: '#dc2626' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(220, 38, 38, 0.25)' },
                { offset: 1, color: 'rgba(220, 38, 38, 0.01)' }
              ]
            }
          },
          data: expenseData
        }
      ]
    };
  }

  loadCategoriesAndCards(): void {
    this.financeApi.getCategories().subscribe({
      next: cats => {
        this.categories = cats;
        if (cats.length > 0 && !this.txForm.category) {
          this.txForm.category = cats[0].name;
        }
      },
      error: err => console.error('Erro ao carregar categorias:', err)
    });

    this.financeApi.getCards().subscribe({
      next: cards => {
        this.cards = cards;
        if (cards.length > 0 && !this.txForm.paymentMethod) {
          this.txForm.paymentMethod = cards[0].name;
        }
      },
      error: err => console.error('Erro ao carregar cartões:', err)
    });
  }

  // --- Navegação e Abas ---

  prevMonth(): void {
    if (this.currentMonth === 1) {
      this.currentMonth = 12;
      this.currentYear--;
    } else {
      this.currentMonth--;
    }
    this.loadDashboard();
  }

  nextMonth(): void {
    if (this.currentMonth === 12) {
      this.currentMonth = 1;
      this.currentYear++;
    } else {
      this.currentMonth++;
    }
    this.loadDashboard();
  }

  setTab(tab: 'total' | 'expense_variable' | 'expense_fixed' | 'income'): void {
    this.currentTab = tab;
    this.selectedCategoryFilter = '';
    if (tab !== 'total') {
      this.txForm.type = tab;
    }
    this.loadDashboard();
  }

  toggleHideValues(): void {
    this.hideValues = !this.hideValues;
    if (this.trendData) {
      this.initTrendChart(this.trendData);
    }
    if (this.dashboardData) {
      this.initChart(this.dashboardData.expensesByCategory);
    }
  }

  toggleSort(): void {
    this.sortAscending = !this.sortAscending;
  }

  // --- Filtro de Categoria ---

  toggleFilterPopover(): void {
    this.isFilterOpen = !this.isFilterOpen;
  }

  applyCategoryFilter(categoryName: string): void {
    if (this.selectedCategoryFilter === categoryName) {
      this.selectedCategoryFilter = '';
    } else {
      this.selectedCategoryFilter = categoryName;
    }
    this.isFilterOpen = false;
    this.loadDashboard();
  }

  clearCategoryFilter(): void {
    this.selectedCategoryFilter = '';
    this.isFilterOpen = false;
    this.loadDashboard();
  }

  // --- ECharts Donut ---

  initChart(breakdowns: CategoryBreakdown[]): void {
    if (!breakdowns || breakdowns.length === 0) {
      this.chartOption = {
        title: {
          text: 'Sem lançamentos no período',
          left: 'center',
          top: 'center',
          textStyle: { color: '#94a3b8', fontSize: 13, fontWeight: 'normal' }
        },
        series: []
      };
      return;
    }

    const data = breakdowns.map(item => ({
      name: item.category,
      value: item.amount,
      itemStyle: { color: item.color }
    }));

    this.chartOption = {
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const valFormatted = this.hideValues
            ? '••••••'
            : new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(params.value);
          return `<div style="font-family: inherit; font-size: 13px;">
                    <strong>${params.name}</strong><br/>
                    ${valFormatted} (${params.percent}%)
                  </div>`;
        },
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        borderWidth: 0,
        textStyle: { color: '#ffffff' }
      },
      series: [
        {
          name: 'Categorias',
          type: 'pie',
          radius: ['52%', '78%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#ffffff',
            borderWidth: 3
          },
          label: {
            show: false
          },
          emphasis: {
            scale: true,
            scaleSize: 8,
            label: {
              show: false
            }
          },
          data: data
        }
      ]
    };
  }

  onChartClick(params: any): void {
    if (params && params.name) {
      this.applyCategoryFilter(params.name);
    }
  }

  // --- CRUD de Transações ---

  openAddTransaction(): void {
    this.editingTransaction = null;
    this.txForm = {
      description: '',
      amount: null,
      category: this.categories.length > 0 ? this.categories[0].name : 'Mercado',
      type: this.currentTab === 'total' ? 'expense_variable' : this.currentTab,
      paymentMethod: this.cards.length > 0 ? this.cards[0].name : 'Cartão de Crédito Pessoal',
      installment: '',
      owner: '',
      date: new Date().toISOString().substring(0, 10)
    };
    this.showTransactionModal = true;
  }

  openEditTransaction(tx: FinanceTransaction): void {
    this.editingTransaction = tx;
    this.txForm = {
      description: tx.description,
      amount: tx.amount,
      category: tx.category,
      type: tx.type,
      paymentMethod: tx.paymentMethod || 'Cartão de Crédito Pessoal',
      installment: tx.installment || '',
      owner: (tx.owner && tx.owner !== 'Christian') ? tx.owner : '',
      date: tx.date ? tx.date.substring(0, 10) : new Date().toISOString().substring(0, 10)
    };
    this.showTransactionModal = true;
  }

  // --- Helpers de Feedback & Confirmação (Substitutos de alert/confirm) ---

  showToast(message: string, type: 'success' | 'error' | 'warning' | 'info' = 'success', title: string = ''): void {
    if (this.toastTimer) {
      clearTimeout(this.toastTimer);
    }
    this.toastNotification = {
      show: true,
      type,
      title,
      message
    };
    this.toastTimer = setTimeout(() => {
      this.toastNotification.show = false;
    }, 3800);
  }

  closeToast(): void {
    this.toastNotification.show = false;
    if (this.toastTimer) {
      clearTimeout(this.toastTimer);
    }
  }

  openConfirmDialog(options: {
    title: string;
    message: string;
    confirmButtonText?: string;
    cancelButtonText?: string;
    isDanger?: boolean;
    onConfirm: () => void;
  }): void {
    this.confirmModal = {
      isOpen: true,
      title: options.title,
      message: options.message,
      confirmButtonText: options.confirmButtonText || 'Confirmar',
      cancelButtonText: options.cancelButtonText || 'Cancelar',
      isDanger: options.isDanger ?? true,
      action: options.onConfirm
    };
  }

  onConfirmDialogProceed(): void {
    const action = this.confirmModal.action;
    this.confirmModal.isOpen = false;
    if (action) {
      action();
    }
  }

  onConfirmDialogCancel(): void {
    this.confirmModal.isOpen = false;
  }

  saveTransaction(): void {
    if (!this.txForm.description.trim() || !this.txForm.amount || this.txForm.amount <= 0) {
      this.showToast('Por favor, informe a descrição e um valor maior que zero.', 'warning');
      return;
    }

    const payload: Partial<FinanceTransaction> = {
      description: this.txForm.description.trim(),
      amount: Number(this.txForm.amount),
      category: this.txForm.category,
      type: this.txForm.type,
      paymentMethod: this.txForm.paymentMethod,
      installment: this.txForm.installment ? this.txForm.installment.trim() : undefined,
      owner: this.txForm.owner ? this.txForm.owner.trim() : undefined,
      date: this.txForm.date
    };

    if (this.editingTransaction) {
      this.financeApi.updateTransaction(this.editingTransaction.id, payload).subscribe({
        next: () => {
          this.showTransactionModal = false;
          this.showToast('Transação atualizada com sucesso!', 'success');
          this.loadDashboard();
          this.loadTrends();
        },
        error: err => {
          console.error('Erro ao atualizar transação:', err);
          this.showToast('Erro ao atualizar transação.', 'error');
        }
      });
    } else {
      this.financeApi.createTransaction(payload).subscribe({
        next: () => {
          this.showTransactionModal = false;
          this.showToast('Transação cadastrada com sucesso!', 'success');
          this.loadDashboard();
          this.loadTrends();
        },
        error: err => {
          console.error('Erro ao salvar transação:', err);
          this.showToast('Erro ao gravar transação.', 'error');
        }
      });
    }
  }

  deleteCurrentTransaction(): void {
    if (!this.editingTransaction) return;
    const tx = this.editingTransaction;
    this.openConfirmDialog({
      title: 'Excluir Transação',
      message: `Deseja realmente excluir a transação "${tx.description}"?`,
      confirmButtonText: 'Sim, Excluir',
      isDanger: true,
      onConfirm: () => {
        this.financeApi.deleteTransaction(tx.id).subscribe({
          next: () => {
            this.showTransactionModal = false;
            this.showToast('Transação excluída com sucesso!', 'success');
            this.loadDashboard();
            this.loadTrends();
          },
          error: err => {
            console.error('Erro ao excluir transação:', err);
            this.showToast('Erro ao excluir transação.', 'error');
          }
        });
      }
    });
  }

  // --- Gerenciador de Categorias & Cartões ---

  openManageModal(): void {
    this.showManageModal = true;
  }

  addCategory(): void {
    if (!this.newCategoryName.trim()) return;
    const name = this.newCategoryName.trim();
    this.financeApi.createCategory({
      name,
      color: this.newCategoryColor
    }).subscribe({
      next: () => {
        this.newCategoryName = '';
        this.showToast(`Categoria "${name}" criada com sucesso!`, 'success');
        this.loadCategoriesAndCards();
        this.loadDashboard();
      },
      error: err => {
        console.error('Erro ao criar categoria:', err);
        this.showToast('Erro ao criar categoria.', 'error');
      }
    });
  }

  startEditCategory(cat: FinanceCategory): void {
    this.editingCategory = { ...cat };
  }

  saveEditCategory(): void {
    if (!this.editingCategory || !this.editingCategory.name.trim()) return;
    const catName = this.editingCategory.name.trim();
    this.financeApi.updateCategory(this.editingCategory.id, {
      name: catName,
      color: this.editingCategory.color
    }).subscribe({
      next: () => {
        this.editingCategory = null;
        this.showToast(`Categoria "${catName}" atualizada!`, 'success');
        this.loadCategoriesAndCards();
        this.loadDashboard();
      },
      error: err => {
        console.error('Erro ao atualizar categoria:', err);
        this.showToast('Erro ao atualizar categoria.', 'error');
      }
    });
  }

  deleteCategory(cat: FinanceCategory): void {
    this.openConfirmDialog({
      title: 'Excluir Categoria',
      message: `Deseja excluir a categoria "${cat.name}"? As despesas associadas passarão para "Outros".`,
      confirmButtonText: 'Sim, Excluir',
      isDanger: true,
      onConfirm: () => {
        this.financeApi.deleteCategory(cat.id).subscribe({
          next: () => {
            this.showToast(`Categoria "${cat.name}" excluída com sucesso!`, 'success');
            this.loadCategoriesAndCards();
            this.loadDashboard();
          },
          error: err => {
            console.error('Erro ao deletar categoria:', err);
            this.showToast('Erro ao excluir categoria.', 'error');
          }
        });
      }
    });
  }

  addCard(): void {
    if (!this.newCardName.trim()) return;
    const cardName = this.newCardName.trim();
    this.financeApi.createCard({
      name: cardName,
      type: this.newCardType
    }).subscribe({
      next: () => {
        this.newCardName = '';
        this.showToast(`Cartão "${cardName}" cadastrado com sucesso!`, 'success');
        this.loadCategoriesAndCards();
      },
      error: err => {
        console.error('Erro ao cadastrar cartão:', err);
        this.showToast('Erro ao cadastrar cartão.', 'error');
      }
    });
  }

  startEditCard(card: FinanceCard): void {
    this.editingCard = { ...card };
  }

  saveEditCard(): void {
    if (!this.editingCard || !this.editingCard.name.trim()) return;
    const name = this.editingCard.name.trim();
    this.financeApi.updateCard(this.editingCard.id, {
      name,
      type: this.editingCard.type
    }).subscribe({
      next: () => {
        this.editingCard = null;
        this.showToast(`Cartão "${name}" atualizado!`, 'success');
        this.loadCategoriesAndCards();
      },
      error: err => {
        console.error('Erro ao atualizar cartão:', err);
        this.showToast('Erro ao atualizar cartão.', 'error');
      }
    });
  }

  deleteCard(card: FinanceCard): void {
    this.openConfirmDialog({
      title: 'Remover Cartão',
      message: `Deseja realmente remover o cartão "${card.name}"?`,
      confirmButtonText: 'Sim, Remover',
      isDanger: true,
      onConfirm: () => {
        this.financeApi.deleteCard(card.id).subscribe({
          next: () => {
            this.showToast(`Cartão "${card.name}" removido!`, 'success');
            this.loadCategoriesAndCards();
          },
          error: err => {
            console.error('Erro ao deletar cartão:', err);
            this.showToast('Erro ao remover cartão.', 'error');
          }
        });
      }
    });
  }

  // --- Ações de Limpeza e Importação ---

  clearPeriodTransactions(): void {
    this.openConfirmDialog({
      title: 'Limpar Lançamentos',
      message: `Atenção: Deseja realmente limpar os lançamentos de ${this.tabTitle} para ${this.currentMonthLabel}? Para sua segurança, esta ação requer confirmação.`,
      confirmButtonText: 'Entendi',
      isDanger: false,
      onConfirm: () => {
        this.showToast('Operação de limpeza em lote protegida pelo sistema.', 'info');
      }
    });
  }

  openImportModal(): void {
    this.showImportModal = true;
  }

  closeImportModal(): void {
    this.showImportModal = false;
  }
}
