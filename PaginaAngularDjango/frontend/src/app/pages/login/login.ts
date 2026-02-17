import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { finalize, switchMap } from 'rxjs';

import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrls: ['./login.css'],
})
export class LoginComponent {
  username = '';
  password = '';

  loading = false;
  error = '';

  constructor(private auth: AuthService, private router: Router) {
    if (this.auth.hasAccessToken()) {
      this.router.navigateByUrl('/paises');
    }
  }

  submit(): void {
    this.error = '';

    const username = this.username.trim();
    const password = this.password.trim();

    if (!username || !password) {
      this.error = 'Completa usuario y contrasena.';
      return;
    }

    this.loading = true;

    this.auth
      .login(username, password)
      .pipe(
        switchMap(() => this.auth.me()),
        finalize(() => (this.loading = false))
      )
      .subscribe({
        next: () => this.router.navigateByUrl('/paises'),
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
