import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Project {
  id: number;
  title: string;
  description: string;
  tech_stack: string;
  repo_url: string;
  live_url: string;
  created_at: string;
}

export interface ContactMessageCreate {
  name: string;
  email: string;
  message: string;
}

export interface Pais {
  id: number;
  codigo_iso: string;
  nombre: string;
  moneda_codigo: string;
  moneda_nombre: string;
  region: string;
  latitud: number;
  longitud: number;
  poblacion: number;
  activo: boolean;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // OJO: Projects puede estar paginado (si DRF pagination está global)
  getProjects(): Observable<PaginatedResponse<Project>> {
    return this.http.get<PaginatedResponse<Project>>(`${this.baseUrl}/projects/`);
  }

  createContactMessage(payload: ContactMessageCreate): Observable<any> {
    return this.http.post(`${this.baseUrl}/contact-messages/`, payload);
  }

  getPaises(): Observable<PaginatedResponse<Pais>> {
    return this.http.get<PaginatedResponse<Pais>>(`${this.baseUrl}/paises/`);
  }

  getPaisDetalle(codigoIso: string): Observable<Pais> {
    return this.http.get<Pais>(`${this.baseUrl}/paises/${codigoIso}/`);
  }

  getIndicadores(codigoIso: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/paises/${codigoIso}/indicadores/`);
  }

  getTipoCambio(codigoIso: string): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/paises/${codigoIso}/tipo-cambio/`);
  }
}