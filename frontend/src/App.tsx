import {useEffect,useRef,useState} from 'react';
import {LockKeyhole} from 'lucide-react';
import {api} from './api';
import {notifyProcessFinished,requestNotificationPermission} from './notifications';
import type {AIResult,OllamaStatus,Settings,Transcription} from './types';
import {Header} from './components/Header';
import {UploadZone} from './components/UploadZone';
import {TranscriptPanel} from './components/TranscriptPanel';
import {AIPanel} from './components/AIPanel';
import {SettingsModal} from './components/SettingsModal';

const defaults:Settings={transcription:{whisper_model:'small',language:'auto',device:'auto',diarization:false,speaker_count:null},ai:{ollama_url:'http://localhost:11434',model:'qwen3:8b',temperature:.2,context_length:32768}};

export default function App(){
 const [dark,setDark]=useState(()=>matchMedia('(prefers-color-scheme: dark)').matches);
 const [settings,setSettings]=useState(defaults);
 const [status,setStatus]=useState<OllamaStatus>({connected:false,models:[],modelAvailable:false});
 const [modal,setModal]=useState(false);
 const [file,setFile]=useState<File|null>(null);
 const [item,setItem]=useState<Transcription|null>(null);
 const [uploading,setUploading]=useState(false);
 const [error,setError]=useState('');
 const [results,setResults]=useState<Record<string,AIResult>>({});
 const [aiLoading,setAiLoading]=useState<string|null>(null);
 const [aiError,setAiError]=useState('');
 const [clock,setClock]=useState(Date.now());
 const controller=useRef<AbortController|null>(null);
 const statusObservedAt=useRef(Date.now());
 const previousTranscriptionStatus=useRef<Transcription['status']|undefined>(undefined);
 const busy=uploading||!!item&&['queued','processing'].includes(item.status);

 useEffect(()=>{document.documentElement.dataset.theme=dark?'dark':'light'},[dark]);
 useEffect(()=>{
  const activeId=sessionStorage.getItem('activeTranscriptionId');
  const restore=activeId?api.transcription(activeId):api.activeTranscription();
  restore.then(active=>{setItem(active);sessionStorage.setItem('activeTranscriptionId',active.id)}).catch(()=>sessionStorage.removeItem('activeTranscriptionId'));
  api.settings().then(setSettings).catch(()=>{});
  const check=()=>api.status().then(setStatus).catch(()=>setStatus({connected:false,models:[],modelAvailable:false}));
  check();const id=setInterval(check,30000);return()=>clearInterval(id)
 },[]);
 useEffect(()=>{statusObservedAt.current=Date.now();setClock(Date.now())},[item?.elapsed]);
 useEffect(()=>{
  const previous=previousTranscriptionStatus.current;
  const current=item?.status;
  if(previous&&['queued','processing'].includes(previous)&&current==='completed')notifyProcessFinished('Транскрибация завершена');
  if(previous&&['queued','processing'].includes(previous)&&current==='error')notifyProcessFinished(item?.error||'Ошибка транскрибации','error');
  previousTranscriptionStatus.current=current;
 },[item?.status,item?.error]);
 useEffect(()=>{if(!busy)return;const id=setInterval(()=>setClock(Date.now()),1000);return()=>clearInterval(id)},[busy]);
 useEffect(()=>{
  if(!item||!['queued','processing'].includes(item.status))return;
  const id=setInterval(async()=>{try{const next=await api.transcription(item.id);setItem(next);if(next.status==='error')setError(next.error||'Ошибка транскрибации')}catch{setError('Потеряно соединение с backend.')}} ,1000);
  return()=>clearInterval(id)
 },[item?.id,item?.status]);

 const start=async()=>{if(!file)return;requestNotificationPermission();setError('');setUploading(true);setItem(null);setResults({});try{const created=await api.transcribe(file);setItem(created);sessionStorage.setItem('activeTranscriptionId',created.id)}catch(e){setError(e instanceof Error?e.message:'Не удалось загрузить файл')}finally{setUploading(false)}};
 const cancelTranscription=async()=>{if(!item)return;setError('');try{setItem(await api.cancelTranscription(item.id))}catch(e){setError(e instanceof Error?e.message:'Не удалось отменить транскрибацию')}};
 const analyze=async(scenario:string,question?:string)=>{if(!item)return;requestNotificationPermission();setAiError('');setAiLoading(scenario);controller.current=new AbortController();try{const result=await api.analyze(item.id,scenario,question,controller.current.signal);setResults(r=>({...r,[scenario]:result}));notifyProcessFinished(`AI-анализ «${result.title}» завершён`)}catch(e){if((e as Error).name!=='AbortError'){const message=e instanceof Error?e.message:'Ошибка AI-анализа';setAiError(message);notifyProcessFinished(message,'error')}}finally{setAiLoading(null)}};
 const liveElapsed=(item?.elapsed??0)+(busy?(clock-statusObservedAt.current)/1000:0);
 return <div className="app"><Header dark={dark} onTheme={()=>setDark(!dark)} connected={status.connected&&status.modelAvailable} model={settings.ai.model} onSettings={()=>setModal(true)}/><main><div className="hero"><span className="kicker">Ваши разговоры — в ясные действия</span><h1>Транскрибация встреч.<br/><em>Локально и приватно.</em></h1><p>Whisper распознаёт речь, а ваша локальная модель превращает её в структурированные итоги.</p></div><UploadZone file={file??item?.file??null} busy={busy} progress={item?.progress??(uploading?4:0)} stage={item?.stage??'Загрузка файла'} elapsed={liveElapsed} error={error} onFile={f=>{setFile(f);setItem(null);sessionStorage.removeItem('activeTranscriptionId');setError('')}} onStart={start} onCancel={cancelTranscription}/>
 {item?.status==='completed'&&<div className="workspace"><TranscriptPanel item={item} onChange={setItem} onSave={async()=>setItem(await api.updateTranscription(item))}/><AIPanel results={results} loading={aiLoading} error={aiError} onRun={analyze} onCancel={()=>controller.current?.abort()}/></div>}
 {!item&&<div className="privacy"><LockKeyhole size={18}/><div><strong>Локальная обработка</strong><span>При локальной конфигурации данные не отправляются во внешние AI-сервисы. Ollama получает только актуальный текст транскрипции — никогда не исходный медиафайл.</span></div></div>}
 </main><footer><span>Local Transcript AI</span><span>Файл → Whisper → текст → Ollama</span></footer><SettingsModal open={modal} settings={settings} onClose={()=>setModal(false)} onSave={async s=>setSettings(await api.saveSettings(s))}/></div>
}



