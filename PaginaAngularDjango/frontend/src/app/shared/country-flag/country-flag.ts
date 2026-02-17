import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-country-flag',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './country-flag.html',
  styleUrl: './country-flag.css',
})
export class CountryFlagComponent {
  @Input({ required: true }) iso = '';
  @Input() size = 18;
  @Input() context: 'inline' | 'chip' | 'title' = 'inline';
  @Input() showCode = false;

  private readonly svgByIso: Record<string, string> = {
    AR: `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 16'><rect width='24' height='16' fill='#74acdf'/><rect y='5.33' width='24' height='5.34' fill='#fff'/><circle cx='12' cy='8' r='1.6' fill='#f6b40e'/></svg>`,
    BO: `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 16'><rect width='24' height='5.33' fill='#d52b1e'/><rect y='5.33' width='24' height='5.34' fill='#fcd116'/><rect y='10.67' width='24' height='5.33' fill='#007934'/><circle cx='12' cy='8' r='1.1' fill='#1f2937'/></svg>`,
    BR: `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 16'><rect width='24' height='16' fill='#229e45'/><polygon points='12,2.1 20.5,8 12,13.9 3.5,8' fill='#f8d447'/><circle cx='12' cy='8' r='3.2' fill='#1c3f94'/></svg>`,
    CL: `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 16'><rect width='24' height='8' fill='#fff'/><rect y='8' width='24' height='8' fill='#d52b1e'/><rect width='8' height='8' fill='#0039a6'/><circle cx='4' cy='4' r='1.2' fill='#fff'/></svg>`,
    CO: `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 16'><rect width='24' height='8' fill='#fcd116'/><rect y='8' width='24' height='4' fill='#003893'/><rect y='12' width='24' height='4' fill='#ce1126'/></svg>`,
    EC: `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 16'><rect width='24' height='8' fill='#fcd116'/><rect y='8' width='24' height='4' fill='#003893'/><rect y='12' width='24' height='4' fill='#ce1126'/><circle cx='12' cy='8.4' r='1.2' fill='#1f2937'/></svg>`,
    MX: `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 16'><rect width='8' height='16' fill='#006847'/><rect x='8' width='8' height='16' fill='#fff'/><rect x='16' width='8' height='16' fill='#ce1126'/><circle cx='12' cy='8' r='1.1' fill='#8b5a2b'/></svg>`,
    PA: `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 16'><rect width='12' height='8' fill='#fff'/><rect x='12' width='12' height='8' fill='#d21034'/><rect y='8' width='12' height='8' fill='#0052b4'/><rect x='12' y='8' width='12' height='8' fill='#fff'/><circle cx='6' cy='4' r='1' fill='#0052b4'/><circle cx='18' cy='12' r='1' fill='#d21034'/></svg>`,
    PE: `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 16'><rect width='8' height='16' fill='#d91023'/><rect x='8' width='8' height='16' fill='#fff'/><rect x='16' width='8' height='16' fill='#d91023'/></svg>`,
    PY: `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 16'><rect width='24' height='5.33' fill='#d52b1e'/><rect y='5.33' width='24' height='5.34' fill='#fff'/><rect y='10.67' width='24' height='5.33' fill='#0038a8'/><circle cx='12' cy='8' r='1.1' fill='#1f2937'/></svg>`,
    UY: `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 16'><rect width='24' height='16' fill='#fff'/><rect y='1.8' width='24' height='1.2' fill='#2a5fbd'/><rect y='4.3' width='24' height='1.2' fill='#2a5fbd'/><rect y='6.8' width='24' height='1.2' fill='#2a5fbd'/><rect y='9.3' width='24' height='1.2' fill='#2a5fbd'/><rect y='11.8' width='24' height='1.2' fill='#2a5fbd'/><rect y='14.3' width='24' height='1.2' fill='#2a5fbd'/><circle cx='4' cy='4' r='1.7' fill='#f6b40e'/></svg>`,
  };

  get code(): string {
    return (this.iso || '').toUpperCase();
  }

  get src(): string {
    const svg = this.svgByIso[this.code];
    return svg ? `data:image/svg+xml;utf8,${encodeURIComponent(svg)}` : '';
  }

  get fallbackLabel(): string {
    return this.code || '--';
  }
}
