"""Audit every source lesson and build reproducible, content-linked assignments."""
import json,re,collections
from pathlib import Path
root=Path(__file__).resolve().parents[1]; p=root/'public'
recipes=[
('概念关系图','画出至少五个概念节点与带动词的连线；标出一条易混淆关系','关系图及逐条说明','随机移去一个节点，解释哪些关系会失效'),
('执行轨迹表','选一个具体输入，逐步列出处理动作、状态变化和输出','至少六行轨迹表','用另一个输入重走流程并指出首个分歧'),
('错误诊断单','构造一个与本节有关的错误；写出两个原因假设并分别验证','复现步骤、证据与修复前后对照','验证修复有效且原正常场景仍成立'),
('双方案对照实验','针对同一目标提出两种做法，固定其他条件比较结果','控制变量表与方案取舍结论','至少比较正确性、成本和适用边界'),
('边界案例矩阵','列出正常、空值、极值、非法输入和重复操作的预期行为','至少五类案例矩阵','逐项记录实际观察；不能运行的案例标为待验证'),
('反例挑战','写出三条关于本节的判断，为其中一条寻找反例','判断、反例和修订后的规则','解释反例改变了哪个前提'),
('微课讲解','面向初学者制作三分钟讲解，包含具体例子与常见误区','讲稿或录音及示例','请一位学习者复述；无人参与时以自测问题代替并注明'),
('操作流程图','画出从输入到结果的流程，至少含一个判断和一个失败出口','流程图与两条走查路径','沿正常路径和失败路径分别走查'),
('证据卡片集','摘录本节三个关键结论，分别关联原文依据和实际例子','三张结论—依据—例子卡','区分原文结论、个人推断和待验证信息'),
('验收契约','把本节能力写成前置条件、操作、可观察结果','至少四条 Given/When/Then 验收条目','每条都有明确的通过和失败判定'),
('最小原型','只用本节核心知识做一个可展示的最小模型或可运行例子','原型、使用步骤和结果','移除一项非必要内容后核心目标仍能完成'),
('代码或规则评审','审阅课文示例或自写规则，按严重程度标记三个问题','带位置的评审记录及修订稿','每条建议均提供理由和验证步骤'),
('概念分类卡','将八个实例按本节概念分类，设计一个容易误分的实例','分类卡与分类依据','说明模糊实例为何归入该类'),
('变更影响地图','假设本节一个关键条件改变，追踪受影响的步骤与产物','影响地图与回归检查清单','至少识别一个间接影响和一个无需修改部分'),
('故障复盘','设计一个符合本节机制的失败案例，区分现象、原因与补救','时间线、原因树和预防措施','明确标注模拟案例；每个原因都有证据或验证计划'),
('检索速查手册','把本节整理成按问题查找的五条操作指引','一页速查表与示例','用一个新问题检验能否快速定位到指引'),
('情境角色扮演','分别从使用者、实现者和验收者视角讨论同一案例','三方对话脚本及冲突解决方案','每个角色提出不同约束并说明最终取舍'),
('盲测预测','先遮住示例结论，根据本节知识预测三种情况的结果再核对','带时间顺序的预测与实际结果表','解释至少一个预测正确或错误的机制'),
('约束排序','列出实现本节目标的六项约束，用重要性和代价排序','优先级矩阵与取舍说明','给定时间减半时重新排序并说明变化'),
('数据字典','为本节案例定义对象、属性、取值与校验规则','至少六项字段或概念定义表','给出一个合法实例与两个不合法实例'),
('迁移挑战','把本节方法迁移到与教材不同的使用场景','旧新场景映射和新实例','指出可复用部分与必须重新验证的假设'),
('苏格拉底问答','设计五个由浅入深的问题，用追问检验理解','问答链与参考答案','至少一个问题要求解释原因而不是复述定义'),
('可视化故事板','用六格呈现本节案例的触发、操作、变化与结果','六格故事板及文字标注','必须包含一次失败和恢复过程'),
('学习实验日志','提出一个关于本节的可检验假设，设计并完成一次小实验','假设、过程、观察与修订日志','原始观察与个人解释分开记录')]
cat=json.loads((p/'engineering/catalog.json').read_text(encoding='utf-8')); teaching=json.loads((p/'engineering/section-learning.json').read_text(encoding='utf-8')); method=json.loads((root/'course-data.json').read_text(encoding='utf-8'))
supp=lambda l:bool(re.match(r'^(作业|AI助学|助学)$',re.sub(r'^\d+(?:\.\d+)*\s*[.、:]?\s*','',l['title'].replace('\\','')).replace(' ','')))
byid={l['id']:l for l in cat['lessons']}; output={}; audit=[]; chapters=[]; used={}
preferences=[('安装|环境|配置|部署', [15,7,14,9]),('错误|异常|调试|报错',[2,14,4,17]),('测试|校验|安全|权限',[4,9,5,11]),('数据|数据库|SQL|对象|类型',[19,12,1,4]),('流程|请求|网络|线程|异步',[7,1,0,22]),('样式|布局|CSS|界面|原型',[10,3,22,11]),('需求|访谈|用户|问题',[16,8,18,23]),('AI|模型|提示|检索',[17,5,3,8]),('函数|方法|循环|变量|语法',[1,17,11,10]),('版本|Git|交付|迁移',[13,20,15,14])]

