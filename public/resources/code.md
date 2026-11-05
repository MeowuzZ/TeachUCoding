# 概念与代码练习卡

这些短例子用于解释关键机制，不是完整研习站应用。课程结构与验收以《项目任务书与评分标准》为准。

## 卡 1：同一个标题规则，两种语言

规则：去除首尾空白后非空，最多 80 个 Unicode 码点。表情组合的用户感知字符数可能与码点数不同，本课程按码点明确计数。

```javascript
function normalizeTitle(value) {
  if (typeof value !== 'string') throw new Error('标题必须是文字');
  const title = value.trim();
  if (!title) throw new Error('请填写标题');
  if (Array.from(title).length > 80) throw new Error('标题最多 80 个码点');
  return title;
}

console.assert(normalizeTitle('  接口笔记  ') === '接口笔记');
console.assert(Array.from('😀').length === 1);
```

```python
def normalize_title(value):
    if not isinstance(value, str):
        raise ValueError('标题必须是文字')
    title = value.strip()
    if not title:
        raise ValueError('请填写标题')
    if len(title) > 80:
        raise ValueError('标题最多 80 个码点')
    return title

assert normalize_title('  接口笔记  ') == '接口笔记'
assert len('😀') == 1
```

预测练习：`None/null`、空格、80 个“学”、81 个“学”各走哪个分支？参考结果：前两者拒绝，80 个接受，81 个拒绝。边界一致需要共同测试，不能只看函数名称相同。

## 卡 2：把输入显示为文字

```javascript
const item = document.createElement('li');
item.textContent = record.title;
list.appendChild(item);
```

将标题设为 `<strong>这不是加粗指令</strong>`，预期页面显示整段文字，而不是执行标签含义。此例只说明普通文本展示；富文本需要另外设计清理和允许规则。

## 卡 3：先判断响应，再读结果

```javascript
async function saveRecord(payload) {
  const response = await fetch('/api/records', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error?.message || '保存失败，请重试');
  }
  return body.data;
}
```

这是以接口保证返回 JSON 为前提的最小例子。真实应用还需处理非 JSON 响应、请求超时、认证、重复请求与用户状态。DELETE 返回 204 时不调用 `response.json()`。练习：关闭服务与返回 400，两者分别在哪一步失败？

## 卡 4：在内存数据库中观察事务

保存下列内容为练习脚本运行。仅使用内存数据库，不访问个人项目数据库。

```python
import sqlite3

db = sqlite3.connect(':memory:')
db.execute('PRAGMA foreign_keys = ON')
db.executescript('''
CREATE TABLE projects(id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE records(
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id),
  title TEXT NOT NULL
);
''')
with db:
    db.execute('INSERT INTO projects VALUES (?, ?)', ('p1', '网页练习'))

try:
    with db:
        db.execute('INSERT INTO records VALUES (?, ?, ?)', ('r1', 'p1', '接口笔记'))
        db.execute('INSERT INTO records VALUES (?, ?, ?)', ('r1', 'p1', '重复编号'))
except sqlite3.IntegrityError:
    print('本批导入已回滚')

count = db.execute('SELECT COUNT(*) FROM records').fetchone()[0]
assert count == 0
print('当前资料数：', count)
db.close()
```

预期：提示回滚，资料数为 0。把第二个 id 改成 r2，事务可以成功，断言需按新场景改为 2。这个改变说明测试期望必须跟随业务场景，不能不看输入就固定写“通过”。

## 卡 5：权限必须出现在服务端路径上

以下为伪代码，不是某框架的可直接运行实现。

```text
current_user = verify_session(request)
record = database.find_record(record_id)
if record is absent:
    return not_found
project = database.find_project(record.project_id)
if project.owner_id != current_user.id:
    return forbidden
return permitted_operation(record)
```

测试时不能只用所有者账户。让 B 使用 A 的 record_id 重复读、改、删，核对响应及数据库状态。生产实现还应考虑检查与写入之间的一致性，不能在授权后允许资源归属被竞态改变。

## 卡 6：摘要任务与普通资料分离

```text
任务：把下面的笔记压缩为三条要点。
边界：只使用给定笔记，不增加日期、数量、结论或引用。
缺失处理：资料不足时明确写出不足。
输出：JSON，包含 summary（字符串）与 keywords（字符串数组）。
笔记：
<用户主动选定且有权限访问的内容>
```

这段提示词不保证模型遵守约定。服务端仍要检查格式和长度，用户仍需核对摘要是否忠实。`笔记` 区域中的命令性文字应按资料处理，不能改变工具权限。

## 卡 7：引用也需要验证

```python
def validate_citation_ids(citations, allowed_ids):
    if not isinstance(citations, list):
        return False
    return all(isinstance(item, str) and item in allowed_ids
               for item in citations)

assert validate_citation_ids(['r1'], {'r1', 'r2'})
assert not validate_citation_ids(['r9'], {'r1', 'r2'})
```

这段代码只检查编号属于本次允许集合，不能证明资料支持答案。空引用也会通过这个集合检查，因此还需依据问题类型与 evidenceStatus 检查是否应有引用，并对关键事实进行内容核对。
