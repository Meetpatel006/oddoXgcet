export const API_BASE_URL = "http://localhost:8000/api/v1";

interface FetchOptions extends RequestInit {
    headers?: Record<string, string>;
}

export const api = {
    async get(endpoint: string, token?: string) {
        const headers: Record<string, string> = {
            "Content-Type": "application/json",
        };
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: "GET",
            headers,
        });
        return handleResponse(response);
    },

    async post(endpoint: string, data: any, token?: string) {
        const headers: Record<string, string> = {
            "Content-Type": "application/json",
        };
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: "POST",
            headers,
            body: JSON.stringify(data),
        });
        return handleResponse(response);
    },

    async postFormData(endpoint: string, formData: FormData, token?: string) {
        const headers: Record<string, string> = {};
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        // Content-Type is set automatically by browser for FormData

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: "POST",
            headers,
            body: formData,
        });
        return handleResponse(response);
    },
};

async function handleResponse(response: Response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed with status ${response.status}`);
    }
    return response.json();
}
