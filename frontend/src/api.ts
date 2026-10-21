export const API=import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
export async function request<T>(path:string,method='GET',body?:unknown):Promise<T>{
 let response:Response;
 try{response=await fetch(API+'/api'+path,{method,headers:body?{'Content-Type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined});}
 catch{throw new Error('Não foi possível conectar. Confira se o backend está em execução.');}
 if(!response.ok){const error=await response.json().catch(()=>({}));throw new Error(typeof error.detail==='string'?error.detail:'Não foi possível concluir. Confira os campos e tente novamente.');}
 return response.json();
}
export const money=(c:number)=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(c/100);
export const dateTime=(s:string)=>new Date(s).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo',dateStyle:'short',timeStyle:'short'});
export function cents(s:string){const normalized=s.trim().replace(',','.');if(!/^\d+(\.\d{1,2})?$/.test(normalized))throw new Error('Preço inválido. Use, por exemplo, 89,90.');const [a,b='']=normalized.split('.');return Number(a)*100+Number(b.padEnd(2,'0'));}
export function localDate(){return new Date().toLocaleDateString('sv-SE',{timeZone:'America/Sao_Paulo'});}
export function utcDate(s:string){return s?new Date(s+'-03:00').toISOString():undefined;}
