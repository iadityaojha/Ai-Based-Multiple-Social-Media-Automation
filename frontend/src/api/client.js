import axios from 'axios';

// Create axios instance with base URL
const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

// =========================================
// API Keys
// =========================================
export const keysApi = {
    getStatus: () => api.get('/keys/status'),
    list: () => api.get('/keys/'),
    create: (data) => api.post('/keys/', data),
    update: (id, data) => api.put(`/keys/${id}`, data),
    delete: (id) => api.delete(`/keys/${id}`),
    test: (id) => api.post(`/keys/${id}/test`),
};

// =========================================
// Content Generation
// =========================================
export const generateApi = {
    generate: (data) => api.post('/generate/', data),
    listTopics: () => api.get('/generate/topics'),
    getTopic: (id) => api.get(`/generate/topics/${id}`),
    deleteTopic: (id) => api.delete(`/generate/topics/${id}`),
};

// =========================================
// Posts / Scheduling
// =========================================
export const postsApi = {
    list: (params) => api.get('/posts/', { params }),
    get: (id) => api.get(`/posts/${id}`),
    getStats: () => api.get('/posts/stats'),
    getUpcoming: () => api.get('/posts/upcoming'),
    update: (id, data) => api.put(`/posts/${id}`, data),
    approve: (id, data) => api.post(`/posts/${id}/approve`, data),
    cancel: (id) => api.post(`/posts/${id}/cancel`),
    retry: (id) => api.post(`/posts/${id}/retry`),
    delete: (id) => api.delete(`/posts/${id}`),
};

// =========================================
// Manual Post (with image upload)
// =========================================
export const manualPostApi = {
    uploadImage: (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/manual-post/upload-image', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },
    create: (data) => {
        const formData = new FormData();
        formData.append('content', data.content);
        formData.append('platforms', data.platforms.join(','));
        if (data.imageFilename) {
            formData.append('image_filename', data.imageFilename);
        }
        if (data.scheduleTime) {
            formData.append('schedule_time', data.scheduleTime);
        }
        return api.post('/manual-post/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },
};

export default api;
