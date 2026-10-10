import {useEffect,useState} from 'react';
import {CheckCircle2,Cpu,Gauge,Loader2,SlidersHorizontal,Sparkles,WandSparkles,X} from 'lucide-react';
import type {Recommendation,Settings} from '../types';
import {api} from '../api';

type Props={open:boolean;settings:Settings;onClose:()=>void;onSave:(s:Settings)=>Promise<void>};

export function SettingsModal({open,settings,onClose,onSave}:Props){
 const [form,setForm]=useState(settings);
 const [checking,setChecking]=useState(false);
 const [check,setCheck]=useState<boolean|null>(null);
 const [recommendation,setRecommendation]=useState<Recommendation|null>(null);
 const [recommendationError,setRecommendationError]=useState('');
 useEffect(()=>{
  setForm(settings);
  if(open){
   setRecommendationError('');
   api.recommendation().then(setRecommendation).catch(()=>setRecommendationError('Не удалось определить конфигурацию компьютера.'));
  }
 },[settings,open]);
 if(!open)return null;
 const test=async()=>{setChecking(true);try{await api.saveSettings(form);const s=await api.status();setCheck(s.connected&&s.modelAvailable)}finally{setChecking(false)}};
 const applyRecommendation=()=>{if(!recommendation)return;setForm({...form,transcription:{...form.transcription,whisper_model:recommendation.recommended_model,device:recommendation.recommended_device}})};
 return <div className="modal-backdrop" onMouseDown={e=>e.target===e.currentTarget&&onClose()}><div className="modal"><div className="modal-head"><div><span className="eyebrow">Конфигурация</span><h2>Настройки</h2></div><button className="icon-btn" onClick={onClose}><X size={20}/></button></div>
 <div className="settings-section"><h3><Cpu size={18}/>Транскрибация</h3>
  {recommendation?<div className="recommendation-card"><span className="recommendation-icon"><WandSparkles size={19}/></span><div><small>Рекомендация для этого компьютера</small><strong>{recommendation.recommended_model} · {recommendation.recommended_device.toUpperCase()}</strong><p>{recommendation.reason}</p><span>{recommendation.hardware.cpu_threads} потоков CPU · {recommendation.hardware.ram_gb} ГБ RAM{recommendation.hardware.cuda?` · CUDA${recommendation.hardware.vram_gb?` ${recommendation.hardware.vram_gb} ГБ VRAM`:''}`:recommendation.hardware.cuda_detected?' · GPU найден, CUDA runtime не готов':' · без CUDA'}</span></div><button onClick={applyRecommendation}>Применить</button></div>:<div className="recommendation-loading">{recommendationError||<><Loader2 className="spin" size={15}/> Анализируем конфигурацию компьютера...</>}</div>}
  <div className="form-grid"><label>Модель Whisper<select value={form.transcription.whisper_model} onChange={e=>setForm({...form,transcription:{...form.transcription,whisper_model:e.target.value}})}><option value="tiny">tiny — максимум скорости</option><option value="base">base — экономный вариант</option><option value="small">small — баланс качества</option><option value="medium">medium — высокая точность</option><option value="large-v3">large-v3 — максимум качества</option></select></label><label>Язык<select value={form.transcription.language} onChange={e=>setForm({...form,transcription:{...form.transcription,language:e.target.value}})}><option value="auto">Auto</option><option value="ru">Russian</option><option value="en">English</option><option value="de">German</option><option value="fr">French</option></select></label><label>Устройство<select value={form.transcription.device} onChange={e=>setForm({...form,transcription:{...form.transcription,device:e.target.value as 'auto'|'cpu'|'cuda'}})}><option value="auto">Auto</option><option value="cpu">CPU</option><option value="cuda">CUDA</option></select></label><label>Количество спикеров<input type="number" min="1" max="20" placeholder="Auto" value={form.transcription.speaker_count??''} onChange={e=>setForm({...form,transcription:{...form.transcription,speaker_count:e.target.value?Number(e.target.value):null}})}/></label></div>
  {recommendation&&<div className="model-guide"><Gauge size={15}/>{recommendation.models.map(model=><span key={model.model} className={form.transcription.whisper_model===model.model?'selected':''} title={`${model.accuracy} точность · ~${model.memory_gb} ГБ памяти · ${model.best_for}`}>{model.model}<small>{model.speed}</small></span>)}</div>}
  <label className="switch-row"><div><strong>Diarization</strong><span>Определять разных спикеров через pyannote</span></div><input type="checkbox" checked={form.transcription.diarization} onChange={e=>setForm({...form,transcription:{...form.transcription,diarization:e.target.checked}})}/><i/></label></div>
 <div className="settings-section"><h3><Sparkles size={18}/>AI Assistant</h3><div className="form-grid"><label className="wide">Ollama URL<input value={form.ai.ollama_url} onChange={e=>setForm({...form,ai:{...form.ai,ollama_url:e.target.value}})}/></label><label>Model<input value={form.ai.model} onChange={e=>setForm({...form,ai:{...form.ai,model:e.target.value}})}/></label><label>Temperature<input type="number" min="0" max="2" step="0.1" value={form.ai.temperature} onChange={e=>setForm({...form,ai:{...form.ai,temperature:Number(e.target.value)}})}/></label><label>Context length<input type="number" min="2048" step="1024" value={form.ai.context_length} onChange={e=>setForm({...form,ai:{...form.ai,context_length:Number(e.target.value)}})}/></label></div><button className="connection-test" onClick={test} disabled={checking}>{checking?<Loader2 className="spin" size={17}/>:check===true?<CheckCircle2 size={17}/>:<SlidersHorizontal size={17}/>} {checking?'Проверяем...':check===true?'Ollama и модель доступны':check===false?'Ollama или модель недоступны':'Проверить подключение'}</button></div>
 <div className="modal-actions"><button className="secondary" onClick={onClose}>Отмена</button><button className="primary" onClick={async()=>{await onSave(form);onClose()}}>Сохранить настройки</button></div></div></div>
}

