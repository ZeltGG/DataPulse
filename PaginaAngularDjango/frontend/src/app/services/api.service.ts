import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

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

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getProjects(): Observable<Project[]> {
    return this.http.get<Project[]>(`${this.baseUrl}/projects/`);
  }

  createContactMessage(payload: ContactMessageCreate): Observable<any> {
    return this.http.post(`${this.baseUrl}/contact-messages/`, payload);
  }
}