def build(course,l,chapter,index,context,task):
 key=(course,chapter); seen=used.setdefault(key,set())
 candidates=[]
 for pattern,choices in preferences:
  if re.search(pattern,l['title'],re.I):candidates.extend(choices)
 candidates += [(index+i)%len(recipes) for i in range(len(recipes))]
 choice=next((i for i in candidates if i not in seen),candidates[0]);seen.add(choice)
 name,action,deliver,check=recipes[choice]
 focus=re.sub(r'\s+',' ',context).strip()[:180] or l['title']
 return dict(id=course+':'+l['id'],course=course,lessonId=l['id'],chapter=chapter,title=l['title']+' · '+name,type=name,focus=focus,task=f'围绕「{l["title"]}」，以本节具体案例完成{name}。',requirements=[f'内容锚点：{focus}',f'先完成本节基础任务：{task}',action,f'提交物：{deliver}；明确标注资料来源和模拟数据。'],checks=[check,'成果能解释本节知识与所选案例的关系','保留独立尝试与一次修订的证据'],deliverable=deliver)
for ch in cat['chapters']:
 lessons=[byid[i] for i in ch['lessons'] if not supp(byid[i])]
 for n,l in enumerate(lessons):
  f=p/'engineering'/ (l['id']+'.json');body=json.loads(f.read_text(encoding='utf-8')) if f.exists() else {};t=teaching.get(l['id'],{});context=t.get('focus') or re.sub('<[^>]+>','',body.get('body',''))[:180]
  a=build('engineering',l,ch['title'],n+ch.get('order',0),context,t.get('task','阅读本节示例并解释输入与输出'));output[a['id']]=a
  audit.append(dict(course='engineering',id=l['id'],title=l['title'],bodyPresent=bool(body.get('body')),teachingPresent=bool(t),assignmentType=a['type']))
 chapters.append(dict(course='engineering',id=ch['id'],title=ch['title'],task='整合本章各节成果，选择同一个案例串联知识；提交章节作品、依赖关系图和验收记录。',lessonIds=[l['id'] for l in lessons],checks=['逐节列出成果位置','至少演示一条正常路径与一条失败路径','记录一个跨小节问题及解决过程']))
for n,l in enumerate(method['lessons']):
 ch=next(s['title'] for s in method['stages'] if s['id']==l['stage']);a=build('method',l,ch,n,l['goal']+'；'+'、'.join(c['term'] for c in l.get('concepts',[])),l['practice']);output[a['id']]=a;audit.append(dict(course='method',id=l['id'],title=l['title'],bodyPresent=bool(l['body']),teachingPresent=bool(l['practice']),assignmentType=a['type']))
for s in method['stages']:
 chapters.append(dict(course='method',id=str(s['id']),title=s['title'],task='用本阶段各节成果交付：'+s['output'],lessonIds=[l['id'] for l in method['lessons'] if l['stage']==s['id']],checks=['列出各节成果与阶段目标的对应关系','展示真实结果并标出未完成部分','完成一次复测并保留证据']))
result=dict(types=[dict(name=r[0],action=r[1],deliverable=r[2],check=r[3]) for r in recipes],lessons=output,chapters=chapters)
(p/'academy/assignments.json').write_text(json.dumps(result,ensure_ascii=False,indent=2), encoding='utf-8')
report=dict(lessonCount=len(audit),chapterCount=len(chapters),typeCount=len(recipes),missingBody=[a for a in audit if not a['bodyPresent']],missingTeaching=[a for a in audit if not a['teachingPresent']],typeDistribution=dict(collections.Counter(a['assignmentType'] for a in audit)),lessons=audit)
(root/'curriculum/作业覆盖核查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2), encoding='utf-8')
lines=['# 全课程差异化作业设计','',f'覆盖 {len(chapters)} 个章节/阶段、{len(audit)} 个正式小节，使用 {len(recipes)} 种作业形式。','核查为正文存在性、原有练习与覆盖完整性检查；专业准确性仍需教师逐项复核。','']
for ch in chapters:
 lines += ['## '+ch['title'],'',ch['task'],'']
 for lid in ch['lessonIds']:
  a=output[ch['course']+':'+lid];lines += ['### '+a['title'],'',a['task'],'']+['- '+x for x in a['requirements']]+['','验收：'+'；'.join(a['checks']),'']
(root/'curriculum/全课程差异化作业设计.md').write_text('\n'.join(lines), encoding='utf-8')
assert len(output)==len(audit) and len(set(a['type'] for a in output.values()))>=20
print(json.dumps({k:v for k,v in report.items() if k!='lessons'},ensure_ascii=False,indent=2))
