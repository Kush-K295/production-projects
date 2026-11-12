import axios from 'axios';
import type { SearchPayload, SearchResponse } from '../types/book';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const searchBooks = async (query: string, nresults: number = 5): Promise<SearchResponse> => {
  const payload: SearchPayload = {
    query: query.trim(),
    nresults: Math.min(Math.max(nresults, 1), 20),
  };
  const response = await apiClient.post<SearchResponse>('/search', payload);
  return response.data;
};

