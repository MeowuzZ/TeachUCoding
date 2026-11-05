import * as Store from './academy-store.js';
import {$,esc,toast} from './academy-utils.js';
import {openDialog} from './academy-motion.js';
export function installAccount(){
 const button=$('#account-trigger'),panel=$('#account-panel'),dialog=$('#account-dialog');
 let register=false;
 function draw(){
  button.textContent=Store.account?'账号 · '+Store.cloudStatus:'登录 / 注册';button.title=Store.cloudError||Store.cloudStatus;
  panel.innerHTML=Store.account?`<h2>${esc(Store.account.name)}</h2><p>${esc(Store.account.email)}</p><p>${esc(Store.cloudStatus)}</p><div class="account-actions"><button class="button" id="retry-sync">重新同步</button><button class="button" id="import-device">导入本机记录</button><button class="button" id="account-signout">退出登录</button></div><p>进度、笔记和个人资料按当前账号保存。代码项目在本地完成。</p>`:`<h2>${register?'创建学习账号':'登录后接着学'}</h2><form id="native-account-form">${register?'<label>称呼<input name="name" maxlength="30" autocomplete="nickname"></label>':''}<label>邮箱<input type="email" name="email" required autocomplete="email" maxlength="254"></label><label>密码<input type="password" name="password" required minlength="10" maxlength="256" autocomplete="${register?'new-password':'current-password'}"></label><p>密码至少 10 位。此邮箱仅作为登录名，不发送验证邮件。</p><button class="button primary" type="submit">${register?'注册并登录':'登录'}</button><button class="button" type="button" id="switch-account-form">${register?'已有账号，去登录':'没有账号，去注册'}</button><p id="account-error" role="status"></p></form><p>不登录也可使用课程，学习记录保存在当前浏览器。账号同步需要使用项目自带服务器。</p>`;
 }
 button.addEventListener('click',()=>{draw();openDialog(dialog)});
 document.addEventListener('cloud-status',()=>{if(Store.account)draw();else button.title=Store.cloudError||Store.cloudStatus;});
 panel.addEventListener('submit',async event=>{
  if(event.target.id!=='native-account-form')return;event.preventDefault();
  const form=event.target,submit=form.querySelector('[type=submit]');submit.disabled=true;
  try{const payload=Object.fromEntries(new FormData(form));const response=await fetch('/api/auth/'+(register?'register':'login'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await response.json();if(!response.ok)throw Error(data.error||'登录失败');location.reload();}
  catch(error){panel.querySelector('#account-error').textContent=error.message;submit.disabled=false;}
 });
 panel.addEventListener('click',async event=>{
  const id=event.target.id;
  if(id==='switch-account-form'){register=!register;draw();}
  if(id==='retry-sync'){await Store.retryCloud();draw();}
  if(id==='import-device'){await Store.importDeviceRecords();toast('记录已导入');location.reload();}
  if(id==='account-signout'){await Store.flushCloud();if(['尚未同步','同步不可用'].includes(Store.cloudStatus)){toast('请同步或导出记录后再退出');return;}const response=await fetch('/api/auth/logout',{method:'POST'});if(response.ok)location.reload();else toast('退出失败，请重试');}
 });
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')Store.flushCloud();});window.addEventListener('online',()=>Store.retryCloud());draw();
}
