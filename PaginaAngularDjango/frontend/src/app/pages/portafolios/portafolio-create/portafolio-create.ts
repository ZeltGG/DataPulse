import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatButtonModule } from '@angular/material/button';

import { ApiService } from '../../../services/api.service';

@Component({
  selector: 'app-portafolio-create',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatCheckboxModule,
    MatButtonModule,
  ],
  templateUrl: './portafolio-create.html',
  styleUrl: './portafolio-create.css',
})
export class PortafolioCreateComponent {
  private readonly fb = inject(FormBuilder);

  loading = false;
  checkingName = false;
  error = '';

  form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(100)]],
    descripcion: ['', [Validators.maxLength(500)]],
    es_publico: [false],
  });

  constructor(private api: ApiService, private router: Router) {}

  onNombreBlur(): void {
    const control = this.form.controls.nombre;
    const value = control.value?.trim();
    if (!value || control.invalid) return;
    this.checkingName = true;
    this.api
      .validatePortafolioNombre(value)
      .pipe(finalize(() => (this.checkingName = false)))
      .subscribe({
        next: (res) => {
          if (!res.unique) {
            control.setErrors({ ...(control.errors || {}), notUnique: true });
          } else if (control.errors?.['notUnique']) {
            const { notUnique, ...rest } = control.errors;
            control.setErrors(Object.keys(rest).length ? rest : null);
          }
        },
      });
  }

  submit(): void {
    this.error = '';

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading = true;

    this.api
      .createPortafolio(this.form.getRawValue())
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (created) => this.router.navigateByUrl(`/portafolios/${created.id}`),
        error: () => (this.error = 'No se pudo crear el portafolio.'),
      });
  }
}
