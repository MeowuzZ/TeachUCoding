export const isSupplemental=l=>/^(作业|AI助学|助学)$/.test(l.title.replace(/\\/g,'').replace(/^\d+(?:\.\d+)*\s*[.、:]?\s*/,'').replace(/\s/g,''));
export function integrateCatalog(source){
 const byId=new Map(source.lessons.map(l=>[l.id,l])),redirects={};
 const chapters=source.chapters.map(ch=>{const ids=ch.lessons.filter(id=>!isSupplemental(byId.get(id)));for(const id of ch.lessons.filter(id=>isSupplemental(byId.get(id))))redirects[id]=ch.lessons.slice(0,ch.lessons.indexOf(id)).reverse().find(i=>ids.includes(i))||ids[0];return {...ch,lessons:ids};});
 return {...source,lessons:source.lessons.filter(l=>!isSupplemental(l)),chapters,integrationRedirects:redirects,integratedLessons:source.lessons.filter(isSupplemental)};
}
