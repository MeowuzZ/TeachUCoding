/* Local literal, typo and curated vocabulary expansion. No AI model or remote service. */
if(typeof importScripts==='function')importScripts('/search-vocabulary.js');
const vocabulary=typeof module!=='undefined'?require('./search-vocabulary.js'):COURSE_SEARCH_GROUPS;
const aliases=new Map();
for(const group of vocabulary)for(const term of group){const key=term.toLowerCase();aliases.set(key,[...new Set([...(aliases.get(key)||[]),...group.filter(x=>x.toLowerCase()!==key)])]);}
function expandedOccurrences(text,term){
  return occurrences(text,term).filter(([a,b])=>!(/[a-z0-9_]/i.test(term[0])&&/[a-z0-9_]/i.test(text[a-1]||''))&&!(/[a-z0-9_]/i.test(term.at(-1))&&/[a-z0-9_]/i.test(text[b]||'')));
}
let indexPromise;
const escapeLiteral=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
function occurrences(text,term){
  const re=new RegExp(escapeLiteral(term),'giu'),ranges=[];let m;
  while((m=re.exec(text))!==null)ranges.push([m.index,m.index+m[0].length]);
  return ranges;
}
function oneEdit(a,b){
  if(a===b)return true;
  if(Math.abs(a.length-b.length)>1)return false;
  let i=0;while(i<Math.min(a.length,b.length)&&a[i]===b[i])i++;
  if(a.length===b.length)return a.slice(i+1)===b.slice(i+1)||(a[i]===b[i+1]&&a[i+1]===b[i]&&a.slice(i+2)===b.slice(i+2));
  return a.length>b.length?a.slice(i+1)===b.slice(i):a.slice(i)===b.slice(i+1);
}
function mergeRanges(ranges){
  const out=[];
  for(const range of ranges.sort((a,b)=>a[0]-b[0]||b[1]-a[1])){
    const last=out.at(-1);
    if(last&&range[0]<last[1])last[1]=Math.max(last[1],range[1]);else out.push([...range]);
  }
  return out;
}
function searchLessons(rows,query,fuzzy=false){
  if(!query.trim())return [];
  const terms=fuzzy?[...new Set((aliases.has(query.trim().toLowerCase())?[query.trim().toLowerCase()]:query.trim().toLowerCase().split(/\s+/u)))]:[query];
  const results=[];
  for(const row of rows){
    let ranges=[],corrections=[],expansions=[],allExact=true,missing=false,words;
    const phrase=occurrences(row.text,query);
    if(!fuzzy){if(!phrase.length)continue;ranges=phrase;}
    else for(const term of terms){
      const exact=occurrences(row.text,term);
      if(exact.length){ranges.push(...exact);continue;}
      allExact=false;
      let matches=[];
      if(/^[a-z]{5,}$/.test(term)){
        words ||= [...row.text.matchAll(/(?<![\p{L}\p{N}_])[a-zA-Z]+(?![\p{L}\p{N}_+#])/gu)];
        matches=words.filter(m=>oneEdit(term,m[0].toLowerCase()));
      }
      if(matches.length){
        ranges.push(...matches.map(m=>[m.index,m.index+m[0].length]));
        corrections.push({term,words:[...new Set(matches.map(m=>m[0]))]});continue;
      }
      const expanded=(aliases.get(term)||[]).map(word=>({word,ranges:expandedOccurrences(row.text,word)})).filter(x=>x.ranges.length);
      if(!expanded.length){missing=true;break;}
      ranges.push(...expanded.flatMap(x=>x.ranges));
      expansions.push({term,words:expanded.map(x=>x.word)});
    }
    if(missing)continue;
    ranges=mergeRanges(ranges);
    const rank=!fuzzy||phrase.length?0:allExact?1:expansions.length?3:2;
    const first=ranges[0],start=Math.max(0,first[0]-55),end=Math.min(row.text.length,first[1]+115),prefix=start?'…':'';
    const {text,...metadata}=row;
    const titleRanges=fuzzy?mergeRanges(terms.flatMap(t=>occurrences(row.title,t))):occurrences(row.title,query);
    for(const c of corrections)for(const w of c.words)titleRanges.push(...occurrences(row.title,w));
    for(const e of expansions)for(const w of e.words)titleRanges.push(...expandedOccurrences(row.title,w));
    results.push({...metadata,expansions,count:ranges.length,rank,corrections,titleRanges:mergeRanges(titleRanges),snippet:prefix+text.slice(start,end)+(end<text.length?'…':''),snippetRanges:ranges.filter(r=>r[0]<end&&r[1]>start).map(r=>[Math.max(r[0],start)-start+prefix.length,Math.min(r[1],end)-start+prefix.length])});
  }
  return results.sort((a,b)=>a.rank-b.rank||b.count-a.count);
}
if(typeof self!=='undefined')self.onmessage=async ({data:{id,query,fuzzy=false}})=>{
  try{
    indexPromise ||= fetch('/search-index.json').then(r=>{if(!r.ok)throw Error('index');return r.json();}).catch(e=>{indexPromise=null;throw e;});
    self.postMessage({id,query,fuzzy,results:searchLessons(await indexPromise,query,fuzzy)});
  }catch{self.postMessage({id,error:true});}
};
if(typeof module!=='undefined')module.exports={searchLessons,oneEdit,mergeRanges};
