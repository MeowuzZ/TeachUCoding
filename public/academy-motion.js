const easing='cubic-bezier(.22,1,.36,1)';
let pageAnimation,installed=false;
const disclosures=new WeakMap(),dialogs=new WeakMap();
export const reducedMotion=()=>typeof window!=='undefined'&&window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
export function cancelPageMotion(){pageAnimation?.cancel();pageAnimation=null;}
async function play(element,frames,duration){
 if(!element?.animate||reducedMotion())return;
 const animation=element.animate(frames,{duration,easing});
 pageAnimation=animation;
 try{await animation.finished}catch{/* Navigation can supersede an in-flight animation. */}
 if(pageAnimation===animation)pageAnimation=null;
}
function pageEntrance(page){
 const step=location.hash.split('/').at(-1);
 const type=page==='lesson'?step:page;
 const starts={home:{opacity:0,transform:'scale(1.025)'},courses:{opacity:0,transform:'translateX(30px)'},syllabus:{opacity:0,transform:'translateY(22px)',clipPath:'inset(0 0 12% 0)'},learn:{opacity:0,transform:'translateY(20px)'},practice:{opacity:0,transform:'translateX(-32px)'},project:{opacity:0,transform:'scale(.97)'},records:{opacity:0,transform:'translateY(-25px)'},materials:{opacity:0,transform:'translateX(34px) scale(.985)'},material:{opacity:0,clipPath:'inset(0 10% 0 0)'}};
 return [starts[type]||{opacity:0},{opacity:1,transform:'none',clipPath:'inset(0 0 0 0)'}];
}
export async function swapPage(element,update,isCurrent=()=>true){
 cancelPageMotion();
 if(!isCurrent())return false;
 element.inert=true;
 element.setAttribute('aria-busy','true');
 try{
  if(element.dataset.ready)await play(element,[{opacity:1},{opacity:0}],130);
  if(!isCurrent())return false;
  // Keep the content hidden while asynchronous workbench initialization finishes.
  element.style.opacity='0';
  await update();
  element.dataset.ready='true';
  if(!isCurrent())return false;
  element.style.opacity='';
  element.inert=false;
  await play(element,pageEntrance(element.dataset.page),460);
  return isCurrent();
 }finally{element.style.opacity='';element.inert=false;element.removeAttribute('aria-busy');}
}
export function scrollHome(section){
 const main=document.getElementById('main');if(!main)return;
 main.querySelectorAll(':scope > section,.home-final,.home-footer').forEach(panel=>{panel.hidden=false});
 document.querySelectorAll('.home-nav a,.home-deck-nav a').forEach(a=>{
  if(a.getAttribute('href')===(section?'#home/'+section:'#home'))a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');
 });
 const target=section?document.getElementById('home-'+section):main;
 requestAnimationFrame(()=>{if(target?.isConnected)target.scrollIntoView({block:'start',behavior:'instant'});});
}

export function reveal(element){
 if(!element?.animate||reducedMotion()||document.getElementById('main')?.inert)return;
 element.animate([{opacity:.35,transform:'translateY(3px)'},{opacity:1,transform:'translateY(0)'}],{duration:220,easing});
}
export function openDialog(dialog){
 dialogs.get(dialog)?.cancel();dialogs.delete(dialog);
 if(!dialog.open)dialog.showModal();
 if(reducedMotion()||!dialog.animate)return;
 const animation=dialog.animate([{opacity:0,transform:'translateY(8px) scale(.99)'},{opacity:1,transform:'none'}],{duration:240,easing});
 dialogs.set(dialog,animation);
 animation.finished.catch(()=>{}).finally(()=>{if(dialogs.get(dialog)===animation)dialogs.delete(dialog)});
}
export async function closeDialog(dialog){
 if(!dialog?.open)return;
 dialogs.get(dialog)?.cancel();dialogs.delete(dialog);
 if(reducedMotion()||!dialog.animate){dialog.close();return}
 const animation=dialog.animate([{opacity:1,transform:'none'},{opacity:0,transform:'translateY(5px)'}],{duration:140,easing});
 dialogs.set(dialog,animation);
 try{await animation.finished}catch{return}
 if(dialogs.get(dialog)===animation){dialogs.delete(dialog);dialog.close()}
}
function toggleDisclosure(details){
 const prior=disclosures.get(details),open=prior?!prior.open:!details.open;
 const from=details.getBoundingClientRect().height;
 prior?.animation.cancel();
 if(reducedMotion()||!details.animate){details.open=open;details.style.overflow='';disclosures.delete(details);return}
 details.open=open;
 const to=details.getBoundingClientRect().height;
 details.open=true;
 details.style.overflow='hidden';
 const animation=details.animate([{height:from+'px'},{height:to+'px'}],{duration:260,easing});
 const operation={open,animation};disclosures.set(details,operation);
 animation.finished.then(()=>{if(disclosures.get(details)===operation){details.open=open;details.style.overflow='';disclosures.delete(details)}}).catch(()=>{});
}
export function installMotion(){
 if(installed)return;installed=true;
 document.addEventListener('click',event=>{
  const summary=event.target.closest('summary');
  if(!summary||event.target.closest('a,button,input,select,textarea'))return;
  if(summary.parentElement?.tagName==='DETAILS'){event.preventDefault();toggleDisclosure(summary.parentElement)}
 });
 document.addEventListener('cancel',event=>{if(event.target.tagName==='DIALOG'){event.preventDefault();closeDialog(event.target)}},true);
 document.addEventListener('submit',event=>{if(event.target.getAttribute('method')==='dialog'){event.preventDefault();closeDialog(event.target.closest('dialog'))}});
}

let contentObserver;
export function installContentMotion(root){
 contentObserver?.disconnect();if(document.body.classList.contains('home-page')||reducedMotion()||!globalThis.IntersectionObserver)return;
 contentObserver=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting){if(!root.inert)e.target.animate?.([{opacity:.55,transform:'translateY(10px)'},{opacity:1,transform:'none'}],{duration:380,easing});contentObserver.unobserve(e.target)}},{threshold:.12});
 root.querySelectorAll(':scope > section,:scope > article,:scope > details,.concept-notes>div,.resume-course,.home-cycle>article,.home-outcome-grid>article').forEach(el=>contentObserver.observe(el));
}
