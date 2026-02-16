import { Routes } from '@angular/router';
import { ProjectsComponent } from './pages/projects/projects';
import { ContactComponent } from './pages/contact/contact';
import { LoginComponent } from './pages/login/login';
import { PaisesComponent } from './pages/paises/paises';
import { authGuard } from './guards/auth.guard';
import { PaisDetailComponent } from './pages/pais-detail/pais-detail';
import { SyncComponent } from './pages/sync/sync';
import { adminGuard } from './guards/admin.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'projects', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'projects', component: ProjectsComponent },
  { path: 'contact', component: ContactComponent },
  { path: 'paises', component: PaisesComponent, canActivate: [authGuard] },
  { path: 'sync', component: SyncComponent, canActivate: [authGuard, adminGuard] },
  { path: '**', redirectTo: 'projects' },
  { path: 'paises/:codigo', component: PaisDetailComponent, canActivate: [authGuard] },
  
];