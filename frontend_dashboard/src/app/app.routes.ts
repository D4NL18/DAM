import { Routes } from '@angular/router';
import { LayoutComponent } from './layout/layout.component';
import { HealthDashboardComponent } from './health-dashboard/health-dashboard.component';
import { FinanceDashboardComponent } from './finance-dashboard/finance-dashboard.component';

export const routes: Routes = [
  {
    path: '',
    component: LayoutComponent,
    children: [
      { path: '', redirectTo: 'health', pathMatch: 'full' },
      { path: 'health', component: HealthDashboardComponent },
      { path: 'finance', component: FinanceDashboardComponent }
    ]
  },
  { path: '**', redirectTo: '' }
];
