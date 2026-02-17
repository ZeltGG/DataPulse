import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';
import { roleGuard } from './guards/role.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login').then((m) => m.LoginComponent),
  },
  {
    path: 'register',
    loadComponent: () => import('./pages/register/register').then((m) => m.RegisterComponent),
  },
  {
    path: 'dashboard',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['VIEWER', 'ANALISTA', 'ADMIN'] },
    loadComponent: () => import('./pages/dashboard/dashboard').then((m) => m.DashboardComponent),
  },
  {
    path: 'alertas',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['VIEWER', 'ANALISTA', 'ADMIN'] },
    loadComponent: () => import('./pages/alertas/alertas').then((m) => m.AlertasComponent),
  },
  {
    path: 'perfil',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['VIEWER', 'ANALISTA', 'ADMIN'] },
    loadComponent: () => import('./pages/profile/profile').then((m) => m.ProfileComponent),
  },
  {
    path: 'paises',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['VIEWER', 'ANALISTA', 'ADMIN'] },
    loadComponent: () => import('./pages/paises/paises').then((m) => m.PaisesComponent),
  },
  {
    path: 'paises/:codigo',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['VIEWER', 'ANALISTA', 'ADMIN'] },
    loadComponent: () => import('./pages/pais-detail/pais-detail').then((m) => m.PaisDetailComponent),
  },
  {
    path: 'sync',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ADMIN'] },
    loadComponent: () => import('./pages/sync/sync').then((m) => m.SyncComponent),
  },
  {
    path: 'portafolios',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['VIEWER', 'ANALISTA', 'ADMIN'] },
    loadComponent: () => import('./pages/portafolios/portafolios').then((m) => m.PortafoliosComponent),
  },
  {
    path: 'portafolios/new',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ANALISTA', 'ADMIN'] },
    loadComponent: () => import('./pages/portafolios/portafolio-create/portafolio-create').then((m) => m.PortafolioCreateComponent),
  },
  {
    path: 'portafolios/:id',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['VIEWER', 'ANALISTA', 'ADMIN'] },
    loadComponent: () => import('./pages/portafolios/portafolio-detail/portafolio-detail').then((m) => m.PortafolioDetailComponent),
  },
  {
    path: 'portafolios/:id/posiciones/new',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ANALISTA', 'ADMIN'] },
    loadComponent: () => import('./pages/portafolios/posicion-create/posicion-create').then((m) => m.PosicionCreateComponent),
  },
  {
    path: '404',
    loadComponent: () => import('./pages/not-found/not-found').then((m) => m.NotFoundComponent),
  },
  { path: '**', redirectTo: '404' },
];
