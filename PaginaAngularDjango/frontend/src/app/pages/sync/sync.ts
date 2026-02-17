import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize } from 'rxjs';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-sync',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sync.html',
  styleUrl: './sync.css',
})
export class SyncComponent {
  loading = false;
  error = '';
  result: any = null;

  constructor(private api: ApiService) {}

  runSyncPaises(): void {
    this.run(this.api.syncPaises());
  }

  runSyncIndicadores(): void {
    this.run(this.api.syncIndicadores());
  }

  runRecalcularRiesgo(): void {
    this.run(this.api.recalcularRiesgo());
  }

  private run(obs: any): void {
    this.loading = true;
    this.error = '';
    this.result = null;

    obs.pipe(finalize(() => (this.loading = false))).subscribe({
      next: (res: any) => (this.result = res),
      error: (err: any) => {
        if (err?.status === 403) this.error = 'No tienes permisos (solo ADMIN).';
        else this.error = 'No se pudo ejecutar la operacion.';
      },
    });
  }
}
