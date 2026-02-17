import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, DashboardResumen, Riesgo } from '../../services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class DashboardComponent implements OnInit {
  loading = true;
  error = '';
  resumen: DashboardResumen | null = null;
  riesgos: Riesgo[] = [];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getDashboardResumen().subscribe({
      next: (res) => {
        this.resumen = res;
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudo cargar el dashboard.';
        this.loading = false;
      },
    });

    this.api.getRiesgoRanking().subscribe({
      next: (res) => (this.riesgos = res.slice(0, 10)),
      error: () => {},
    });
  }
}
