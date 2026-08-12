"""集成测试 — 测试所有功能"""
import sys, os, json, urllib.request, urllib.error, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Start server in subprocess
import subprocess
proc = subprocess.Popen([sys.executable, 'app.py'],
    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)

BASE = 'http://127.0.0.1:8765'
PASS = 0
FAIL = 0

def api(method, path, data=None):
    url = BASE + path
    try:
        if data is not None:
            req = urllib.request.Request(url, data=json.dumps(data).encode(),
                headers={'Content-Type': 'application/json'}, method=method)
        else:
            req = urllib.request.Request(url, method=method)
        resp = urllib.request.urlopen(req, timeout=60)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try: body = json.loads(body)
        except: pass
        return e.code, body
    except Exception as e:
        return 0, str(e)

def check(label, ok):
    global PASS, FAIL
    if ok: PASS += 1; print(f'  [PASS] {label}')
    else: FAIL += 1; print(f'  [FAIL] {label}')

# ============================================================
print('\n=== 1. 基础连通性 ===')
s, _ = api('GET', '/'); check('首页', s == 200)
s, r = api('GET', '/api/templates'); check('模板列表', s == 200)

# ============================================================
print('\n=== 2. 经历管理 ===')
for mod, payload in [
    ('basic-info', {'name':'张三','phone':'138','email':'z@t.com','age':'28','job_target':'Python'}),
    ('education', {'school':'清华','major':'CS','degree':'硕士','start_date':'2020','end_date':'2023'}),
    ('internships', {'company':'字节','position':'后端','start_date':'2023','end_date':'至今','description':'推荐系统开发'}),
    ('projects', {'name':'电商后台','role':'负责人','tech_stack':'Python','background':'性能瓶颈','actions':'主导架构','results':'QPS 10x'}),
    ('skills', {'name':'Python','level':'精通','evidence':'3个商业项目','category':'语言'}),
]:
    s, r = api('POST', f'/api/experiences/{mod}', payload)
    check(f'添加 {mod}', s == 200)

s, r = api('POST', '/api/experiences/self-evaluation', {'content':'热爱技术'})
check('自我评价', s == 200)

s, r = api('GET', '/api/experiences/all')
check('获取所有经历', s == 200 and r['basic_info']['name'] == '张三')

# ============================================================
print('\n=== 3. JD分析 ===')
jd_text = '职位：Python后端开发工程师\n公司：字节跳动\n职责：负责核心业务系统后端设计与开发\n要求：3年Python，FastAPI/Django，MySQL/Redis\n加分：分布式、微服务'
s, r = api('POST', '/api/jd/clean', {'jd_text': jd_text})
check('JD分析', s == 200 and r.get('job_title','') != '')
print(f'      岗位={r.get("job_title")}')

# ============================================================
print('\n=== 4. 公司分析 ===')
s, r = api('POST', '/api/company/analyze', {'company_name':'字节跳动','jd_text': jd_text})
check('快速分析', s == 200 and 'verdict' in r)
print(f'      结论={r.get("verdict","?")}')

s, r = api('POST', '/api/company/search', {'company_name':'字节跳动','location':'北京'})
check('深度洞察(降级DeepSeek)', s == 200 and r.get('success'))
print(f'      来源={r.get("source")}')

# ============================================================
print('\n=== 5. 简历生成 ===')
s, r = api('POST', '/api/resumes/generate', {'jd_text': jd_text, 'template_type': 'default'})
check('简历生成', s == 200 and r.get('resume_html') and len(r.get('resume_html','')) > 500)
print(f'      HTML长度={len(r.get("resume_html",""))}')

# ============================================================
print('\n=== 6. 求职信+面试题 ===')
s, r = api('POST', '/api/resumes/cover-letter', {'jd_text': jd_text})
check('求职信', s == 200 and len(r.get('cover_letter','')) > 50)

s, r = api('POST', '/api/resumes/interview-questions', {'jd_text': jd_text})
q_count = len(r.get('tech_questions',[])) + len(r.get('project_deep_dive',[])) + len(r.get('behavioral_questions',[]))
check('面试题生成', s == 200 and q_count > 0)
print(f'      题目数={q_count}')

# ============================================================
print('\n=== 7. 模拟面试 ===')
s, r = api('POST', '/api/interview/start', {'jd_text': jd_text})
check('开始面试', s == 200 and r.get('session_id'))
sid = r.get('session_id','')
print(f'      总题数={r.get("total_questions",0)}')

if sid:
    # 回答第1题
    s, r = api('POST', '/api/interview/answer', {'session_id':sid, 'answer':'我有3年Python后端经验，主导过电商后台系统架构设计，使用FastAPI+PostgreSQL实现了订单管理和支付模块，QPS从1000提升到10000。'})
    check('提交回答', s == 200)

    # 继续回答几题直到结束
    for i in range(10):
        if r.get('is_complete'): break
        s, r = api('POST', '/api/interview/answer', {'session_id':sid, 'answer':f'这是第{i+2}题的详细回答，涵盖了我的项目经验、技术深度和团队协作能力。我使用了Python FastAPI构建微服务，部署在K8s集群上。'})
        if 'error' in str(r): break

    # 结束面试
    if not r.get('is_complete'):
        s, r = api('POST', '/api/interview/end', {'session_id': sid})
    check('评估报告', 'evaluation' in r or r.get('is_complete'))
    if r.get('evaluation'):
        print(f'      匹配度={r["evaluation"].get("overall_match","?")}')

# ============================================================
print('\n=== 8. 投递记录 ===')
s, r = api('POST', '/api/delivery/submit', {
    'resume_html': '<html><body>test</body></html>',
    'jd_text': jd_text, 'company_name':'字节跳动', 'job_title':'Python后端',
})
check('提交投递', s == 200 and r.get('success'))
rid = r.get('record_id')

s, r = api('GET', '/api/delivery/records'); check('投递列表', r.get('total',0) > 0)
import urllib.parse; s, r = api('GET', '/api/delivery/records?search=' + urllib.parse.quote('字节')); check('搜索', isinstance(r, dict) and r.get('total',0) > 0)

s, r = api('POST', '/api/delivery/submit', {
    'resume_html': '<html><body>dup</body></html>',
    'jd_text': jd_text, 'company_name':'字节', 'job_title':'工程师',
})
check('重复检测', not r.get('success'))

if rid:
    s, r = api('GET', f'/api/delivery/records/{rid}')
    check('投递详情', r.get('company_name') == '字节跳动')
    api('DELETE', f'/api/delivery/records/{rid}')

# ============================================================
print('\n=== 9. 前端验证 ===')
req = urllib.request.Request(BASE + '/')
html = urllib.request.urlopen(req, timeout=5).read().decode()
check('Tab1 经历管理', '经历管理' in html)
check('Tab2 简历生成', '简历生成' in html)
check('Tab3 公司洞察', '公司洞察' in html)
check('Tab4 面试准备', '面试准备' in html)
check('Tab5 我的投递', '我的投递' in html)
check('跨Tab跳转', 'jumpToCompanyTab' in html and 'jumpToInterviewTab' in html)
check('深度洞察按钮', '深度洞察' in html)
check('快速分析按钮', '快速分析' in html)

# ============================================================
print(f'\n{"="*50}')
print(f'  TOTAL: {PASS} passed, {FAIL} failed')
print(f'{"="*50}')
