import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

// ---- DRF pagination ----
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ---- Models ----
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

export type Region = 'ANDINA' | 'CONO_SUR' | 'CENTROAMERICA' | 'CARIBE';

export interface Pais {
  id: number;
  codigo_iso: string;
  nombre: string;
  moneda_codigo: string;
  moneda_nombre: string;
  region: Region;
  latitud: number;
  longitud: number;
  poblacion: number;
  activo: boolean;
}

export interface IndicadorEconomico {
  id: number;
  tipo: string;
  valor: number;
  unidad: string;
  anio: number;
  fuente: string;
  fecha_actualizacion: string;
  pais: number;
}

export interface TipoCambio {
  id: number;
  moneda_origen: string;
  moneda_destino: string;
  tasa: number;
  fecha: string;
  variacion_porcentual: number;
  fuente: string;
}

// ---- Portafolios ----
export interface Portafolio {
  id: number;
  nombre: string;
  descripcion: string;
  created_at?: string;
  updated_at?: string;
}

export interface PortafolioCreate {
  nombre: string;
  descripcion: string;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // ---- Projects ----
  getProjects(): Observable<PaginatedResponse<Project>> {
    return this.http.get<PaginatedResponse<Project>>(`${this.baseUrl}/projects/`);
  }

  // ---- Contact ----
  createContactMessage(payload: ContactMessageCreate): Observable<any> {
    return this.http.post(`${this.baseUrl}/contact-messages/`, payload);
  }

  // ---- Países ----
  getPaises(options?: { region?: Region; page?: number; pageSize?: number }): Observable<PaginatedResponse<Pais>> {
    let params = new HttpParams();

    if (options?.region) params = params.set('region', options.region);
    if (options?.page) params = params.set('page', String(options.page));
    if (options?.pageSize) params = params.set('page_size', String(options.pageSize));

    return this.http.get<PaginatedResponse<Pais>>(`${this.baseUrl}/paises/`, { params });
  }

  getPais(codigoISO: string): Observable<Pais> {
    return this.http.get<Pais>(`${this.baseUrl}/paises/${codigoISO}/`);
  }

  getPaisIndicadores(codigoISO: string): Observable<IndicadorEconomico[]> {
    return this.http.get<IndicadorEconomico[]>(`${this.baseUrl}/paises/${codigoISO}/indicadores/`);
  }

  getPaisTipoCambio(codigoISO: string): Observable<TipoCambio> {
    return this.http.get<TipoCambio>(`${this.baseUrl}/paises/${codigoISO}/tipo-cambio/`);
  }

  syncPaises(): Observable<any> {
    return this.http.post(`${this.baseUrl}/sync/paises/`, {});
  }

  // ---- Portafolios ----
  getPortafolios(): Observable<PaginatedResponse<Portafolio>> {
    return this.http.get<PaginatedResponse<Portafolio>>(`${this.baseUrl}/portafolios/`);
  }

  getPortafolio(id: number): Observable<Portafolio> {
    return this.http.get<Portafolio>(`${this.baseUrl}/portafolios/${id}/`);
  }

  createPortafolio(payload: PortafolioCreate): Observable<Portafolio> {
    return this.http.post<Portafolio>(`${this.baseUrl}/portafolios/`, payload);
  }

  deletePortafolio(id: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/portafolios/${id}/`);
  }
}