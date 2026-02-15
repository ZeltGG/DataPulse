import { Routes } from '@angular/router';
import { ProjectsComponent } from './pages/projects/projects';

export const routes: Routes = [
  { path: 'projects', component: ProjectsComponent },
  { path: '', redirectTo: 'projects', pathMatch: 'full' },
];