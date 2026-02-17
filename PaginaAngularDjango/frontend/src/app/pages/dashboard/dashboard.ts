import { AfterViewInit, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { Chart } from 'chart.js/auto';
import * as L from 'leaflet';
import { ApiService, DashboardResumen, Pais, Riesgo } from '../../services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, MatCardModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class DashboardComponent implements OnInit, AfterViewInit {
  loading = true;
  error = '';
  resumen: DashboardResumen | null = null;
  riesgos: Riesgo[] = [];
  paises: Pais[] = [];

  private map?: L.Map;
  private chart?: Chart;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getDashboardResumen().subscribe({
      next: (res) => {
        this.resumen = res;
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudo cargar el dashboard.';
        this.loading = false;
      },
    });

    this.api.getRiesgoRanking().subscribe({
      next: (res) => {
        this.riesgos = res.slice(0, 10);
        this.renderChart();
        this.renderMap();
      },
      error: () => {},
    });

    this.api.getPaises({ page: 1, pageSize: 200 }).subscribe({
      next: (res) => {
        this.paises = res.results;
        this.renderMap();
      },
      error: () => {},
    });
  }

  ngAfterViewInit(): void {
    this.renderMap();
    this.renderChart();
  }

  private riskColor(level: string): string {
    switch (level) {
      case 'CRITICO':
        return '#c62828';
      case 'ALTO':
        return '#ef6c00';
      case 'MODERADO':
        return '#f9a825';
      default:
        return '#2e7d32';
    }
  }

  private renderMap(): void {
    const container = document.getElementById('latam-map');
    if (!container || !this.paises.length || !this.riesgos.length) {
      return;
    }

    if (!this.map) {
      this.map = L.map(container).setView([-15, -65], 3);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(this.map);
    }

    this.map.eachLayer((layer) => {
      if (layer instanceof L.CircleMarker) {
        this.map?.removeLayer(layer);
      }
    });

    const riesgoPorCodigo = new Map(this.riesgos.map((r) => [r.pais_codigo, r]));

    for (const pais of this.paises) {
      const riesgo = riesgoPorCodigo.get(pais.codigo_iso);
      if (!riesgo) {
        continue;
      }
      L.circleMarker([pais.latitud, pais.longitud], {
        radius: 8,
        color: this.riskColor(riesgo.nivel_riesgo),
        fillOpacity: 0.8,
      })
        .bindPopup(`<b>${pais.nombre}</b><br/>IRPC: ${riesgo.indice_compuesto}<br/>Nivel: ${riesgo.nivel_riesgo}`)
        .addTo(this.map);
    }
  }

  private renderChart(): void {
    const canvas = document.getElementById('riesgo-chart') as HTMLCanvasElement | null;
    if (!canvas || !this.riesgos.length) {
      return;
    }

    this.chart?.destroy();

    this.chart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: this.riesgos.map((r) => r.pais_codigo),
        datasets: [
          {
            label: 'IRPC',
            data: this.riesgos.map((r) => r.indice_compuesto),
            backgroundColor: this.riesgos.map((r) => this.riskColor(r.nivel_riesgo)),
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
        },
      },
    });
  }
}
