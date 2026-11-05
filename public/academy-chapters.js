import {esc,icon} from './academy-utils.js';

export const cleanTopic=title=>title.replace(/^第\s*[\d一二三四五六七八九十百]+\s*章\s*[：:、.．-]?\s*/,'').replace(/（\d+学时）/g,'').trim();
export function curriculumChapters(course){
 return (course.chapters||course.modules.map(m=>({id:m.id,title:m.title,modules:[m.id]}))).map(ch=>({...ch,topics:ch.modules.map(id=>course.modules.find(m=>m.id===id)).filter(Boolean)}));
}
function legacyNames(chapter){
 const parts=chapter.title.split(' · ');
 if(parts.length>1)return{title:parts[0],topic:cleanTopic(parts.slice(1).join(' · '))};
 const t=chapter.title;
 if(/Python 编程基础/.test(t))return{title:'Python 编程基础',topic:t.replace('Python 编程基础','').replace(/^[（(]|[）)]/g,'').replace(/^[上下]：/,'')};
 if(chapter.stage===6){
  const title=/课程导览|生成式 AI|选择与对比|负责任/.test(t)?'AI 基础与使用边界':/Prompt|文本生成|聊天应用|AI 图像|低代码|Function Calling|体验与安全/.test(t)?'AI 应用开发':/向量|RAG|开源模型/.test(t)?'检索增强与模型部署':/微调|强化学习|Agentic RL/.test(t)?'模型训练与优化':/可信|校园 AI/.test(t)?'AI 项目交付':'Agent 设计与工程';
  return{title,topic:cleanTopic(t)};
 }
 return{title:cleanTopic(t),topic:cleanTopic(t)};
}
export function legacyChapters(catalog){
 const groups=[];
 for(const chapter of catalog.chapters){
  const names=legacyNames(chapter);
  // Keep first-occurrence chapter order, and original topic/lesson IDs for records.
  let group=groups.find(g=>g.title===names.title);
  if(!group){group={id:'legacy-'+chapter.id,title:names.title,topics:[]};groups.push(group)}
  group.topics.push({...chapter,topicTitle:names.topic});
 }
 return groups;
}
export function legacyLocation(groups,lesson){
 const chapter=groups.find(g=>g.topics.some(t=>t.id===lesson.chapter));
 const topic=chapter?.topics.find(t=>t.id===lesson.chapter);
 return{chapter,topic,label:chapter&&topic?chapter.title+' / '+topic.topicTitle:''};
}
export function legacyOutline(groups,active,getLesson,completed){
 return groups.map(g=>{
  const current=g.topics.some(t=>t.id===active.chapter);
  return `<details class="outline-chapter" ${current?'open':''}><summary>${icon('book',14)}<span>${esc(g.title)}</span><small>${g.topics.length} 主题</small>${icon('chevron',13)}</summary><div class="outline-topics">${g.topics.map(t=>`<details class="outline-topic" ${t.id===active.chapter?'open':''}><summary><span>${esc(t.topicTitle)}</span>${icon('chevron',12)}</summary><div>${t.lessons.map((id,i)=>{const l=getLesson(id);return `<a class="outline-lesson ${id===active.id?'current':''}" href="#course/engineering/${id}/learn" ${id===active.id?'aria-current="page"':''}><span class="lesson-dot ${completed(id)?'complete':''}">${completed(id)?icon('check',10):String(i+1).padStart(2,'0')}</span><span>${esc(l.title)}</span></a>`}).join('')}</div></details>`).join('')}</div></details>`;
 }).join('');
}
