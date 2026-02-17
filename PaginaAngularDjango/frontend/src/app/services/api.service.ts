import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
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

export interface Posicion {
  id: number;
  portafolio: number;
  pais: number;
  activo: string;
  ticker: string;
  tipo_activo: string;
  moneda: string;
  cantidad: number;
  precio_unitario: number;
  peso_porcentual: number | null;
  monto_inversion_usd: number;
  fecha_entrada: string;
  fecha_salida: string | null;
  notas: string;
  created_at: string;
}

export interface Portafolio {
  id: number;
  nombre: string;
  descripcion: string;
  owner: number | null;
  es_publico: boolean;
  activo: boolean;
  created_at: string;
  updated_at: string;
  posiciones?: Posicion[];
}

export interface PortafolioCreate {
  nombre: string;
  descripcion: string;
  es_publico?: boolean;
}

export interface PosicionCreate {
  pais: number;
  activo: string;
  ticker: string;
  tipo_activo: string;
  moneda: string;
  cantidad: number;
  precio_unitario: number;
  peso_porcentual?: number | null;
  monto_inversion_usd?: number;
  fecha_entrada?: string;
  notas?: string;
}

export interface Riesgo {
  id: number;
  pais: number;
  pais_codigo: string;
  pais_nombre: string;
  fecha_calculo: string;
  score_economico: number;
  score_cambiario: number;
  score_estabilidad: number;
  indice_compuesto: number;
  nivel_riesgo: 'BAJO' | 'MODERADO' | 'ALTO' | 'CRITICO';
  detalle_calculo: Record<string, unknown>;
}

export interface Alerta {
  id: number;
  usuario: number | null;
  pais: number | null;
  pais_codigo: string;
  tipo_alerta: 'RIESGO' | 'TIPO_CAMBIO' | 'INDICADOR';
  severidad: 'INFO' | 'WARNING' | 'CRITICAL';
  titulo: string;
  mensaje: string;
  leida: boolean;
  fecha_creacion: string;
}

export interface DashboardResumen {
  kpis: {
    total_paises: number;
    alertas_activas: number;
    portafolios_usuario: number;
    promedio_irpc: number;
  };
  ranking: Array<{
    pais__codigo_iso: string;
    pais__nombre: string;
    indice_compuesto: number;
    nivel_riesgo: string;
    variacion: number;
    tendencia: 'ALZA' | 'BAJA' | 'ESTABLE';
  }>;
}

export interface DashboardMapaItem {
  codigo_iso: string;
  nombre: string;
  latitud: number;
  longitud: number;
  indice_compuesto: number;
  nivel_riesgo: 'BAJO' | 'MODERADO' | 'ALTO' | 'CRITICO';
  color: string;
}

export interface DashboardTendencias {
  tipo: string;
  years: number[];
  series: Array<{
    pais_codigo: string;
    pais_nombre: string;
    valores: Array<number | null>;
  }>;
}

export interface MeProfile {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_superuser: boolean;
  groups: string[];
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  register(payload: { username: string; email: string; password: string; rol: 'ADMIN' | 'ANALISTA' | 'VIEWER' }): Observable<unknown> {
    return this.http.post(`${this.baseUrl}/auth/register/`, payload);
  }

  getMe(): Observable<MeProfile> {
    return this.http.get<MeProfile>(`${this.baseUrl}/auth/me/`);
  }

  updateMe(payload: { email?: string; first_name?: string; last_name?: string }): Observable<MeProfile> {
    return this.http.put<MeProfile>(`${this.baseUrl}/auth/me/`, payload);
  }

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

  getPaisIndicadores(codigoISO: string, params?: { tipo?: string; anio?: number; page?: number; pageSize?: number }): Observable<PaginatedResponse<IndicadorEconomico>> {
    let httpParams = new HttpParams();
    if (params?.tipo) httpParams = httpParams.set('tipo', params.tipo);
    if (params?.anio) httpParams = httpParams.set('anio', String(params.anio));
    if (params?.page) httpParams = httpParams.set('page', String(params.page));
    if (params?.pageSize) httpParams = httpParams.set('page_size', String(params.pageSize));
    return this.http.get<PaginatedResponse<IndicadorEconomico>>(`${this.baseUrl}/paises/${codigoISO}/indicadores/`, { params: httpParams });
  }

  getPaisTipoCambio(codigoISO: string, params?: { start?: string; end?: string; page?: number; pageSize?: number }): Observable<PaginatedResponse<TipoCambio>> {
    let httpParams = new HttpParams();
    if (params?.start) httpParams = httpParams.set('start', params.start);
    if (params?.end) httpParams = httpParams.set('end', params.end);
    if (params?.page) httpParams = httpParams.set('page', String(params.page));
    if (params?.pageSize) httpParams = httpParams.set('page_size', String(params.pageSize));
    return this.http.get<PaginatedResponse<TipoCambio>>(`${this.baseUrl}/paises/${codigoISO}/tipo-cambio/`, { params: httpParams });
  }

  syncPaises(): Observable<unknown> {
    return this.http.post(`${this.baseUrl}/sync/paises/`, {});
  }

  syncIndicadores(): Observable<unknown> {
    return this.http.post(`${this.baseUrl}/paises/sync-indicadores/`, {});
  }

  getPortafolios(): Observable<PaginatedResponse<Portafolio>> {
    return this.http.get<PaginatedResponse<Portafolio>>(`${this.baseUrl}/portafolios/`);
  }

