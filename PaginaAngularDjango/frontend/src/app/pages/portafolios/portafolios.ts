import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { ApiService, Portafolio } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-portafolios',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './portafolios.html',
  styleUrl: './portafolios.css',
})
export class PortafoliosComponent implements OnInit {
  items: Portafolio[] = [];
  loading = true;
  error = '';

  canCreate = false;

  constructor(private api: ApiService, private auth: AuthService) {}

  ngOnInit(): void {
    // si no has cargado /me aún, lo pedimos (para roles)
    if (!this.auth.getMeSnapshot()) {
      this.auth.initSession().subscribe(() => {
        this.canCreate = this.auth.hasAnyRole(['ADMIN', 'ANALISTA']);
      });
    } else {
      this.canCreate = this.auth.hasAnyRole(['ADMIN', 'ANALISTA']);
    }

    this.api.getPortafolios().subscribe({
      next: (res) => {
        this.items = res.results ?? [];
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar los portafolios.';
        this.loading = false;
      },
    });
  }
}