'use strict';
const $ = selector => document.querySelector(selector);
let config, records = [];
const offline = location.protocol === 'file:';
async function api(path, data) {
  const response = await fetch(path, data ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)} : {});
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || '请求失败');
  return value;
}
function persist() { localStorage.setItem('life-project:'+config.id, JSON.stringify(records)); }
function message(text) { $('#message').textContent = text; }
function text(tag, value) { const node = document.createElement(tag); node.textContent = value; return node; }
function render() {
  const query = $('#search').value.trim().toLowerCase();
  const state = $('#status-filter').value;
  const visible = records.filter(row => (!state || row.status === state) && [row.title,row.category,row.note].join(' ').toLowerCase().includes(query));
  $('#summary').replaceChildren(text('strong', '总记录 '+records.length), text('span', ' 待处理 '+records.filter(r=>r.status!==config.states.at(-1)).length), text('span', ' 数值合计 '+records.reduce((sum,r)=>sum+r.amount,0)));
  $('#records').replaceChildren();
  if (!visible.length) $('#records').append(text('p', '没有符合条件的记录'));
  visible.forEach(row => {
    const card = document.createElement('article');
    card.append(text('h3',row.title),text('p',row.category+' · '+row.status+' · '+row.amount),text('p',row.note));
    const button = text('button', row.status===config.states.at(-1)?'已完成':'推进到下一状态');
    button.disabled = row.status===config.states.at(-1);
    button.addEventListener('click', async () => {
      button.disabled = true;
      try {
        if (offline) {row.status=config.states[config.states.indexOf(row.status)+1];persist();}
        else {await api('/api/advance/'+row.id,{});records=await api('/api/records');}
        render();message('状态已更新');
      } catch(error) {message(error.message);button.disabled=false;}
    });
    card.append(button);$('#records').append(card);
  });
}
$('#record-form').addEventListener('submit',async event=>{
  event.preventDefault();
  const form = event.currentTarget, values = new FormData(form);
  const record = {title:values.get('title').trim(),category:values.get('category'),amount:Number(values.get('amount')),note:values.get('note')};
  if (!record.title || !Number.isInteger(record.amount) || record.amount<0 || record.amount>100000000) return message('请检查名称和数值');
  const submit = form.querySelector('button');submit.disabled=true;
  try {
    if(offline){records.unshift({...record,id:Date.now(),status:config.states[0]});persist();}
    else {await api('/api/records',record);records=await api('/api/records');}
    form.reset();render();message('保存成功');
  } catch(error){message(error.message);}finally{submit.disabled=false;}
});
$('#search').addEventListener('input',render);$('#status-filter').addEventListener('change',render);
$('#export').addEventListener('click',()=>{
  if(!offline){location.href='/api/export';return;}
  const cell = value => '"'+String(value).replace(/^[=+@-]/,"'$&").replaceAll('"','""')+'"';
  const csv = '\ufeff'+[['编号','名称','分类','数量／金额','状态','说明'],...records.map(r=>[r.id,r.title,r.category,r.amount,r.status,r.note])].map(row=>row.map(cell).join(',')).join('\r\n');
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=config.id+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
(async()=>{try{
  config = offline ? window.PROJECT_CONFIG : await api('/api/config');
  if(!config)throw new Error('请使用说明中的启动方式');
  $('#project-title').textContent=config.title;$('#project-description').textContent=config.description;document.title=config.title;
  config.categories.forEach(value=>{const option=text('option',value);option.value=value;$('#category').append(option);});
  config.states.forEach(value=>{const option=text('option',value);option.value=value;$('#status-filter').append(option);});
  if(offline){const saved=localStorage.getItem('life-project:'+config.id);records=saved?JSON.parse(saved):config.seed.map((r,i)=>({id:i+1,title:r[0],category:r[1],amount:r[2],status:r[3],note:r[4]}));}
  else records=await api('/api/records');
  render();
}catch(error){message(error.message);}})();
