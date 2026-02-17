import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { ApiService, Pais, PosicionCreate } from '../../../services/api.service';

@Component({
  selector: 'app-posicion-create',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './posicion-create.html',
  styleUrl: './posicion-create.css',
})
export class PosicionCreateComponent implements OnInit {
  portafolioId = 0;
  paises: Pais[] = [];

  form: PosicionCreate = {
    pais: 0,
    activo: '',
    ticker: '',
    tipo_activo: 'ACCION',
    moneda: 'USD',
    cantidad: 0,
    precio_unitario: 0,
    peso_porcentual: null,
  };

  loading = false;
  loadingPaises = true;
  error = '';

  constructor(
    private api: ApiService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.portafolioId = Number(this.route.snapshot.paramMap.get('id'));
    this.api.getPaises({ page: 1, pageSize: 200 }).subscribe({
      next: (res) => {
        this.paises = res.results;
        if (this.paises.length) {
          this.form.pais = this.paises[0].id;
        }
        this.loadingPaises = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar los paises.';
        this.loadingPaises = false;
      },
    });
  }

  submit(): void {
    this.error = '';

    if (!this.portafolioId) {
      this.error = 'Portafolio invalido.';
      return;
    }
    if (!this.form.pais || !this.form.activo.trim()) {
      this.error = 'Completa los campos obligatorios.';
      return;
    }

    this.loading = true;

    this.api
      .createPosicion(this.portafolioId, {
        ...this.form,
        activo: this.form.activo.trim(),
        ticker: this.form.ticker.trim(),
      })
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: () => this.router.navigateByUrl(`/portafolios/${this.portafolioId}`),
        error: () => {
          this.error = 'No se pudo crear la posicion.';
        },
      });
  }
}
