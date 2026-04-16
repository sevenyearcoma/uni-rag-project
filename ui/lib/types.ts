export interface ChunkMeta {
  filename: string;
  title: string;
  date: string;
  chunk_index: number;
  strategy: string;
  token_count: number;
  source_url?: string;
}

export interface RetrievedChunk {
  text: string;
  metadata: ChunkMeta;
  score: number;
  id: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  chunks?: RetrievedChunk[];
  isRefusal?: boolean;
  isLoading?: boolean;
}

export interface QueryResponse {
  answer: string;
  sources: string[];
  chunks: RetrievedChunk[];
  provider: string;
  model: string;
}

export interface IngestResponse {
  documents_loaded: number;
  chunks_created: number;
  total_vectors: number;
  strategy: string;
}
