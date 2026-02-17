import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService, Pais, Region } from '../../services/api.service';
import { CountryFlagComponent } from '../../shared/country-flag/country-flag';

@Component({
  selector: 'app-paises',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, CountryFlagComponent],
  templateUrl: './paises.html',
  styleUrl: './paises.css',
})
export class PaisesComponent implements OnInit {
  paises: Pais[] = [];
  filtered: Pais[] = [];

  loading = true;
  error = '';

  region: Region | '' = '';
  search = '';

  page = 1;
  count = 0;
  next: string | null = null;
  previous: string | null = null;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.load(1);
  }

  load(page = 1): void {
    this.loading = true;
    this.error = '';

    this.api
      .getPaises({
        region: this.region === '' ? undefined : (this.region as Region),
        page,
      })
      .subscribe({
        next: (res) => {
          this.paises = res.results;
          this.count = res.count;
          this.next = res.next;
          this.previous = res.previous;
          this.page = page;
          this.applyFilters();
          this.loading = false;
        },
        error: () => {
          this.error = 'No se pudieron cargar los paises.';
          this.loading = false;
        },
      });
  }

  applyFilters(): void {
    const q = this.search.trim().toLowerCase();

    if (!q) {
      this.filtered = [...this.paises];
      return;
    }

    this.filtered = this.paises.filter((p) => {
      return (
        p.nombre.toLowerCase().includes(q) ||
        p.codigo_iso.toLowerCase().includes(q) ||
        p.moneda_codigo.toLowerCase().includes(q)
      );
    });
  }

  onRegionChange(value: Region | ''): void {
    this.region = value;
    this.load(1);
  }

  goPrev(): void {
    if (!this.previous) return;
    this.load(this.page - 1);
  }

  goNext(): void {
    if (!this.next) return;
    this.load(this.page + 1);
  }
}