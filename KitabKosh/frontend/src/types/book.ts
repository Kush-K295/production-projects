export interface Book {
  title: string;
  author: string;
  edition: string;
  publisher: string;
  year: string;
  accession_nos: string[];
}

export interface SearchResponse {
  results: Book[];
}

export interface SearchPayload {
  query: string;
  nresults: number;
}

