import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Subject, interval, startWith, takeUntil } from 'rxjs';
import { AuthService } from '../../services/auth.service';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './navbar.html',
  styleUrl: './navbar.css',
})
export class NavbarComponent implements OnInit, OnDestroy {
  unreadAlerts = 0;
  theme: 'light' | 'dark' = 'light';
  private readonly destroy$ = new Subject<void>();

  constructor(public auth: AuthService, private api: ApiService) {}

  ngOnInit(): void {
    this.theme = (localStorage.getItem('theme') as 'light' | 'dark') || 'light';
    document.documentElement.setAttribute('data-theme', this.theme);

    if (this.auth.hasAccessToken() && !this.auth.getMeSnapshot()) {
      this.auth.initSession().subscribe();
    }

    interval(30000)
      .pipe(startWith(0), takeUntil(this.destroy$))
      .subscribe(() => {
        if (!this.auth.hasAccessToken()) {
          this.unreadAlerts = 0;
          return;
        }
        this.api.getAlertasResumen().subscribe({
          next: (res: any) => (this.unreadAlerts = res?.no_leidas || 0),
          error: () => {
            this.unreadAlerts = 0;
          },
        });
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  logout(): void {
    this.auth.logout();
    this.unreadAlerts = 0;
  }

  toggleTheme(): void {
    this.theme = this.theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', this.theme);
    localStorage.setItem('theme', this.theme);
    window.dispatchEvent(new Event('themechange'));
  }
}
