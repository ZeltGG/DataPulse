import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, Project } from '../../services/api.service';

@Component({
  selector: 'app-projects',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './projects.html',
  styleUrl: './projects.css',
})
export class ProjectsComponent implements OnInit {
  projects: Project[] = [];
  loading = true;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getProjects().subscribe({
      next: (res) => {
        this.projects = res.results;
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar los proyectos.';
        this.loading = false;
      },
    });
  }
}