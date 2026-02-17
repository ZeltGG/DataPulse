import { Component } from '@angular/core';
import { RouterOutlet, RouterLink } from '@angular/router';
import { NavbarComponent } from './components/navbar/navbar';
import { LoadingSpinnerComponent } from './shared/loading-spinner/loading-spinner';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, NavbarComponent, LoadingSpinnerComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
  
})
export class AppComponent {}
