import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { ApiService, Portafolio } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-portafolios',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './portafolios.html',
  styleUrl: './portafolios.css',
})
export class PortafoliosComponent implements OnInit {
  items: Portafolio[] = [];
  loading = true;
  error = '';
  deletingId: number | null = null;

  canWrite = false;

  constructor(private api: ApiService, private auth: AuthService) {}

  ngOnInit(): void {
    this.canWrite = this.auth.hasRole('ANALISTA', 'ADMIN');

    if (!this.auth.getMeSnapshot()) {
      this.auth.initSession().subscribe(() => {
        this.canWrite = this.auth.hasRole('ANALISTA', 'ADMIN');
      });
    }

    this.loadPortafolios();
  }

  loadPortafolios(): void {
    this.loading = true;
    this.error = '';

    this.api
      .getPortafolios()
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (res) => {
          this.items = res.results ?? [];
        },
        error: () => {
          this.error = 'No se pudieron cargar los portafolios.';
        },
      });
  }

  deletePortafolio(id: number): void {
    if (!this.canWrite || this.deletingId) {
      return;
    }

    this.deletingId = id;
    this.api
      .deletePortafolio(id)
      .pipe(finalize(() => (this.deletingId = null)))
      .subscribe({
        next: () => {
          this.items = this.items.filter((item) => item.id !== id);
        },
        error: () => {
          this.error = 'No se pudo eliminar el portafolio.';
        },
      });
  }
}
