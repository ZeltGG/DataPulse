import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService, Pais, Region } from '../../services/api.service';

@Component({
  selector: 'app-paises',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './paises.html',
  styleUrl: './paises.css',
})
export class PaisesComponent implements OnInit {
  paises: Pais[] = [];
  loading = true;
  error = '';

  // filtro/paginación
  regions: Region[] = ['ANDINA', 'CONO_SUR', 'CENTROAMERICA', 'CARIBE'];
  selectedRegion: Region | '' = '';
  page = 1;
  count = 0;
  next: string | null = null;
  prev: string | null = null;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = '';

    this.api.getPaises({
      region: this.selectedRegion || undefined,
      page: this.page,
    }).subscribe({
      next: (res) => {
        this.paises = res.results;
        this.count = res.count;
        this.next = res.next;
        this.prev = res.previous;
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar los países.';
        this.loading = false;
      },
    });
  }

  setRegion(region: Region | ''): void {
    this.selectedRegion = region;
    this.page = 1;
    this.load();
  }

  nextPage(): void {
    if (!this.next) return;
    this.page += 1;
    this.load();
  }

  prevPage(): void {
    if (!this.prev) return;
    this.page = Math.max(1, this.page - 1);
    this.load();
  }
}