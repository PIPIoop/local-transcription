import type {Transcription} from './types';
export const time=(seconds:number)=>{const s=Math.max(0,Math.floor(seconds));return [Math.floor(s/3600),Math.floor(s%3600/60),s%60].map(v=>String(v).padStart(2,'0')).join(':')};
export const size=(bytes:number)=>bytes>1024**2?`${(bytes/1024**2).toFixed(1)} МБ`:`${Math.round(bytes/1024)} КБ`;
export const transcriptText=(t:Transcription)=>{const names=Object.fromEntries(t.speakers.map(s=>[s.id,s.name]));return t.segments.map(s=>`[${time(s.start)}] ${names[s.speaker]||s.speaker}:\n${s.text}`).join('\n\n')};
export function download(name:string,content:string,type='text/plain'){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();URL.revokeObjectURL(url)}
