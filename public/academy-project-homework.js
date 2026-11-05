import {esc,icon} from './academy-utils.js';

export function localHomeworkPage(data,course,lesson,completed,next){
 const task=data?.[course+':'+lesson.id];
 if(!task)return '<section class="article-card"><h2>作业暂未就绪</h2><p>请刷新页面重试。</p></section>';
 return `<div class="homework-layout"><section class="article-card local-homework" data-homework-key="${esc(course+':'+lesson.id)}"><div class="homework-card-heading"><span class="surface-label">${icon('code',16)} 本地项目作业</span><span class="homework-chip">${esc(task.type)}</span></div><h2>${esc(task.project)}</h2><p class="homework-subtitle">${esc(task.title)}</p><div class="homework-meta"><span>${task.stack==='web'?'网页项目':task.stack==='java'?'Java 项目':'Python 项目'}</span><span>关键词填空</span><span>本地完成</span></div><div class="homework-focus"><span>这一节要解决什么</span><p>${esc(task.focus)}</p></div><div class="homework-block"><h3><span>01</span> 按顺序完成</h3><ol class="homework-checklist">${task.requirements.map((x,i)=>`<li><span>${String(i+1).padStart(2,'0')}</span><p>${esc(x)}</p></li>`).join('')}</ol></div><div class="homework-block"><h3><span>02</span> 启动后检查结果</h3><p class="homework-run">${esc(task.run)}</p></div><div class="homework-download"><div><strong>领取这一节的项目文件</strong><p>代码骨架 · 关键词词库 · 运行说明 · 验收清单</p></div><a class="button primary" href="${esc(task.download)}" download>${icon('download',16)} 下载本节项目包</a></div><details class="homework-acceptance"><summary>核对成果，安排下一轮改进 ${icon('chevron',15)}</summary><ul>${task.checks.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><p>${task.milestones.map(esc).join(' → ')} → 模块拆分与测试交付。</p></details></section><section class="article-card reference-section"><div class="homework-card-heading"><span class="surface-label">${icon('book',16)} 学习参考</span><span class="homework-chip">完成尝试再对照</span></div><div class="reference-intro"><div class="reference-symbol">${icon('code',24)}</div><h2>参考实现与填空解析</h2><p>先解释自己的做法，再核对参考实现。<br>这里提供基础版本，以及本节关键位置的解析。</p><button class="button" id="open-reference">${icon('right',15)} 拼合图案，查看参考实现</button><small>拼合图案后显示代码</small></div><div id="reference-challenge" hidden></div><div id="reference-result" hidden></div></section></div><div class="step-action homework-footer"><span>请核对本地运行结果，再留下这节的完成记录。</span><div class="button-row"><button class="button ${completed?'success':''}" data-mark="practice">${icon('check',16)} ${completed?'本节完成记录已保存':'记录本节已完成'}</button><a class="button" href="${esc(next)}">项目推进安排 ${icon('right',15)}</a></div></div>`;
}

