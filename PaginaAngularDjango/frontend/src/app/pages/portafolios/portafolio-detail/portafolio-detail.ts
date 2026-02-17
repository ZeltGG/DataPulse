import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ApiService, Portafolio } from '../../../services/api.service';

@Component({
  selector: 'app-portafolio-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './portafolio-detail.html',
  styleUrl: './portafolio-detail.css',
})
export class PortafolioDetailComponent implements OnInit {
  item: Portafolio | null = null;
  loading = true;
  error = '';

  constructor(private api: ApiService, private route: ActivatedRoute) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) {
      this.error = 'ID inválido.';
      this.loading = false;
      return;
    }

    this.api.getPortafolio(id).subscribe({
      next: (res) => {
        this.item = res;
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudo cargar el portafolio.';
        this.loading = false;
      },
    });
  }
}