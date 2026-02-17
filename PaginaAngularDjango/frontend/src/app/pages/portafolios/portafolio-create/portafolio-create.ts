import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';

import { ApiService } from '../../../services/api.service';

@Component({
  selector: 'app-portafolio-create',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './portafolio-create.html',
  styleUrl: './portafolio-create.css',
})
export class PortafolioCreateComponent {
  nombre = '';
  descripcion = '';

  loading = false;
  error = '';

  constructor(private api: ApiService, private router: Router) {}

  submit(): void {
    this.error = '';
    this.loading = true;

    this.api
      .createPortafolio({
        nombre: this.nombre.trim(),
        descripcion: this.descripcion.trim(),
      })
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (created) => this.router.navigateByUrl(`/portafolios/${created.id}`),
        error: () => (this.error = 'No se pudo crear el portafolio (¿permisos?).'),
      });
  }
}