import assert from 'node:assert/strict';
import fs from 'node:fs';
import {returnDestination,homePage,homeSections} from '../public/academy-home.js';
import {syllabusPage,curriculumOutline} from '../public/academy-curriculum.js';
const c=JSON.parse(fs.readFileSync(new URL('../public/curriculum/curriculum.json',import.meta.url)));
const lookup=(course,id)=>course==='method'&&id==='L07';
assert.deepEqual(returnDestination('#course/method/L07/practice',c,lookup),{href:'#course/method/L07/practice',label:'返回上次学习位置'});
assert.equal(returnDestination('#syllabus/engineering/B39',c,lookup).href,'#syllabus/engineering/B39');
assert.equal(returnDestination('#syllabus/method',c,lookup).href,'#syllabus/method');
for(const invalid of [null,{},'https://example.com','#home','#courses','#syllabus/method/A99','#syllabus/unknown','#course/method/L99/learn','#course/method/L07/unknown','#course/method/L07/practice/extra','javascript:alert(1)'])assert.equal(returnDestination(invalid,c,lookup),null);
const fresh=homePage(c,null),returning=homePage(c,returnDestination('#syllabus/engineering/B39',c,lookup));
assert(fresh.includes('href="#courses"'));
assert(!fresh.includes('>继续查看课时大纲'));
assert(returning.includes('href="#syllabus/engineering/B39"'));
for(const section of homeSections)assert(fresh.includes(`id="home-${section}"`));
for(const [key,course] of Object.entries(c.courses)){
 const plans=course.modules.flatMap(m=>m.lessons);
 assert.equal(plans.length,course.lessonCount);
 assert.equal(plans.length*course.minutes/60+course.modules.length*course.projectHours,course.totalHours);
 const overview=syllabusPage(c,key);
 for(let i=0;i<plans.length;i++){
  const l=plans[i],page=syllabusPage(c,key,l.id);
  assert(overview.includes(`#syllabus/${key}/${l.id}`));
  assert(page.includes(l.practice)&&page.includes(l.evidence));
  assert(curriculumOutline(c,key,l.id).tree.includes(`href="#syllabus/${key}/${l.id}" aria-current="page"`));
  assert.deepEqual(l.dependsOn,i?[plans[i-1].id]:[]);
 }
}
assert(!syllabusPage(c,'method','A99').includes('undefined'));
const source=fs.readFileSync(new URL('../public/academy.js',import.meta.url),'utf8');
assert(source.indexOf('await Workspace.leave()')<source.indexOf('route=parseRoute()'));
assert(source.includes("if(['lesson','syllabus'].includes(route.page))"));
const index=fs.readFileSync(new URL('../public/index.html',import.meta.url),'utf8');
assert(index.includes('class="brand" href="#home"'));
for(const [,asset] of index.matchAll(/(?:src|href)="([^"#]+\.(?:css|js|svg))"/g))assert(fs.existsSync(new URL('../public/'+asset,import.meta.url)));
console.log('PASS: 72 curriculum routes, prerequisite chain, lesson evidence, valid resume targets, invalid target rejection, homepage sections and local assets');
