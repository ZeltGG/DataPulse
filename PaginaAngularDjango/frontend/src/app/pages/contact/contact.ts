import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-contact',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './contact.html',
  styleUrl: './contact.css',
})
export class ContactComponent {
  name = '';
  email = '';
  message = '';

  sending = false;
  success = '';
  error = '';

  constructor(private api: ApiService) {}

  submit(): void {
    this.sending = true;
    this.success = '';
    this.error = '';

    const payload = {
      name: this.name.trim(),
      email: this.email.trim().toLowerCase(),
      message: this.message.trim(),
    };

    this.api
      .createContactMessage(payload)
      .pipe(finalize(() => (this.sending = false)))
      .subscribe({
        next: () => {
          this.success = 'Mensaje enviado ✅';
          this.name = '';
          this.email = '';
          this.message = '';
        },
        error: (err) => {
          console.error('ERROR STATUS:', err.status);
          console.error('ERROR BODY:', err.error);

          const msg =
            err?.error?.email?.[0] ??
            err?.error?.detail ??
            'No se pudo enviar el mensaje.';

          // si quieres ver también el detalle crudo:
          
        },
      });
  }
}