import type {AIResult,OllamaStatus,Recommendation,Settings,Transcription} from './types';
async function request<T>(url:string,options?:RequestInit):Promise<T>{
 const response=await fetch(url,options); if(!response.ok){let detail='Произошла ошибка.';try{detail=(await response.json()).detail||detail}catch{} throw new Error(detail)} return response.json();
}
export const api={
 settings:()=>request<Settings>('/api/settings'),
 saveSettings:(body:Settings)=>request<Settings>('/api/settings',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),
 status:()=>request<OllamaStatus>('/api/ollama/status'),
 recommendation:()=>request<Recommendation>('/api/transcription/recommendation'),
 transcribe:(file:File)=>{const body=new FormData();body.append('file',file);return request<Transcription>('/api/transcribe',{method:'POST',body})},
 activeTranscription:()=>request<Transcription>('/api/transcription/active/current'),
 cancelTranscription:(id:string)=>request<Transcription>(`/api/transcription/${id}/cancel`,{method:'POST'}),
 transcription:(id:string)=>request<Transcription>(`/api/transcription/${id}`),
 updateTranscription:(item:Transcription)=>request<Transcription>(`/api/transcription/${item.id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({speakers:item.speakers,segments:item.segments})}),
 analyze:(id:string,scenario:string,question?:string,signal?:AbortSignal)=>request<AIResult>('/api/ai/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({transcription_id:id,scenario,question}),signal})
};
