import { Routes } from '@angular/router';
import { ProjectsComponent } from './pages/projects/projects';
import { ContactComponent } from './pages/contact/contact';
import { LoginComponent } from './pages/login/login';
import { PaisesComponent } from './pages/paises/paises';

export const routes: Routes = [
  { path: '', redirectTo: 'projects', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'projects', component: ProjectsComponent },
  { path: 'contact', component: ContactComponent },
  { path: 'paises', component: PaisesComponent },
  { path: '**', redirectTo: 'projects' },
];