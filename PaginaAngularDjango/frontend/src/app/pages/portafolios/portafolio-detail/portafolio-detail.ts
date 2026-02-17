import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { ApiService, Portafolio } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-portafolio-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './portafolio-detail.html',
  styleUrl: './portafolio-detail.css',
})
export class PortafolioDetailComponent implements OnInit {
  item: Portafolio | null = null;
  loading = true;
  error = '';
  deletingPosicionId: number | null = null;

  canWrite = false;

  constructor(
    private api: ApiService,
    private auth: AuthService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.canWrite = this.auth.hasRole('ANALISTA', 'ADMIN');

    if (!this.auth.getMeSnapshot()) {
      this.auth.initSession().subscribe(() => {
        this.canWrite = this.auth.hasRole('ANALISTA', 'ADMIN');
      });
    }

    this.load();
  }

  load(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) {
      this.error = 'ID invalido.';
      this.loading = false;
      return;
    }

    this.loading = true;
    this.error = '';

    this.api
      .getPortafolio(id)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (res) => {
          this.item = res;
        },
        error: () => {
          this.error = 'No se pudo cargar el portafolio.';
        },
      });
  }

  deletePosicion(posicionId: number): void {
    if (!this.item || !this.canWrite || this.deletingPosicionId) {
      return;
    }

    this.deletingPosicionId = posicionId;
    this.api
      .deletePosicion(this.item.id, posicionId)
      .pipe(finalize(() => (this.deletingPosicionId = null)))
      .subscribe({
        next: () => {
          if (!this.item?.posiciones) {
            return;
          }
          this.item.posiciones = this.item.posiciones.filter((p) => p.id !== posicionId);
        },
        error: () => {
          this.error = 'No se pudo eliminar la posicion.';
        },
      });
  }
}
