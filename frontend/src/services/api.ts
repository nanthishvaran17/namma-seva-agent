const API_BASE = '/api/v1';

export class ApiClient {
  private static token: string | null = localStorage.getItem('namma_seva_token');

  static setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('namma_seva_token', token);
    } else {
      localStorage.removeItem('namma_seva_token');
    }
  }

  static getToken(): string | null {
    return this.token;
  }

  private static async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(err.detail || `HTTP Error ${response.status}`);
    }

    return response.json();
  }

  // Services
  static async getServices(query?: string, category?: string) {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (category) params.append('category', category);
    return this.request<any[]>(`/services?${params.toString()}`);
  }

  static async getServiceDetails(serviceId: string) {
    return this.request<any>(`/services/${serviceId}`);
  }

  static async getActionPlan(targetServiceId: string, completed: string[] = [], docs: string[] = []) {
    return this.request<any>('/services/action-plan', {
      method: 'POST',
      body: JSON.stringify({
        target_service_id: targetServiceId,
        user_completed_services: completed,
        user_available_documents: docs
      })
    });
  }

  // Chat
  static async sendChatMessage(message: string, conversationId?: string, language: string = 'ta') {
    return this.request<any>('/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        language
      })
    });
  }

  // Auth
  static async register(data: any) {
    const res = await this.request<any>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    this.setToken(res.access_token);
    return res;
  }

  static async login(data: any) {
    const res = await this.request<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    this.setToken(res.access_token);
    return res;
  }

  static async getProfile() {
    return this.request<any>('/auth/me');
  }

  static async exportData() {
    return this.request<any>('/auth/me/export');
  }

  static async deleteData() {
    return this.request<any>('/auth/me/data', { method: 'DELETE' });
  }

  // Tasks
  static async getTasks() {
    return this.request<any[]>('/tasks');
  }

  static async createTask(serviceId: string) {
    return this.request<any>('/tasks', {
      method: 'POST',
      body: JSON.stringify({ service_id: serviceId })
    });
  }

  static async updateTaskStatus(taskId: string, status: string, reason?: string) {
    return this.request<any>(`/tasks/${taskId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, reason })
    });
  }

  // Documents
  static async uploadDocument(file: File, docCode: string, taskId?: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_code', docCode);
    if (taskId) {
      formData.append('task_id', taskId);
    }

    const headers: Record<string, string> = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || `Upload failed with status ${res.status}`);
    }

    return res.json();
  }

  static async getDocuments(taskId?: string) {
    const url = taskId ? `/documents?task_id=${taskId}` : '/documents';
    return this.request<any[]>(url);
  }

  static async verifyDocument(documentId: string, corrections: Record<string, any> = {}) {
    return this.request<any>(`/documents/${documentId}/verify`, {
      method: 'PATCH',
      body: JSON.stringify({
        is_verified: true,
        user_corrections: corrections
      })
    });
  }

  // Reminders
  static async getReminders() {
    return this.request<any[]>('/reminders');
  }

  // Admin
  static async getAdminPlaybooks() {
    return this.request<any[]>('/admin/playbooks');
  }

  static async updatePlaybookStatus(serviceId: string, status: string, reviewNotes?: string) {
    return this.request<any>(`/admin/playbooks/${serviceId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ verification_status: status, review_notes: reviewNotes })
    });
  }

  static async getAdminMetrics() {
    return this.request<any>('/admin/metrics');
  }

  static async getAuditLogs() {
    return this.request<any[]>('/admin/audit-logs');
  }

  // WhatsApp Simulator
  static async simulateWhatsApp(fromPhone: string, messageText: string) {
    return this.request<any>('/whatsapp/simulate', {
      method: 'POST',
      body: JSON.stringify({
        from_phone: fromPhone,
        message_text: messageText
      })
    });
  }
}
