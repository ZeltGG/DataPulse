import { AfterViewInit, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { Chart } from 'chart.js/auto';
import * as L from 'leaflet';
import { ApiService, DashboardMapaItem, DashboardResumen, DashboardTendencias } from '../../services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, MatCardModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class DashboardComponent implements OnInit, AfterViewInit {
  loading = true;
  error = '';
  resumen: DashboardResumen | null = null;
  mapa: DashboardMapaItem[] = [];
  tendencias: DashboardTendencias | null = null;

  tiposIndicador = ['PIB', 'INFLACION', 'DESEMPLEO', 'BALANZA_COMERCIAL', 'DEUDA_PIB', 'PIB_PERCAPITA'];
  paisesDisponibles = ['CO', 'BR', 'MX', 'AR', 'CL', 'PE', 'EC', 'UY', 'PY', 'PA'];
  tipoSeleccionado = 'INFLACION';
  paisesSeleccionados = ['CO', 'BR', 'MX'];

  private map?: L.Map;
  private chartRanking?: Chart;
  private chartTendencias?: Chart;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadAll();
  }

  ngAfterViewInit(): void {
    this.initMap();
    this.renderRankingChart();
    this.renderTrendChart();
  }

  loadAll(): void {
    this.loading = true;
    this.error = '';

    this.api.getDashboardResumen().subscribe({
      next: (res) => {
        this.resumen = res;
        setTimeout(() => this.renderRankingChart(), 0);
      },
      error: () => {
        this.error = 'No se pudo cargar el resumen del dashboard.';
      },
    });

    this.api.getDashboardMapa().subscribe({
      next: (res) => {
        this.mapa = res;
        setTimeout(() => {
          this.initMap();
          this.renderMap();
        }, 0);
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudo cargar el mapa.';
        this.loading = false;
      },
    });

    this.loadTendencias();
  }

  loadTendencias(): void {
    this.api.getDashboardTendencias(this.tipoSeleccionado, this.paisesSeleccionados).subscribe({
      next: (res) => {
        this.tendencias = res;
        setTimeout(() => this.renderTrendChart(), 0);
      },
      error: () => {
        this.error = 'No se pudo cargar las tendencias.';
      },
    });
  }

  onPaisToggle(iso: string, checked: boolean): void {
    if (checked) {
      if (!this.paisesSeleccionados.includes(iso) && this.paisesSeleccionados.length < 3) {
        this.paisesSeleccionados = [...this.paisesSeleccionados, iso];
      }
    } else {
      this.paisesSeleccionados = this.paisesSeleccionados.filter((p) => p !== iso);
    }
    if (this.paisesSeleccionados.length === 0) {
      this.paisesSeleccionados = ['CO'];
    }
    this.loadTendencias();
  }

  private renderMap(): void {
    const container = document.getElementById('latam-map');
    if (!container || !this.map) {
      return;
    }

    this.map.eachLayer((layer) => {
      if (layer instanceof L.CircleMarker) {
        this.map?.removeLayer(layer);
      }
    });

    for (const item of this.mapa) {
      L.circleMarker([item.latitud, item.longitud], {
        radius: 8,
        color: item.color,
        fillOpacity: 0.8,
      })
        .bindPopup(`<b>${item.nombre}</b><br/>IRPC: ${item.indice_compuesto}<br/>Nivel: ${item.nivel_riesgo}`)
        .addTo(this.map);
    }
    setTimeout(() => this.map?.invalidateSize(), 0);
  }

  private initMap(): void {
    const container = document.getElementById('latam-map');
    if (!container || this.map) return;
    this.map = L.map(container).setView([-15, -65], 3);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(this.map);
    setTimeout(() => this.map?.invalidateSize(), 0);
    this.renderMap();
  }

  private renderRankingChart(): void {
    const canvas = document.getElementById('riesgo-chart') as HTMLCanvasElement | null;
    if (!canvas || !this.resumen?.ranking?.length) {
      return;
    }

    this.chartRanking?.destroy();
    this.chartRanking = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: this.resumen.ranking.map((r) => r.pais__codigo_iso),
        datasets: [
          {
            label: 'IRPC',
            data: this.resumen.ranking.map((r) => r.indice_compuesto),
            backgroundColor: this.resumen.ranking.map((r) => this.colorByLevel(r.nivel_riesgo)),
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
      },
    });
  }

  private renderTrendChart(): void {
    const canvas = document.getElementById('tendencias-chart') as HTMLCanvasElement | null;
    if (!canvas || !this.tendencias?.series?.length) {
      return;
    }

    const palette = ['#2563eb', '#16a34a', '#dc2626'];
    this.chartTendencias?.destroy();
    this.chartTendencias = new Chart(canvas, {
      type: 'line',
      data: {
        labels: this.tendencias.years.map((y) => String(y)),
        datasets: this.tendencias.series.map((s, i) => ({
          label: `${s.pais_nombre} (${s.pais_codigo})`,
          data: s.valores,
          borderColor: palette[i % palette.length],
          backgroundColor: palette[i % palette.length],
          tension: 0.25,
        })),
      },
      options: {
        responsive: true,
      },
    });
  }

  private colorByLevel(level: string): string {
    switch (level) {
      case 'CRITICO':
        return '#ef4444';
      case 'ALTO':
        return '#f97316';
      case 'MODERADO':
        return '#eab308';
      default:
        return '#22c55e';
    }
  }
}
