import {useRef,useState} from 'react';
import {FileAudio,UploadCloud,X,Sparkles} from 'lucide-react';
import {size} from '../utils';
type DisplayFile=Pick<File,'name'|'size'>;
type Props={file:DisplayFile|null;busy:boolean;progress:number;stage:string;elapsed:number;error?:string;onFile:(f:File|null)=>void;onStart:()=>void;onCancel:()=>void};
const accept='.mp3,.wav,.m4a,.aac,.flac,.ogg,.mp4,.webm,.mov,.mkv';
export function UploadZone({file,busy,progress,stage,elapsed,error,onFile,onStart,onCancel}:Props){const ref=useRef<HTMLInputElement>(null);const [drag,setDrag]=useState(false);const pick=(files:FileList|null)=>files?.[0]&&onFile(files[0]);const canStart=file instanceof File;const startOrPick=()=>canStart?onStart():ref.current?.click();return <section className={`upload-card ${drag?'dragging':''}`} onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={()=>setDrag(false)} onDrop={e=>{e.preventDefault();setDrag(false);pick(e.dataTransfer.files)}}>
 <input ref={ref} hidden type="file" accept={accept} onChange={e=>pick(e.target.files)}/>
 {!file?<><span className="upload-icon"><UploadCloud size={30}/></span><h1>Перетащите аудио или видео сюда</h1><p>MP3, WAV, M4A, MP4, WEBM, MOV и другие форматы · до 2 ГБ</p><button className="secondary" onClick={()=>ref.current?.click()}>Выбрать файл</button></>:<>
 <div className="file-row"><span className="file-icon"><FileAudio size={24}/></span><div className="file-meta"><strong>{file.name}</strong><span>{size(file.size)} · {file.name.split('.').pop()?.toUpperCase()}</span></div>{!busy&&<button className="icon-btn" onClick={()=>onFile(null)}><X size={18}/></button>}</div>
 {busy?<div className="progress-area"><div className="progress-head"><span><i className="pulse"/>{stage}</span><b>{progress}%</b></div><div className="progress"><i style={{width:`${progress}%`}}/></div><div className="progress-footer"><small>Прошло {Math.floor(elapsed/60)}:{String(Math.floor(elapsed%60)).padStart(2,'0')}</small><button className="cancel-transcription" onClick={onCancel}><X size={14}/>Отменить транскрибацию</button></div></div>:<button className="primary start" onClick={startOrPick}><Sparkles size={18}/>{canStart?"Начать транскрибацию":"Выбрать файл заново"}</button>}
 </>}{error&&<div className="error-box">{error}<button onClick={startOrPick}>{canStart?"Повторить":"Выбрать файл"}</button></div>}</section>}

