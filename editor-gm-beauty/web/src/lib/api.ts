// Ponto único de comunicação com o backend (FastAPI).
// Fase 1: ainda devolve dados fictícios. Na Fase 2 estas funções passam
// a chamar a API de verdade — as telas não precisam mudar.
import { MOCK_PROJECTS, getMockProject } from "./mock-data";
import type { Project } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function listProjects(): Promise<Project[]> {
  return MOCK_PROJECTS;
}

export async function getProject(id: string): Promise<Project> {
  return getMockProject(id);
}
