import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, Pais } from '../../services/api.service';

@Component({
  selector: 'app-paises',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './paises.html',
  styleUrl: './paises.css',
})
export class PaisesComponent implements OnInit {
  paises: Pais[] = [];
  loading = true;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getPaises().subscribe({
      next: (res) => {
        this.paises = res.results;
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar los países.';
        this.loading = false;
      },
    });
  }
}