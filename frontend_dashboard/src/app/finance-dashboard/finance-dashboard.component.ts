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
  CategoryBreakdown
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

  // Controles de data e visualização
  currentYear: number = new Date().getFullYear();
  currentMonth: number = new Date().getMonth() + 1; // 1-indexed
  currentTab: 'expense_variable' | 'expense_fixed' | 'income' = 'expense_variable';
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
    owner: 'Christian',
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
  }

  get userDisplayName(): string {
    const user = this.authService.getCurrentUser();
    return user?.name || 'Christian';
  }

  get currentMonthLabel(): string {
    return `${this.monthNames[this.currentMonth - 1]} de ${this.currentYear}`;
  }

  get tabTitle(): string {
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

  setTab(tab: 'expense_variable' | 'expense_fixed' | 'income'): void {
    this.currentTab = tab;
    this.selectedCategoryFilter = '';
    this.txForm.type = tab;
    this.loadDashboard();
  }

  toggleHideValues(): void {
    this.hideValues = !this.hideValues;
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
      type: this.currentTab,
      paymentMethod: this.cards.length > 0 ? this.cards[0].name : 'Cartão de Crédito Pessoal',
      installment: '',
      owner: this.userDisplayName,
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
      owner: tx.owner || this.userDisplayName,
      date: tx.date ? tx.date.substring(0, 10) : new Date().toISOString().substring(0, 10)
    };
    this.showTransactionModal = true;
  }

  saveTransaction(): void {
    if (!this.txForm.description.trim() || !this.txForm.amount || this.txForm.amount <= 0) {
      alert('Por favor, informe a descrição e um valor maior que zero.');
      return;
    }

    const payload: Partial<FinanceTransaction> = {
      description: this.txForm.description.trim(),
      amount: Number(this.txForm.amount),
      category: this.txForm.category,
      type: this.txForm.type,
      paymentMethod: this.txForm.paymentMethod,
      installment: this.txForm.installment ? this.txForm.installment.trim() : undefined,
      owner: this.txForm.owner ? this.txForm.owner.trim() : this.userDisplayName,
      date: this.txForm.date
    };

    if (this.editingTransaction) {
      this.financeApi.updateTransaction(this.editingTransaction.id, payload).subscribe({
        next: () => {
          this.showTransactionModal = false;
          this.loadDashboard();
        },
        error: err => console.error('Erro ao atualizar transação:', err)
      });
    } else {
      this.financeApi.createTransaction(payload).subscribe({
        next: () => {
          this.showTransactionModal = false;
          this.loadDashboard();
        },
        error: err => console.error('Erro ao salvar transação:', err)
      });
    }
  }

  deleteCurrentTransaction(): void {
    if (!this.editingTransaction) return;
    if (confirm(`Deseja realmente excluir a transação "${this.editingTransaction.description}"?`)) {
      this.financeApi.deleteTransaction(this.editingTransaction.id).subscribe({
        next: () => {
          this.showTransactionModal = false;
          this.loadDashboard();
        },
        error: err => console.error('Erro ao excluir transação:', err)
      });
    }
  }

  // --- Gerenciador de Categorias & Cartões ---

  openManageModal(): void {
    this.showManageModal = true;
  }

  addCategory(): void {
    if (!this.newCategoryName.trim()) return;
    this.financeApi.createCategory({
      name: this.newCategoryName.trim(),
      color: this.newCategoryColor
    }).subscribe({
      next: () => {
        this.newCategoryName = '';
        this.loadCategoriesAndCards();
        this.loadDashboard();
      },
      error: err => console.error('Erro ao criar categoria:', err)
    });
  }

  startEditCategory(cat: FinanceCategory): void {
    this.editingCategory = { ...cat };
  }

  saveEditCategory(): void {
    if (!this.editingCategory || !this.editingCategory.name.trim()) return;
    this.financeApi.updateCategory(this.editingCategory.id, {
      name: this.editingCategory.name.trim(),
      color: this.editingCategory.color
    }).subscribe({
      next: () => {
        this.editingCategory = null;
        this.loadCategoriesAndCards();
        this.loadDashboard();
      },
      error: err => console.error('Erro ao atualizar categoria:', err)
    });
  }

  deleteCategory(cat: FinanceCategory): void {
    if (confirm(`Deseja excluir a categoria "${cat.name}"? As despesas associadas passarão para "Outros".`)) {
      this.financeApi.deleteCategory(cat.id).subscribe({
        next: () => {
          this.loadCategoriesAndCards();
          this.loadDashboard();
        },
        error: err => console.error('Erro ao deletar categoria:', err)
      });
    }
  }

  addCard(): void {
    if (!this.newCardName.trim()) return;
    this.financeApi.createCard({
      name: this.newCardName.trim(),
      type: this.newCardType
    }).subscribe({
      next: () => {
        this.newCardName = '';
        this.loadCategoriesAndCards();
      },
      error: err => console.error('Erro ao cadastrar cartão:', err)
    });
  }

  startEditCard(card: FinanceCard): void {
    this.editingCard = { ...card };
  }

  saveEditCard(): void {
    if (!this.editingCard || !this.editingCard.name.trim()) return;
    this.financeApi.updateCard(this.editingCard.id, {
      name: this.editingCard.name.trim(),
      type: this.editingCard.type
    }).subscribe({
      next: () => {
        this.editingCard = null;
        this.loadCategoriesAndCards();
      },
      error: err => console.error('Erro ao atualizar cartão:', err)
    });
  }

  deleteCard(card: FinanceCard): void {
    if (confirm(`Deseja remover o cartão "${card.name}"?`)) {
      this.financeApi.deleteCard(card.id).subscribe({
        next: () => this.loadCategoriesAndCards(),
        error: err => console.error('Erro ao deletar cartão:', err)
      });
    }
  }

  // --- Ações de Limpeza e Importação ---

  clearPeriodTransactions(): void {
    if (confirm(`Atenção: Deseja realmente limpar os lançamentos de ${this.tabTitle} para ${this.currentMonthLabel}?`)) {
      alert('Para sua segurança, a exclusão em lote no Firestore requer confirmação individual ou script de migração seguro.');
    }
  }

  openImportModal(): void {
    this.showImportModal = true;
  }

  closeImportModal(): void {
    this.showImportModal = false;
  }
}
