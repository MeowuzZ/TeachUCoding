"""Build per-lesson downloadable local projects and separately fetched references."""
import json,re,zipfile,collections
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'public';templates=root/'project-templates';out=p/'homework';out.mkdir(exist_ok=True)
data=json.loads((p/'academy/assignments.json').read_text(encoding='utf-8'));cat=json.loads((p/'engineering/catalog.json').read_text(encoding='utf-8'));byid={l['id']:l for l in cat['lessons']};teaching=json.loads((p/'engineering/section-learning.json').read_text(encoding='utf-8'));method=json.loads((root/'course-data.json').read_text(encoding='utf-8'));methods={l['id']:l for l in method['lessons']}
scenarios=[
('library','社区共享书屋','图书借阅从登记、借出到归还；逾期与库存为扩展模块',['文学','技术','儿童'],['待借出','借阅中','已归还'],'借阅数量','登记共享图书','借阅记录与归还流程','预约排队与逾期提醒'),
('budget','合租家庭账本','室友登记生活支出，核对账单并完成结算',['餐饮','交通','水电'],['待核对','已确认','已结算'],'金额（分）','登记生活支出','分类统计与核对','按成员分摊与月度预算'),
('repair','社区报修服务台','居民登记故障，物业接单并记录处理结果',['水电','家电','公共设施'],['待受理','处理中','已完成'],'预计工时（小时）','登记故障工单','受理与处理记录','优先级分派、超时提醒与回访'),
('event','周末活动报名站','社区活动收集报名并完成签到',['运动','读书','手工'],['待确认','已报名','已签到'],'参加人数','登记报名信息','确认与签到','名额锁定、候补队列与取消退款模拟'),
('food','社区团购配送台','邻里团购收集需求、准备商品并交付',['蔬果','早餐','日用品'],['待备货','配送中','已送达'],'商品数量','登记团购单','备货与配送状态','库存扣减、分批配送与缺货补偿'),
('petcare','邻里宠物照护预约','居民登记照护请求，确认并完成服务',['喂养','遛宠','清洁'],['待确认','服务中','已完成'],'服务时长（小时）','登记照护请求','确认照护与完成记录','时段冲突检测与服务者排班'),
('travel','家庭旅行筹备板','整理旅行物资和开销，核实并准备就绪',['交通','住宿','物资'],['待核实','已确认','已准备'],'预算（分）','登记出行事项','确认与准备状态','多人协作、预算上限与离线行程'),
('study','学习资料研习站','登记学习资料，组织研读并保留复盘',['编程','设计','语言'],['待阅读','研读中','已复盘'],'计划时长（分钟）','登记学习资料','研读与复盘','全文检索、来源校验与受控 AI 摘要'),
('equipment','校园器材借用中心','社团借用器材，确认领用与归还',['摄影','运动','音响'],['待领用','使用中','已归还'],'借用数量','登记器材借用','领用与归还','库存台账、并发预约与损坏处理'),
('volunteer','社区志愿服务中心','居民报名志愿任务，确认参加并核对工时',['助老','环保','活动'],['待确认','服务中','已核对'],'服务工时','登记志愿服务','服务执行与核对','人员排班、工时审核与证书导出'),
('garden','社区花园养护台','登记养护事项并追踪执行情况',['浇灌','修剪','补种'],['待安排','养护中','已完成'],'材料数量','登记养护任务','安排与完成记录','天气策略、物资消耗与轮值提醒'),
('market','校园闲置交换集市','登记闲置物品并追踪交换交接',['书籍','数码','生活'],['待交换','已约定','已交接'],'物品数量','登记闲置物品','约定与交接','匹配规则、失约处理与评价申诉')]
manifest={};counts=collections.Counter()
for index,a in enumerate(data['lessons'].values()):
 course=a['course'];lid=a['lessonId'];chapter=a['chapter'];title=a['title'].split(' · ')[0]
 chapter_index=next(i for i,c in enumerate(data['chapters']) if c['course']==course and lid in c['lessonIds'])
 scenario=scenarios[chapter_index%len(scenarios)];sid,project,desc,categories,states,unit,*milestones=scenario
 stack='web' if re.search(r'HTML|CSS|JavaScript|TypeScript|Vue',chapter,re.I) else 'python' if course=='method' or re.search(r'Python|AI |Agent|大模型',chapter,re.I) else 'java'
 config=dict(id=sid,title=project,description=desc,categories=categories,states=states,unit=unit,seed=[[project+'示例',categories[0],2,states[0],'模拟数据：请替换为自建测试样例']])
 config_text=json.dumps(config,ensure_ascii=False,indent=2)
 files={'scenario.json':config_text}
 if stack=='web':
  files.update({f:(templates/f).read_text(encoding='utf-8') for f in ['index.html','app.js','style.css']});files['scenario.js']='window.PROJECT_CONFIG = '+config_text+';\n';files['index.html']=files['index.html'].replace('<script src="app.js"','<script src="scenario.js"></script><script src="app.js"')
  run='直接用浏览器打开 index.html。此版本使用 localStorage；若浏览器限制 file:// 存储，请用编辑器的本地静态服务器打开。';main='app.js'
 elif stack=='python':
  files.update({f:(templates/f).read_text(encoding='utf-8') for f in ['index.html','app.js','style.css','service.py','test_service.py']});run='需要 Python 3.10+。在本目录运行 python3 service.py，然后打开 http://127.0.0.1:8088 。测试：python3 -m unittest -v test_service.py。Windows 可将 python3 替换为 py -3。';main='service.py'
 else:
  files['Main.java']=(templates/'Main.java').read_text(encoding='utf-8');files['scenario.properties']='title='+project+'\ncategories='+','.join(categories)+'\nstates='+','.join(states)+'\n';run='需要 JDK 17+。在本目录执行 javac -encoding UTF-8 Main.java，再执行 java Main。自动检查：java Main --test。命令示例：add 示例|'+categories[0]+'|2|模拟数据，然后执行 list、next 1、stats、export。';main='Main.java'
 # Select the actual layer taught by this lesson for beginner blanks.
 if stack=='web' and re.search(r'HTML|标签|表单|表格|语义',chapter+' '+title,re.I):
  main='index.html'
 elif stack=='web' and re.search(r'CSS|样式|布局|选择器|盒模型',chapter+' '+title,re.I):
  main='style.css'
 # Choose blanks in actual project code; remaining architecture is supplied.
 choices={'web':['filter','addEventListener','textContent','JSON.stringify','Number.isInteger','reduce','querySelector','createElement'], 'python':['sqlite3.connect','json.loads','ValueError','int','str','execute','return','if'], 'java':['ArrayList','IllegalArgumentException','Long.parseLong','StandardCharsets.UTF_8','return','new','static','String']}[stack]
 if main=='index.html':choices=['charset','viewport','label','required','form','input','section','button']
 if main=='style.css':choices=['display','grid','padding','border','margin','color','flex','font']
 # Prefer keywords explicitly present in the lesson's content.
 context=title+' '+a['focus'];selected=sorted(choices,key=lambda word:(word.lower() not in context.lower(),choices.index(word)))
 starter=dict(files);blanks=[];code=starter[main]
 for word in selected:
  pattern=r'(?<![\w])'+re.escape(word)+r'(?![\w])';match=re.search(pattern,code)
  if match:
   token='__TODO_'+str(len(blanks)+1)+'__';line=code[:match.start()].count('\n')+1;code=code[:match.start()]+token+code[match.end():];blanks.append(dict(token=token,answer=word,line=line))
  if len(blanks)>=3:break
 starter[main]=code
 foundation='关键词填空：已提供项目大部分实现，只补三个关键位置。' if course=='method' or index<300 else '关键词填空 + 独立扩展：先补齐三个位置，再按本节知识实现一个业务变式。'
 learning=teaching.get(lid,{}) if course=='engineering' else methods[lid]
 bodyfile=p/'engineering'/(lid+'.json')
 # Preserve real lesson specimens separately rather than presenting them as integrated functionality.
 if bodyfile.exists():
  blocks=json.loads(bodyfile.read_text(encoding='utf-8')).get('blocks',[])
  excerpts='\n\n'.join('```'+str(b.get('language','text'))+'\n'+str(b.get('code',''))+'\n```' for b in blocks[:3])
 else:excerpts=learning.get('body','')+'\n\n'+learning.get('practice','')
 focus=a['focus'];req='\n'.join('- '+r for r in a['requirements'][2:])
 tests=f'''# 验收清单\n\n- [ ] 启动后能查看模拟记录。\n- [ ] 新建「{project}测试」，分类选「{categories[0]}」，数值填 2；刷新或重启后仍在。\n- [ ] 空名称和负数被拒绝；导出文件中没有这次非法记录。\n- [ ] 逐次推进「{' → '.join(states)}」，终态不能重复推进。\n- [ ] 搜索独有关键词仅返回匹配项（Java 使用 list 关键词）。\n- [ ] 导出 CSV，核对中文、数量与状态。\n- [ ] 根据本节「{title}」增加一个新测试，写出预期与实际结果。\n- [ ] Web 项目另测分类／状态筛选；Java 项目执行 --test；Python 项目执行 unittest。\n\n教学原型不包含真实登录、支付、短信或在线 AI 调用。\n'''
 brief=f'''# {project} · {title}\n\n## 真实场景\n{desc}。本项目服务居民、执行人员与管理员。禁止录入真实隐私数据。\n\n## 当前交付范围\n这是大型项目的可运行基础切片：登记、分类、检索、状态推进、统计、持久化、CSV 导出。\n{foundation}\n\n## 本节知识与项目的连接\n{focus}\n先阅读教材对应段落，再找到 {main} 中的三个 __TODO_n__ 标记。每个空只替换一个关键字或表达式，代码架构与其他功能已提供。\n本节概念如果不直接涉及程序语法，请先运行已有代码，观察对应的输入—处理—输出，并用本节知识解释设计；尚未学过的语法无需独立编写。\n\n## 运行方法\n{run}\n\n## 填空提示\n'''+ '\n'.join(f'- {b["token"]}：在 {main} 第 {b["line"]} 行附近，阅读上下文和教材，补全该位置的职责；可选词见 关键词词库.md。' for b in blanks)+f'''\n\n## 本节差异化项目证据 · {a['type']}\n{req}\n所有图表、实验和说明必须围绕当前代码项目。\n\n## 本章迭代与大型项目路线\n1. {milestones[0]}：用当前切片完成输入校验和数据保存。\n2. {milestones[1]}：完善检索、状态机、失败路径与测试。\n3. {milestones[2]}：拆分模块，设计关联数据、角色权限、并发与恢复策略。\n4. 增加接口、数据库迁移和多用户身份；进行集成测试，再考虑发布。\n5. 提交需求说明、架构图、源码、测试报告、演示与运行手册。\n\n路线第 3—5 步是后续扩展目标，当前答案只覆盖基础切片和本次填空，不声称已实现大型生产系统。\n\n## 提交\n压缩修改后的源码、验收记录和本节证据文件。不要提交数据库中的真实信息、虚拟环境或构建缓存。\n'''
 starter.update({'README.md':brief,'验收清单.md':tests,'本节教材示例.md':'# 教材参考\n\n以下为本节原文代码或材料，不宣称已接入项目。请分析其与项目的关系。\n\n'+excerpts,'关键词词库.md':'# 候选词（含干扰项）\n\n'+', '.join(sorted(set(choices+['continue','null','False','undefined']))),'实践记录.md':'# 本地作业记录\n\n运行环境：\n\n三个填空的职责解释：\n\n本节知识如何用于项目：\n\n实际验收结果：\n\n失败案例与修订：\n\n扩展模块：\n'})
 slug=course+'-'+lid
 with zipfile.ZipFile(out/(slug+'.zip'),'w',zipfile.ZIP_DEFLATED) as z:
  for path,content in starter.items():z.writestr(path,content)
 answer={'title':project+' · 标准参考实现','scope':'覆盖项目基础切片及本次填空；扩展路线需另行实现。','explanations':[dict(token=b['token'],answer=b['answer'],location=main+':'+str(b['line'])) for b in blanks],'files':[dict(path=path,content=text) for path,text in files.items()]}
 (out/(slug+'-answer.json')).write_text(json.dumps(answer,ensure_ascii=False), encoding='utf-8')
 manifest[a['id']]=dict(project=project,scenario=sid,stack=stack,mode=foundation,focus=focus,milestones=milestones,title=title,type=a['type'],download='homework/'+slug+'.zip',answer='homework/'+slug+'-answer.json',requirements=['下载并解压作业包，阅读 README 与本节教材示例。','补齐三个关键词，保留大部分已提供的代码。','在本地运行项目，完成验收清单。',f'围绕项目提交「{a["type"]}」，说明本节知识的实际用途。'],checks=['基础项目可启动，填空职责解释正确','合法与非法输入、状态终点和保存恢复均有验证证据','本节证据与代码行为一致'],run=run)
 counts[stack]+=1
(p/'academy/project-homework.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2), encoding='utf-8')
(root/'curriculum/项目作业交付说明.md').write_text('# 本地项目作业\n\n'+f'覆盖 {len(manifest)} 节，{len(scenarios)} 类生活场景，24 种项目证据形式。\n\n'+ '\n'.join('- '+s[1]+'：'+s[2] for s in scenarios)+'\n\n基础包采用 Web 本地存储、Java 命令行业务引擎或 Python/SQLite 服务三种实现。框架课程可在基础切片上迁移实现，不将标准库实现称为 Spring/Vue 完整系统。标准答案覆盖基础切片；大型项目扩展需按各章知识继续实现。\n', encoding='utf-8')
assert len(manifest)==1111
print('Built',len(manifest),'packages;',dict(counts))
