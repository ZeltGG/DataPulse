import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { Chart } from 'chart.js/auto';

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
  resumen: any = null;
  loading = true;
  error = '';
  deletingPosicionId: number | null = null;
  editingPosicionId: number | null = null;

  canWrite = false;
  private chartPais?: Chart;
  private chartTipo?: Chart;

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
          this.loadResumen(id);
        },
        error: () => {
          this.error = 'No se pudo cargar el portafolio.';
        },
      });
  }

  loadResumen(id: number): void {
    this.api.getPortafolioResumen(id).subscribe({
      next: (res) => {
        this.resumen = res;
        this.renderCharts();
      },
      error: () => {
        this.resumen = null;
      },
    });
  }

  editPortafolio(): void {
    if (!this.item || !this.canWrite) return;
    const nombre = prompt('Nuevo nombre', this.item.nombre);
    if (!nombre) return;
    const descripcion = prompt('Descripcion', this.item.descripcion || '') || '';
    this.api.updatePortafolio(this.item.id, { nombre, descripcion }).subscribe({
      next: () => this.load(),
      error: () => (this.error = 'No se pudo actualizar el portafolio.'),
    });
  }

  exportPdf(): void {
    if (!this.item) return;
    this.api.exportPortafolioPdf(this.item.id).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `portafolio_${this.item?.id}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: () => (this.error = 'No se pudo exportar PDF.'),
    });
  }

  editPosicion(posicionId: number): void {
    if (!this.item || !this.canWrite || this.editingPosicionId) return;
    const pos = this.item.posiciones?.find((p) => p.id === posicionId);
    if (!pos) return;
    const cantidad = Number(prompt('Nueva cantidad', String(pos.cantidad)));
    const precio = Number(prompt('Nuevo precio unitario', String(pos.precio_unitario)));
    if (!cantidad || !precio) return;

    this.editingPosicionId = posicionId;
    this.api
      .updatePosicion(this.item.id, posicionId, { cantidad, precio_unitario: precio })
      .pipe(finalize(() => (this.editingPosicionId = null)))
      .subscribe({
        next: () => this.load(),
        error: () => (this.error = 'No se pudo actualizar la posicion.'),
      });
  }

  deletePosicion(posicionId: number): void {
    if (!this.item || !this.canWrite || this.deletingPosicionId) {
      return;
    }
    if (!confirm('Confirma cerrar esta posicion?')) return;

    this.deletingPosicionId = posicionId;
    this.api
      .deletePosicion(this.item.id, posicionId)
      .pipe(finalize(() => (this.deletingPosicionId = null)))
      .subscribe({
        next: () => this.load(),
        error: () => {
          this.error = 'No se pudo cerrar la posicion.';
        },
      });
  }

  private renderCharts(): void {
    if (!this.resumen) return;
    const paisCanvas = document.getElementById('dist-pais-chart') as HTMLCanvasElement | null;
    const tipoCanvas = document.getElementById('dist-tipo-chart') as HTMLCanvasElement | null;
    if (!paisCanvas || !tipoCanvas) return;

    this.chartPais?.destroy();
    this.chartTipo?.destroy();

    this.chartPais = new Chart(paisCanvas, {
      type: 'pie',
      data: {
        labels: (this.resumen.distribucion_pais || []).map((r: any) => r.pais__nombre),
        datasets: [{ data: (this.resumen.distribucion_pais || []).map((r: any) => r.total) }],
      },
    });

    this.chartTipo = new Chart(tipoCanvas, {
      type: 'doughnut',
      data: {
        labels: (this.resumen.distribucion_tipo_activo || []).map((r: any) => r.tipo_activo),
        datasets: [{ data: (this.resumen.distribucion_tipo_activo || []).map((r: any) => r.total) }],
      },
    });
  }
}
