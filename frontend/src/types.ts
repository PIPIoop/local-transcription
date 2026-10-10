export type Speaker={id:string;name:string};
export type Segment={id:string;start:number;end:number;speaker:string;text:string};
export type Transcription={id:string;status:'queued'|'processing'|'completed'|'error'|'cancelled';stage:string;progress:number;elapsed:number;file:{name:string;size:number;duration:number;format:string};language:string;speakers:Speaker[];segments:Segment[];error?:string};
export type Settings={transcription:{whisper_model:string;language:string;device:'auto'|'cpu'|'cuda';diarization:boolean;speaker_count:number|null};ai:{ollama_url:string;model:string;temperature:number;context_length:number}};
export type AIResult={scenario:string;title:string;content:string};
export type OllamaStatus={connected:boolean;models:string[];modelAvailable:boolean};
export type Recommendation={recommended_model:string;recommended_device:'cpu'|'cuda';reason:string;hardware:{os:string;cpu_threads:number;ram_gb:number;cuda:boolean;cuda_detected:boolean;cuda_issue:string|null;vram_gb:number};models:Array<{model:string;speed:string;accuracy:string;memory_gb:number;best_for:string}>};


