import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { finalize } from 'rxjs';

import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './profile.html',
  styleUrl: './profile.css',
})
export class ProfileComponent implements OnInit {
  private readonly fb = new FormBuilder();

  loading = true;
  saving = false;
  error = '';
  success = '';

  form = this.fb.nonNullable.group({
    username: [{ value: '', disabled: true }],
    email: ['', [Validators.required, Validators.email]],
    first_name: [''],
    last_name: [''],
  });

  constructor(
    private api: ApiService,
    private auth: AuthService
  ) {}

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = '';
    this.success = '';
    this.api
      .getMe()
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (me) => {
          this.form.patchValue({
            username: me.username || '',
            email: me.email || '',
            first_name: me.first_name || '',
            last_name: me.last_name || '',
          });
        },
        error: () => {
          this.error = 'No se pudo cargar el perfil.';
        },
      });
  }

  submit(): void {
    this.error = '';
    this.success = '';
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const payload = {
      email: this.form.getRawValue().email.trim(),
      first_name: this.form.getRawValue().first_name.trim(),
      last_name: this.form.getRawValue().last_name.trim(),
    };

    this.saving = true;
    this.api
      .updateMe(payload)
      .pipe(finalize(() => (this.saving = false)))
      .subscribe({
        next: () => {
          this.success = 'Perfil actualizado.';
          this.auth.me().subscribe();
        },
        error: () => {
          this.error = 'No se pudo actualizar el perfil.';
        },
      });
  }
}
