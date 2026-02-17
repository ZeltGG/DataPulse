import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs';
import { Alerta, ApiService } from '../../services/api.service';

@Component({
  selector: 'app-alertas',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './alertas.html',
  styleUrl: './alertas.css',
})
export class AlertasComponent implements OnInit {
  loading = true;
  error = '';
  items: Alerta[] = [];
  tipo = '';
  severidad = '';
  leida: '' | 'true' | 'false' = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = '';

    this.api
      .getAlertas({
        tipo: this.tipo || undefined,
        severidad: this.severidad || undefined,
        leida: this.leida || undefined,
      })
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (res) => (this.items = res.results || []),
        error: () => (this.error = 'No se pudieron cargar las alertas.'),
      });
  }

  clearFilters(): void {
    this.tipo = '';
    this.severidad = '';
    this.leida = '';
    this.load();
  }

  markRead(id: number): void {
    this.api.marcarAlertaLeida(id).subscribe({
      next: () => {
        this.items = this.items.map((a) => (a.id === id ? { ...a, leida: true } : a));
      },
    });
  }

  markAll(): void {
    this.api.marcarAlertasLeidas().subscribe({
      next: () => {
        this.items = this.items.map((a) => ({ ...a, leida: true }));
      },
    });
  }
}
