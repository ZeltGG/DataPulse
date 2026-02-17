import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NavbarComponent } from './components/navbar/navbar';
import { LoadingSpinnerComponent } from './shared/loading-spinner/loading-spinner';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, NavbarComponent, LoadingSpinnerComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
  
})
export class AppComponent {}
