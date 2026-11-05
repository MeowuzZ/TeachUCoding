// Give a continuous page visible chapter boundaries and a scroll-aware location.
const chapters=[['.home-hero','intro','起点'],['#home-routes','routes','课程路线'],['#home-experience','experience','学习方式'],['#home-outcomes','outcomes','交付成果'],['#home-faq','faq','常见问题'],['.home-final','start','开始学习']];
export function chapterEntrance(key,amount,index=0,mobile=false){
 const q=Math.max(0,Math.min(1,amount*(key==='experience'?1+index*.1:1)));
 const d=index%2?-1:1,m=mobile?.5:1;
 let x=0,y=0,scale=1,rz=0,rx=0,ry=0,clip=0;
 switch(key){
  case 'intro':x=d*55*q*m;y=100*q*m;ry=d*10*q;scale=1-.1*q;break;
  case 'routes':x=d*240*q*m;y=55*q*m;rz=d*6*q;scale=1-.16*q;break;
  case 'experience':y=185*q*m;rx=-16*q;scale=1-.08*q;break;
  case 'outcomes':x=d*95*q*m;y=110*q*m;rz=(index%3-1)*9*q;scale=1-.22*q;break;
  case 'faq':x=d*110*q*m;y=20*q*m;clip=22*q;break;
  case 'start':y=65*q*m;scale=1+.18*q;break;
 }
 return {transform:`perspective(1100px) translate3d(${x.toFixed(2)}px,${y.toFixed(2)}px,0) rotateX(${rx.toFixed(2)}deg) rotateY(${ry.toFixed(2)}deg) rotateZ(${rz.toFixed(2)}deg) scale(${scale.toFixed(4)})`,clipPath:`inset(0 ${clip.toFixed(2)}% 0 0)`,blur:q*(mobile?4:7)};
}
let installed=false;
export function installHomeWayfinding(){
 if(installed)return;installed=true;
 const main=document.getElementById('main');let panels=[],items=[],frame;
 const progress=document.createElement('div');progress.className='home-scroll-progress';progress.setAttribute('role','progressbar');progress.setAttribute('aria-label','宣传页阅读进度');progress.setAttribute('aria-valuemin','0');progress.setAttribute('aria-valuemax','100');progress.innerHTML='<span></span>';document.body.append(progress);
 const preference=window.matchMedia('(prefers-reduced-motion: reduce)');
 function refresh(){
  panels=[];items=[];
  if(!document.body.classList.contains('home-page'))return;
  chapters.forEach(([selector,key,title],i)=>{
   const panel=main.querySelector(selector);if(!panel)return;
   panel.dataset.homeChapter=key;panel.dataset.chapterNumber=String(i+1).padStart(2,'0');
   if(key==='start')panel.id='home-start';
   if(!panel.querySelector(':scope > .home-chapter-marker')){
    const marker=document.createElement('div');marker.className='home-chapter-marker';
    const number=document.createElement('span');number.textContent=String(i+1).padStart(2,'0');
    const label=document.createElement('span');label.textContent=title;marker.append(number,label);panel.prepend(marker);
    if(chapters[i+1]){const next=document.createElement('p');next.className='home-next-note';next.textContent='继续向下 · '+String(i+2).padStart(2,'0')+' / '+chapters[i+1][2]+' ↓';panel.append(next);}
   }
   const heading=panel.querySelector('.home-section-heading');if(heading)heading.dataset.sectionNumber=String(i+1).padStart(2,'0');
   panels.push({panel,key});
   const nodes=panel.querySelectorAll('.home-hero-copy,.home-visual,.home-section-heading,.home-course,.home-cycle>article,.home-workspace-note,.home-outcome-grid>article,.home-faq-list,.home-final>h2,.home-final>.home-actions');
   nodes.forEach(node=>{node.classList.add('home-gather-item');node.style.transform='';node.style.opacity='';node.style.filter='';node.style.clipPath='';});
   const panelTop=panel.getBoundingClientRect().top;
   nodes.forEach((node,index)=>{const r=node.getBoundingClientRect();items.push({node,panel,key,index,offset:r.top-panelTop,height:r.height,direction:index%2?-1:1,heading:node.classList.contains('home-section-heading')});});
  });update();
 }
 function update(){
  frame=null;if(!panels.length)return;
  const maximum=document.documentElement.scrollHeight-window.innerHeight;
  const percent=maximum>0?Math.max(0,Math.min(100,window.scrollY/maximum*100)):100;
  progress.firstElementChild.style.transform=`scaleX(${percent/100})`;
  progress.setAttribute('aria-valuenow',String(Math.round(percent)));
  const header=document.querySelector('.topbar')?.offsetHeight||72;
  const focus=header+(window.innerHeight-header)*.5;
  let current=panels[0].key;
  const tops=new Map();
  for(const item of panels){const r=item.panel.getBoundingClientRect();tops.set(item.panel,r.top);if(r.top<=focus)current=item.key;}
  for(const a of document.querySelectorAll('.home-nav a')){
   const key=a.hash==='#home'?'intro':a.hash.split('/')[1];
   if(key===current)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');
  }
  for(const item of items){
   if(!item.node.isConnected)continue;
   if(preference.matches){item.node.style.transform='';item.node.style.opacity='';item.node.style.filter='';item.node.style.clipPath='';item.node.style.willChange='auto';continue;}
   const center=tops.get(item.panel)+item.offset+Math.min(item.height,window.innerHeight*.75)/2;
   const distance=center-focus;
   const clamp=value=>Math.max(0,Math.min(1,value));
   const entrance=clamp((distance-window.innerHeight*.17)/(window.innerHeight*.55));
   const departure=clamp((-distance-window.innerHeight*.17)/(window.innerHeight*.55));
   const fade=Math.max(entrance,departure);
   const mobile=window.innerWidth<740;
   // Only entrance controls geometry; departure changes opacity, never blur or direction.
   const motion=chapterEntrance(item.key,entrance,item.index,mobile);
   item.node.style.transform=motion.transform;
   item.node.style.clipPath=motion.clipPath;
   item.node.style.opacity=String((1-fade*.82).toFixed(3));
   item.node.style.filter=`blur(${motion.blur.toFixed(2)}px)`;
   item.node.style.willChange=Math.abs(distance)<window.innerHeight?'transform, opacity, filter':'auto';
  }
 }
 function schedule(){if(!frame)frame=requestAnimationFrame(update);}
 new MutationObserver(refresh).observe(main,{childList:true});
 window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',refresh,{passive:true});preference.addEventListener('change',refresh);refresh();
}
