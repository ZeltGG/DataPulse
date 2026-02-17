import { AfterViewInit, Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { Chart } from 'chart.js/auto';
import * as L from 'leaflet';
import { ApiService, DashboardMapaItem, DashboardResumen, DashboardTendencias } from '../../services/api.service';
import { CountryFlagComponent } from '../../shared/country-flag/country-flag';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, MatCardModule, CountryFlagComponent],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class DashboardComponent implements OnInit, AfterViewInit, OnDestroy {
  loading = true;
  error = '';
  resumen: DashboardResumen | null = null;
  mapa: DashboardMapaItem[] = [];
  tendencias: DashboardTendencias | null = null;

  tiposIndicador = ['PIB', 'INFLACION', 'DESEMPLEO', 'BALANZA_COMERCIAL', 'DEUDA_PIB', 'PIB_PERCAPITA'];
  paisesDisponibles = ['CO', 'BR', 'MX', 'AR', 'CL', 'PE', 'EC', 'UY', 'PY', 'PA'];
  tipoSeleccionado = 'INFLACION';
  paisesSeleccionados = ['CO', 'BR', 'MX'];
  readonly countryColors: Record<string, string> = {
    CO: '#facc15',
    AR: '#7dd3fc',
    BR: '#facc15',
    MX: '#16a34a',
    CL: '#ef4444',
    PE: '#dc2626',
    EC: '#f59e0b',
    UY: '#60a5fa',
    PY: '#22c55e',
    PA: '#93c5fd',
  };

  private map?: L.Map;
  private chartRanking?: Chart;
  private chartTendencias?: Chart;
  private readonly onThemeChange = () => {
    this.renderRankingChart();
    this.renderTrendChart();
  };

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadAll();
  }

  ngAfterViewInit(): void {
    this.initMap();
    this.renderRankingChart();
    this.renderTrendChart();
    window.addEventListener('themechange', this.onThemeChange);
  }

  ngOnDestroy(): void {
    window.removeEventListener('themechange', this.onThemeChange);
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
      if (!this.paisesSeleccionados.includes(iso)) {
        if (this.paisesSeleccionados.length >= 3) {
          this.paisesSeleccionados = [...this.paisesSeleccionados.slice(1), iso];
        } else {
          this.paisesSeleccionados = [...this.paisesSeleccionados, iso];
        }
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

    const fg = this.cssVar('--fg', '#111111');
    const muted = this.cssVar('--muted-fg', '#4b5563');
    const border = this.cssVar('--border', '#e5e7eb');
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
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: {
            ticks: { color: muted },
            grid: { color: border },
          },
          y: {
            ticks: { color: muted },
            grid: { color: border },
          },
        },
        color: fg,
      },
    });
  }

  private renderTrendChart(): void {
    const canvas = document.getElementById('tendencias-chart') as HTMLCanvasElement | null;
    if (!canvas || !this.tendencias?.series?.length) {
      return;
    }

    const fg = this.cssVar('--fg', '#111111');
    const muted = this.cssVar('--muted-fg', '#4b5563');
    const border = this.cssVar('--border', '#e5e7eb');
    this.chartTendencias?.destroy();
    this.chartTendencias = new Chart(canvas, {
      type: 'line',
      data: {
        labels: this.tendencias.years.map((y) => String(y)),
        datasets: this.tendencias.series.map((s, i) => ({
          label: `${s.pais_nombre} (${s.pais_codigo})`,
          data: s.valores,
          borderColor: this.countryColor(s.pais_codigo),
          backgroundColor: this.countryColor(s.pais_codigo),
          pointBackgroundColor: this.countryColor(s.pais_codigo),
          pointBorderColor: fg,
          pointBorderWidth: 1,
          tension: 0.25,
          borderWidth: 2.5,
        })),
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            labels: {
              color: fg,
            },
          },
        },
        scales: {
          x: {
            ticks: { color: muted },
            grid: { color: border },
          },
          y: {
            ticks: { color: muted },
            grid: { color: border },
          },
        },
        color: fg,
      },
    });
  }

  countryColor(iso: string): string {
    return this.countryColors[iso] || '#64748b';
  }

  private cssVar(name: string, fallback: string): string {
    const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return value || fallback;
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