  validatePortafolioNombre(nombre: string): Observable<{ unique: boolean; detail?: string }> {
    const params = new HttpParams().set('nombre', nombre);
    return this.http.get<{ unique: boolean; detail?: string }>(`${this.baseUrl}/portafolios/validate-nombre/`, { params });
  }

  getPortafolio(id: number): Observable<Portafolio> {
    return this.http.get<Portafolio>(`${this.baseUrl}/portafolios/${id}/`);
  }

  createPortafolio(payload: PortafolioCreate): Observable<Portafolio> {
    return this.http.post<Portafolio>(`${this.baseUrl}/portafolios/`, payload);
  }

  updatePortafolio(id: number, payload: Partial<PortafolioCreate>): Observable<Portafolio> {
    return this.http.put<Portafolio>(`${this.baseUrl}/portafolios/${id}/`, payload);
  }

  deletePortafolio(id: number): Observable<unknown> {
    return this.http.delete(`${this.baseUrl}/portafolios/${id}/`);
  }

  getPortafolioResumen(id: number): Observable<unknown> {
    return this.http.get(`${this.baseUrl}/portafolios/${id}/resumen/`);
  }

  exportPortafolioPdf(id: number): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/portafolios/${id}/export/pdf/`, { responseType: 'blob' });
  }

  createPosicion(portafolioId: number, payload: PosicionCreate): Observable<Posicion> {
    return this.http.post<Posicion>(`${this.baseUrl}/portafolios/${portafolioId}/posiciones/`, payload);
  }

  updatePosicion(portafolioId: number, posicionId: number, payload: Partial<PosicionCreate>): Observable<Posicion> {
    return this.http.put<Posicion>(`${this.baseUrl}/portafolios/${portafolioId}/posiciones/${posicionId}/`, payload);
  }

  deletePosicion(portafolioId: number, posicionId: number): Observable<unknown> {
    return this.http.delete(`${this.baseUrl}/portafolios/${portafolioId}/posiciones/${posicionId}/`);
  }

  getRiesgoRanking(params?: { page?: number; pageSize?: number; ordering?: string }): Observable<PaginatedResponse<Riesgo>> {
    let httpParams = new HttpParams();
    if (params?.page) httpParams = httpParams.set('page', String(params.page));
    if (params?.pageSize) httpParams = httpParams.set('page_size', String(params.pageSize));
    if (params?.ordering) httpParams = httpParams.set('ordering', params.ordering);
    return this.http.get<PaginatedResponse<Riesgo>>(`${this.baseUrl}/riesgo/`, { params: httpParams });
  }

  getRiesgoPais(codigoISO: string): Observable<Riesgo> {
    return this.http.get<Riesgo>(`${this.baseUrl}/riesgo/${codigoISO}/`);
  }

  getRiesgoHistorico(codigoISO: string, params?: { start?: string; end?: string; page?: number; pageSize?: number }): Observable<PaginatedResponse<Riesgo>> {
    let httpParams = new HttpParams();
    if (params?.start) httpParams = httpParams.set('start', params.start);
    if (params?.end) httpParams = httpParams.set('end', params.end);
    if (params?.page) httpParams = httpParams.set('page', String(params.page));
    if (params?.pageSize) httpParams = httpParams.set('page_size', String(params.pageSize));
    return this.http.get<PaginatedResponse<Riesgo>>(`${this.baseUrl}/riesgo/${codigoISO}/historico/`, { params: httpParams });
  }

  recalcularRiesgo(): Observable<unknown> {
    return this.http.post(`${this.baseUrl}/riesgo/calcular/`, {});
  }

  getDashboardResumen(): Observable<DashboardResumen> {
    return this.http.get<DashboardResumen>(`${this.baseUrl}/dashboard/resumen/`);
  }

  getDashboardMapa(): Observable<DashboardMapaItem[]> {
    return this.http.get<DashboardMapaItem[]>(`${this.baseUrl}/dashboard/mapa/`);
  }

  getDashboardTendencias(tipo = 'INFLACION', paises: string[] = []): Observable<DashboardTendencias> {
    let params = new HttpParams().set('tipo', tipo);
    if (paises.length) params = params.set('paises', paises.join(','));
    return this.http.get<DashboardTendencias>(`${this.baseUrl}/dashboard/tendencias/`, { params });
  }

  getAlertas(params?: { tipo?: string; severidad?: string; leida?: 'true' | 'false' }): Observable<PaginatedResponse<Alerta>> {
    let httpParams = new HttpParams();
    if (params?.tipo) httpParams = httpParams.set('tipo', params.tipo);
    if (params?.severidad) httpParams = httpParams.set('severidad', params.severidad);
    if (params?.leida) httpParams = httpParams.set('leida', params.leida);
    return this.http.get<PaginatedResponse<Alerta>>(`${this.baseUrl}/alertas/`, { params: httpParams });
  }

  marcarAlertaLeida(id: number): Observable<unknown> {
    return this.http.put(`${this.baseUrl}/alertas/${id}/leer/`, {});
  }

  marcarAlertasLeidas(): Observable<unknown> {
    return this.http.put(`${this.baseUrl}/alertas/leer-todas/`, {});
  }

  getAlertasResumen(): Observable<unknown> {
    return this.http.get(`${this.baseUrl}/alertas/resumen/`);
  }
}
