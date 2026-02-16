import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class LoginComponent {
  username = '';
  password = '';

  loading = false;
  error = '';

  constructor(private auth: AuthService, private router: Router) {
    // opcional: si ya hay sesión, saca de login
    if (this.auth.hasAccessToken()) {
      this.router.navigateByUrl('/paises');
    }
  }

  submit(): void {
    this.error = '';

    const username = this.username.trim();
    const password = this.password.trim();

    if (!username || !password) {
      this.error = 'Completa usuario y contraseña.';
      return;
    }

    this.loading = true;

    this.auth
      .login(username, password)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: () => this.router.navigateByUrl('/paises'),
        error: (err: unknown) => {
          if (err instanceof HttpErrorResponse) {
            if (err.status === 401) {
              this.error = 'Usuario o contraseña incorrectos.';
              return;
            }
            if (err.status === 0) {
              this.error = 'No hay conexión con el backend (¿runserver encendido?).';
              return;
            }
            this.error = `Error ${err.status}: no se pudo iniciar sesión.`;
            return;
          }
          this.error = 'No se pudo iniciar sesión.';
        },
      });
  }
}