import type { ContentTypeId } from "./types";

export interface ContentType {
  id: ContentTypeId;
  label: string;
  description: string;
}

// Para adicionar um tipo novo no futuro: acrescente um item aqui
// (e o id em types.ts). A interface se atualiza sozinha.
export const CONTENT_TYPES: ContentType[] = [
  { id: "ugc", label: "UGC", description: "Vídeos mais naturais, pessoais e dinâmicos." },
  { id: "produto", label: "Produto", description: "Maquiagem, skincare ou produto em detalhes." },
  { id: "tutorial", label: "Tutorial", description: "Ensinando aplicação, uso ou passo a passo." },
  { id: "oferta", label: "Oferta", description: "Preço, promoção, kit, desconto ou campanha." },
  { id: "falando-camera", label: "Falando para câmera", description: "A pessoa fala diretamente com o público." },
];
