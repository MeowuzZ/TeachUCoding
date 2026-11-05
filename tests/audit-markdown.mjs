import fs from 'node:fs';
import assert from 'node:assert/strict';
import {marked} from '../public/vendor/marked.esm.js';
const issues=[],checked=[];
function inspect(id,source){
 const tokens=marked.lexer(source||'');
 let strong=0,code=0;
 marked.walkTokens(tokens,token=>{
  if(token.type==='strong')strong++;
  if(token.type==='code')code++;
  if(token.type==='text'&&/\*\*[^*\n]+\*\*/.test(token.text||''))issues.push({id,kind:'unrendered emphasis',text:token.text.slice(0,180)});
 });
 const rendered=marked.parse(source||'');
 const outsideCode=rendered.replace(/<pre\b[\s\S]*?<\/pre>/g,'').replace(/<code\b[\s\S]*?<\/code>/g,'');
 if(/<p>\s*#{1,6}\s/.test(outsideCode))issues.push({id,kind:'unrendered heading'});
 if(/```/.test(outsideCode))issues.push({id,kind:'unclosed fence'});
 checked.push({id,strong,code});
 return rendered;
}
for(const file of fs.readdirSync('public/engineering').filter(f=>f.endsWith('.json'))){
 const d=JSON.parse(fs.readFileSync('public/engineering/'+file));
 if(typeof d.body!=='string')continue;
 const html=inspect('engineering/'+file,d.body);
 if(d.body.includes('**动手观察**')){
  assert(html.includes('<strong>动手观察</strong>：'),file);
  assert(html.includes('<strong>容易忽略的边界</strong>：'),file);
 }
}
const course=JSON.parse(fs.readFileSync('course-data.json'));
for(const lesson of course.lessons)inspect('method/'+lesson.id,lesson.body);
for(const doc of course.resources)inspect('material/'+doc.id,doc.body);
for(const file of fs.readdirSync('public/curriculum').filter(f=>f.endsWith('.md')))inspect('curriculum/'+file,fs.readFileSync('public/curriculum/'+file,'utf8'));
inspect('project-guide',fs.readFileSync('public/engineering/project-guide.md','utf8'));
const sample=marked.parse('## 标题\n\n**重点**：说明\n\n- 一项\n- 二项\n\n[资料](https://example.com)\n\n```html\n<strong>示例源码</strong>\n```');
for(const expected of ['<h2>','<strong>重点</strong>','<ul>','<li>','<a href="https://example.com">','<pre><code','&lt;strong&gt;'])assert(sample.includes(expected),expected);
fs.writeFileSync('qa/markdown/逐节渲染核查.json',JSON.stringify({checked:checked.length,issues,lessons:checked},null,2));
console.log(JSON.stringify({checked:checked.length,issues:issues.length,examples:issues.slice(0,8)},null,2));
assert.equal(issues.length,0,'See qa/markdown/逐节渲染核查.json');