const randomInt=(min,max)=>min+crypto.getRandomValues(new Uint32Array(1))[0]%(max-min+1);
export function bindLocalHomework(data,root){
 const card=root.querySelector('[data-homework-key]');
 if(!card)return;
 const task=data[card.dataset.homeworkKey],open=root.querySelector('#open-reference'),host=root.querySelector('#reference-challenge'),result=root.querySelector('#reference-result');
 let target,tiles=[],source,slider,canvas,message,attempts=0,verified=false,loading=false,idleTimer=null,checking=false;
 function create(){
  if(loading)return;
  clearTimeout(idleTimer);checking=false;
  verified=false;attempts=0;result.hidden=true;result.replaceChildren();
  host.hidden=false;host.innerHTML=`<div class="letter-puzzle"><p id="puzzle-instruction">拖动滑块拼合字母，停留 1 秒后自动验证。拼合失败将自动更换图片，也可点击右侧刷新图标换图。</p><canvas width="560" height="280" role="img" aria-label="彩色字母碎片拼图，请调整下方滑块"></canvas><label for="letter-slider">移动滑块，观察图案</label><div class="puzzle-control-row"><div class="puzzle-slider-wrap"><input id="letter-slider" type="range" min="0" max="100" step="1" value="0" aria-describedby="puzzle-instruction"><span class="puzzle-success-label" hidden>验证成功</span></div><button class="puzzle-refresh" id="new-puzzle" type="button" aria-label="换一张拼图" title="换一张拼图"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 7v5h-5"/><path d="M4 17v-5h5"/><path d="M6.1 7a7 7 0 0 1 11.6-1L20 9M4 15l2.3 3A7 7 0 0 0 17.9 17"/></svg></button></div><p role="status" aria-live="polite" id="puzzle-message">拖动后停留 1 秒，即可自动验证。</p></div>`;
  canvas=host.querySelector('canvas');slider=host.querySelector('input');message=host.querySelector('#puzzle-message');target=randomInt(18,82);
  source=document.createElement('canvas');source.width=560;source.height=280;const ctx=source.getContext('2d');
  const letter='ABCDEFGHJKLMNPQRSTUVWXYZ'[randomInt(0,23)];
  ctx.font='900 230px Arial, sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(letter,280,150);
  ctx.globalCompositeOperation='source-in';
  const gradient=ctx.createLinearGradient(170,30,380,250);gradient.addColorStop(0,'#ef5f85');gradient.addColorStop(.45,'#6e8cff');gradient.addColorStop(1,'#37cbb2');ctx.fillStyle=gradient;ctx.fillRect(0,0,560,280);
  ctx.globalCompositeOperation='source-atop';
  for(let y=32;y<260;y+=18)for(let x=150;x<420;x+=18){ctx.fillStyle=['#ffe9ad','#fff9','#22366088'][randomInt(0,2)];ctx.beginPath();ctx.arc(x+randomInt(-3,3),y,randomInt(2,5),0,Math.PI*2);ctx.fill();}
  tiles=[];
  for(let y=20;y<260;y+=20)for(let x=160;x<400;x+=20){
   const pixels=ctx.getImageData(x,y,20,20).data;
   if(!pixels.some((value,index)=>index%4===3&&value>0))continue;
   tiles.push({x,y,dx:randomInt(-170,170),dy:randomInt(-85,85),wave:randomInt(-25,25),spin:randomInt(-6,6)/10});
  }
  if(tiles.length)tiles[0].spin=0.9;
  draw(0);
  slider.addEventListener('input',()=>{
   if(verified||checking)return;
   clearTimeout(idleTimer);draw(Number(slider.value));
   message.textContent='停留 1 秒后自动验证…';
   idleTimer=setTimeout(()=>{if(host.isConnected)check();},1000);
  });
  host.querySelector('#new-puzzle').addEventListener('click',create);slider.focus();
 }
 function draw(value){
  slider.style.setProperty('--slider-progress',value+'%');
  slider.style.setProperty('--slider-fill',value===target?'#229a67':'#2785e8');
  const ctx=canvas.getContext('2d');ctx.clearRect(0,0,560,280);ctx.fillStyle='#151d2d';ctx.fillRect(0,0,560,280);
  ctx.fillStyle='#c8d7eb';ctx.font='12px system-ui';ctx.fillText('移动碎片 · 拼出完整字母',18,22);
  const delta=(value-target)/100;
  for(const tile of tiles){ctx.save();ctx.translate(tile.x+10+delta*tile.dx+Math.sin(delta*5)*tile.wave,tile.y+10+delta*tile.dy);ctx.rotate(delta*tile.spin);ctx.drawImage(source,tile.x,tile.y,20,20,-10,-10,20,20);ctx.restore();}
 }
 async function check(){
  if(loading||verified||checking||!host.isConnected)return;
  checking=true;clearTimeout(idleTimer);slider.disabled=true;
  host.querySelector('#new-puzzle').disabled=true;
  if(Number(slider.value)!==target){
   message.textContent='未能拼合，正在更换图片…';
   idleTimer=setTimeout(()=>{if(host.isConnected)create();},650);return;
  }
  const wrap=host.querySelector('.puzzle-slider-wrap');wrap.classList.add('is-verified');
  host.querySelector('.puzzle-success-label').hidden=false;
  verified=true;slider.disabled=true;message.textContent='验证成功，正在加载参考答案…';loading=true;
  try{
   const response=await fetch(task.answer);if(!response.ok)throw Error('参考答案加载失败，请重试');const answer=await response.json();if(!host.isConnected)return;
   result.hidden=false;result.replaceChildren();const heading=document.createElement('h3');heading.textContent=answer.title;result.append(heading);
   const scope=document.createElement('p');scope.textContent=answer.scope;result.append(scope);
   const list=document.createElement('ul');answer.explanations.forEach(item=>{const li=document.createElement('li');li.textContent=item.token+' → '+item.answer+'（'+item.location+'）';list.append(li);});result.append(list);
   answer.files.forEach(file=>{const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre'),code=document.createElement('code');summary.textContent=file.path;code.textContent=file.content;pre.append(code);details.append(summary,pre);result.append(details);});
   message.textContent='验证成功，参考代码已展开。';open.disabled=true;open.textContent='参考答案已解锁';
  }catch(error){verified=false;checking=false;slider.disabled=false;host.querySelector('#new-puzzle').disabled=false;host.querySelector('.puzzle-slider-wrap').classList.remove('is-verified');host.querySelector('.puzzle-success-label').hidden=true;message.textContent=error.message+'；请调整滑块后重试。';}finally{loading=false;}
 }
 open.addEventListener('click',()=>{if(!loading)create();});
}
