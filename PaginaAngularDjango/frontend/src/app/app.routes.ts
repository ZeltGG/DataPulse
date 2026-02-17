import { Routes } from '@angular/router';
import { ProjectsComponent } from './pages/projects/projects';
import { ContactComponent } from './pages/contact/contact';
import { LoginComponent } from './pages/login/login';
import { PaisesComponent } from './pages/paises/paises';
import { authGuard } from './guards/auth.guard';
import { PaisDetailComponent } from './pages/pais-detail/pais-detail';
import { SyncComponent } from './pages/sync/sync';
import { PortafoliosComponent } from './pages/portafolios/portafolios';
import { PortafolioDetailComponent } from './pages/portafolios/portafolio-detail/portafolio-detail';
import { PortafolioCreateComponent } from './pages/portafolios/portafolio-create/portafolio-create';




export const routes: Routes = [
  { path: '', redirectTo: 'projects', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'projects', component: ProjectsComponent },
  { path: 'contact', component: ContactComponent },
  { path: 'paises', component: PaisesComponent, canActivate: [authGuard] },
  { path: 'sync', component: SyncComponent, canActivate: [authGuard] },
  { path: 'paises/:codigo', component: PaisDetailComponent, canActivate: [authGuard], data: { roles: ['VIEWER', 'ANALISTA', 'ADMIN']} },
  { path: 'portafolios', component: PortafoliosComponent, canActivate: [authGuard], data: { roles: ['VIEWER', 'ANALISTA', 'ADMIN'] } },
  { path: 'portafolios/create', component: PortafolioCreateComponent, canActivate: [authGuard], data: { roles: ['ANALISTA', 'ADMIN'] } },
  { path: 'portafolios/:id', component: PortafolioDetailComponent, canActivate: [authGuard], data: { roles: ['VIEWER', 'ANALISTA', 'ADMIN'] } },
  { path: '**', redirectTo: 'projects' },
];