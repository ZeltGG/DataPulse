import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { ApiService, Pais, IndicadorEconomico, TipoCambio } from '../../services/api.service';

@Component({
  selector: 'app-pais-detail',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './pais-detail.html',
  styleUrl: './pais-detail.css',
})
export class PaisDetailComponent implements OnInit {
  codigo = '';
  loading = true;
  error = '';

  pais: Pais | null = null;
  indicadores: IndicadorEconomico[] = [];
  tipoCambio: TipoCambio | null = null;

  constructor(private route: ActivatedRoute, private api: ApiService) {}

  ngOnInit(): void {
    this.codigo = (this.route.snapshot.paramMap.get('codigo') || '').toUpperCase();
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = '';

    this.api.getPais(this.codigo).subscribe({
      next: (pais) => {
        this.pais = pais;

        // cargar extras en paralelo simple
        this.api.getPaisIndicadores(this.codigo).subscribe({
          next: (data) => (this.indicadores = data),
          error: () => (this.indicadores = []),
        });

        this.api.getPaisTipoCambio(this.codigo).subscribe({
          next: (fx) => (this.tipoCambio = fx),
          error: () => (this.tipoCambio = null),
        });

        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudo cargar el país.';
        this.loading = false;
      },
    });
  }
}