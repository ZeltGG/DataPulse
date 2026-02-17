import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { finalize, switchMap } from 'rxjs';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';

import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
  ],
  templateUrl: './login.html',
  styleUrls: ['./login.css'],
})
export class LoginComponent {
  loading = false;
  error = '';

  form = this.fb.nonNullable.group({
    username: ['', [Validators.required]],
    password: ['', [Validators.required]],
  });

  constructor(private fb: FormBuilder, private auth: AuthService, private router: Router) {
    if (this.auth.hasAccessToken()) {
      this.router.navigateByUrl('/dashboard');
    }
  }

  submit(): void {
    this.error = '';

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const username = this.form.getRawValue().username.trim();
    const password = this.form.getRawValue().password.trim();

    this.loading = true;

    this.auth
      .login(username, password)
      .pipe(
        switchMap(() => this.auth.me()),
        finalize(() => (this.loading = false))
      )
      .subscribe({
        next: () => this.router.navigateByUrl('/dashboard'),
        error: (err: unknown) => {
          if (err instanceof HttpErrorResponse) {
            if (err.status === 401) {
              this.error = 'Usuario o contrasena incorrectos.';
              return;
            }
            if (err.status === 0) {
              this.error = 'No hay conexion con el backend.';
              return;
            }
            this.error = `Error ${err.status}: no se pudo iniciar sesion.`;
            return;
          }
          this.error = 'No se pudo iniciar sesion.';
        },
      });
  }
}
