import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { forkJoin } from 'rxjs';
import { ApiService, Pais, IndicadorEconomico, TipoCambio } from '../../services/api.service';

@Component({
  selector: 'app-pais-detail',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './pais-detail.html',
  styleUrl: './pais-detail.css',
})
export class PaisDetailComponent implements OnInit {
  codigoISO = '';

  loading = true;
  error = '';

  pais: Pais | null = null;
  indicadores: IndicadorEconomico[] = [];
  tipoCambio: TipoCambio | null = null;

  constructor(private route: ActivatedRoute, private api: ApiService) {}

  ngOnInit(): void {
    this.codigoISO = (this.route.snapshot.paramMap.get('codigo') || '').toUpperCase();
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = '';

    forkJoin({
      pais: this.api.getPais(this.codigoISO),
      indicadores: this.api.getPaisIndicadores(this.codigoISO),
      tipoCambio: this.api.getPaisTipoCambio(this.codigoISO),
    }).subscribe({
      next: ({ pais, indicadores, tipoCambio }) => {
        this.pais = pais;

        // ordenar indicadores (más nuevo arriba)
        this.indicadores = [...(indicadores || [])].sort((a, b) => b.anio - a.anio);

        this.tipoCambio = tipoCambio;
        this.loading = false;
      },
      error: (e) => {
        console.error('Pais detail error', e);
        this.error =
          e?.error?.detail ||
          'No se pudo cargar el detalle del país. Revisa el backend o permisos.';
        this.loading = false;
      },
    });
  }

  formatNumber(n: number): string {
    try {
      return new Intl.NumberFormat('es-CO').format(n);
    } catch {
      return String(n);
    }
  }
}