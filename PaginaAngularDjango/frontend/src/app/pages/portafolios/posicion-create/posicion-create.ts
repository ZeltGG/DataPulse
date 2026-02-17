import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSelectModule } from '@angular/material/select';

import { ApiService, Pais } from '../../../services/api.service';

@Component({
  selector: 'app-posicion-create',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatSelectModule,
  ],
  templateUrl: './posicion-create.html',
  styleUrl: './posicion-create.css',
})
export class PosicionCreateComponent implements OnInit {
  portafolioId = 0;
  paises: Pais[] = [];

  form = this.fb.nonNullable.group({
    pais: [0, [Validators.required]],
    activo: ['', [Validators.required]],
    ticker: [''],
    tipo_activo: ['ACCION', [Validators.required]],
    moneda: ['USD', [Validators.required]],
    cantidad: [0, [Validators.required, Validators.min(0.0001)]],
    precio_unitario: [0, [Validators.required, Validators.min(0.0001)]],
    peso_porcentual: [null as number | null],
    notas: ['', [Validators.maxLength(200)]],
  });

  loading = false;
  loadingPaises = true;
  error = '';

  constructor(
    private fb: FormBuilder,
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
          this.form.patchValue({ pais: this.paises[0].id });
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

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading = true;

    const payload = this.form.getRawValue();
    if (payload.tipo_activo === 'MONEDA') {
      const pais = this.paises.find((p) => p.id === payload.pais);
      if (pais?.moneda_codigo === 'USD') {
        this.error = 'No se permite posicion MONEDA para pais con moneda USD.';
        this.loading = false;
        return;
      }
    }

    this.api
      .createPosicion(this.portafolioId, {
        ...payload,
        activo: payload.activo.trim(),
        ticker: payload.ticker.trim(),
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
