import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './register.html',
  styleUrl: './register.css',
})
export class RegisterComponent {
  username = '';
  email = '';
  password = '';
  rol: 'VIEWER' | 'ANALISTA' | 'ADMIN' = 'VIEWER';
  loading = false;
  error = '';

  constructor(private api: ApiService, private router: Router) {}

  submit(): void {
    this.error = '';
    if (!this.username.trim() || !this.email.trim() || !this.password.trim()) {
      this.error = 'Completa todos los campos.';
      return;
    }

    this.loading = true;
    this.api
      .register({ username: this.username.trim(), email: this.email.trim(), password: this.password.trim(), rol: this.rol })
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: () => this.router.navigateByUrl('/login'),
        error: (e) => {
          this.error = e?.error?.detail || 'No se pudo registrar el usuario.';
        },
      });
  }
}
