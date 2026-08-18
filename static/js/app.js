const { createApp, ref, reactive, computed, onMounted, nextTick, watch } = Vue;

createApp({
    setup() {
        const svgImport = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z"/></svg>';
const svgExperience = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8"/><path d="M8 17h5"/></svg>';
const svgGenerate = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M9 15l2 2 4-4"/></svg>';
const svgCompany = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/></svg>';
const svgInterview = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';
const svgDelivery = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/></svg>';

const tabs = [
    {id: 'import', label: 'AI导入', icon: svgImport, group: 'core'},
    {id: 'experience', label: '经历管理', icon: svgExperience, group: 'core'},
    {id: 'generate', label: '简历生成', icon: svgGenerate, group: 'core'},
    {id: 'company', label: '公司洞察', icon: svgCompany, group: 'extra'},
    {id: 'interview', label: '面试准备', icon: svgInterview, group: 'extra'},
    {id: 'delivery', label: '我的投递', icon: svgDelivery, group: 'extra'},
];
const coreTabs = tabs.filter(t => t.group === 'core');
const extraTabs = tabs.filter(t => t.group === 'extra');
        const currentTab = ref('import');

        function switchTab(tabId) {
            currentTab.value = tabId;
            if (tabId === 'delivery') {
                loadDeliveryRecords(1);
            }
        }

        // 跨Tab跳转
        function jumpToCompanyTab() {
            if (jdAnalysis.value && jdAnalysis.value.company_name) {
                companySearchName.value = jdAnalysis.value.company_name;
            }
            currentTab.value = 'company';
            // 自动触发搜索
            if (companySearchName.value.trim()) {
                searchCompany();
            }
        }

        function jumpToInterviewTab() {
            currentTab.value = 'interview';
        }

        function quickAnalyzeCompany() {
            // 调用旧的 analyzeCompany，结果精简显示在 Tab 2
            analyzeCompany();
        }

        // ======== 经历管理 ========
        const basicInfo = reactive({name:'', phone:'', email:'', age:'', job_target:'', photo_path:''});
        const modules = reactive([
            {key:'education', label:'教育背景', icon:'🎓', items:[],
                hint:'从最高学历开始填写，每条包含学校、专业、学位、起止时间'},
            {key:'internships', label:'工作经历', icon:'💼', items:[],
                hint:'包含全职工作和实习经历，每段经历写清楚公司、职位、起止时间和主要职责'},
            {key:'projects', label:'项目经历', icon:'📁', items:[],
                hint:'挑2-3个最有代表性的项目，用STAR法则描述（背景→动作→成果），尽量量化'},
            {key:'skills', label:'技能', icon:'🛠', items:[],
                hint:'列出你掌握的技术和工具，每条标上熟练度和一句证据（如"独立开发过3个SPA项目"）'},
            {key:'awards', label:'获奖情况', icon:'🏆', items:[],
                hint:'竞赛获奖、奖学金、荣誉称号等。编程比赛获奖放这里，编程技能放「技能」模块'},
            {key:'others', label:'其他信息', icon:'📌', items:[],
                hint:'证书、语言能力、培训经历、兴趣爱好等不属于以上分类的内容，每类一条'},
        ]);
        // 模块英文 key -> 中文名（去重弹窗等展示用）
        const MODULE_LABELS = {education:'教育背景', internships:'工作经历', work_experience:'工作经历', projects:'项目经历', skills:'技能', awards:'获奖情况', others:'其他信息'};
        const selfEval = reactive({content:''});
        const pasteText = ref('');
        const parsing = ref(false);
        const resumeFileInput = ref(null);
        const fileImporting = ref(false);
        const collectingPrompt = ref(false);
        const photoInput = ref(null);
        const photoPreviewUrl = ref('');

        function getModule(key) {
            return modules.find(m => m.key === key) || {items:[]};
        }

        function getPhotoUrl(photoPath) {
            if (!photoPath) return '';
            const filename = photoPath.replace(/\\/g, '/').split('/').pop();
            return '/api/photos/' + filename;
        }

        async function loadExperiences() {
            try {
                const data = await API.get('/api/experiences/all');
                Object.assign(basicInfo, data.basic_info || {});
                modules.find(m=>m.key==='education').items = data.education || [];
                modules.find(m=>m.key==='internships').items = data.internships || [];
                modules.find(m=>m.key==='projects').items = data.projects || [];
                modules.find(m=>m.key==='skills').items = data.skills || [];
                modules.find(m=>m.key==='awards').items = data.awards || [];
                modules.find(m=>m.key==='others').items = data.others || [];
                Object.assign(selfEval, data.self_evaluation || {});
                // 刷新照片预览
                if (basicInfo.photo_path) {
                    photoPreviewUrl.value = getPhotoUrl(basicInfo.photo_path);
                }
            } catch(e) { console.error('加载经历失败:', e); }
        }

        async function saveBasicInfo() {
            try {
                await API.post('/api/experiences/basic-info', {...basicInfo});
                alert('基本信息已保存');
            } catch(e) { alert('保存失败: ' + e.message); }
        }

        async function saveSelfEval() {
            try {
                await API.post('/api/experiences/self-evaluation', {content: selfEval.content});
                alert('自我评价已保存');
            } catch(e) { alert('保存失败: ' + e.message); }
        }

        function formatItem(item) {
            const vals = Object.entries(item).filter(([k,v]) =>
                typeof v === 'string' && v && k !== 'id' && k !== 'sort_order'
            );
            return vals.slice(0, 4).map(([k,v]) => v).join(' | ') || '(空)';
        }

        // 分字段编辑表单
        const editingId = ref(null);
        const editFields = reactive({});

        const fieldDefs = {
            education: [
                {key:'school', label:'学校', placeholder:'例：清华大学'},
                {key:'major', label:'专业', placeholder:'例：计算机科学'},
                {key:'degree', label:'学位', placeholder:'例：本科'},
                {key:'start_date', label:'入学时间', placeholder:'例：2020.09'},
                {key:'end_date', label:'毕业时间', placeholder:'例：2024.07'},
            ],
            internships: [
                {key:'company', label:'公司', placeholder:'例：字节跳动'},
                {key:'position', label:'职位', placeholder:'例：Python后端开发工程师'},
                {key:'start_date', label:'开始时间', placeholder:'例：2023.07'},
                {key:'end_date', label:'结束时间', placeholder:'例：至今'},
                {key:'description', label:'主要职责', placeholder:'例：负责推荐系统后台开发，设计并实现了高并发API网关...'},
            ],
            projects: [
                {key:'name', label:'项目名称', placeholder:'例：电商后台系统'},
                {key:'role', label:'担任角色', placeholder:'例：后端负责人'},
                {key:'tech_stack', label:'技术栈', placeholder:'例：Python, FastAPI, PostgreSQL'},
                {key:'start_date', label:'开始时间', placeholder:'例：2023.01'},
                {key:'end_date', label:'结束时间', placeholder:'例：2023.06'},
                {key:'background', label:'项目背景', placeholder:'例：旧系统性能瓶颈，需重构...'},
                {key:'actions', label:'你的行动', placeholder:'例：主导架构设计，独立完成核心模块开发...'},
                {key:'results', label:'项目成果', placeholder:'例：QPS从1000提升至10000，支撑双11峰值'},
            ],
            skills: [
                {key:'name', label:'技能名称', placeholder:'例：Python'},
                {key:'level', label:'熟练度', placeholder:'例：精通 / 熟练 / 了解'},
                {key:'evidence', label:'掌握证据', placeholder:'例：独立开发过3个商业项目'},
                {key:'category', label:'分类', placeholder:'例：编程语言 / 框架 / 数据库'},
            ],
            awards: [
                {key:'name', label:'奖项名称', placeholder:'例：ACM-ICPC亚洲区域赛'},
                {key:'level', label:'奖项级别', placeholder:'例：国家级 / 省级 / 校级'},
                {key:'date', label:'获奖时间', placeholder:'例：2023.06'},
            ],
            others: [
                {key:'title', label:'标题', placeholder:'例：CET-6 英语六级'},
                {key:'content', label:'内容', placeholder:'例：2023年通过，阅读248 / 写作212'},
            ],
        };

        function getFields(modKey) {
            return fieldDefs[modKey] || [{key:'name', label:'名称', placeholder:'输入名称'}];
        }

        function startEdit(modKey, item) {
            editingId.value = item.id;
            const fields = getFields(modKey);
            // 清空并填充编辑字段
            Object.keys(editFields).forEach(k => delete editFields[k]);
            fields.forEach(f => {
                editFields[f.key] = item[f.key] || '';
            });
        }

        function cancelEdit() {
            editingId.value = null;
        }

        async function confirmEdit(modKey, item) {
            const fields = getFields(modKey);
            // 将 editFields 的值写回 item
            fields.forEach(f => {
                item[f.key] = editFields[f.key] || '';
            });
            try {
                await API.put(`/api/experiences/${modKey}/${item.id}`, item);
                await loadExperiences();
                cancelEdit();
            } catch(e) { alert('更新失败: ' + e.message); }
        }

        async function deleteItem(modKey, id) {
            if (!confirm('确认删除？')) return;
            try {
                await API.del(`/api/experiences/${modKey}/${id}`);
                await loadExperiences();
            } catch(e) { alert('删除失败: ' + e.message); }
        }

        // 跨模块移动：分错了模块（如技能里的证书）一键移到正确模块
        function otherModules(modKey) {
            return modules.filter(m => m.key !== modKey);
        }
        async function moveItem(fromModule, itemId, toModule) {
            if (!toModule) return;
            if (!confirm('确认把这条移到「' + (MODULE_LABELS[toModule] || toModule) + '」？')) { return; }
            try {
                await API.post('/api/experiences/move', {from_module: fromModule, item_id: itemId, to_module: toModule});
                await loadExperiences();
            } catch(e) { alert('移动失败: ' + e.message); }
        }

        // 内联添加（展开完整字段表单）
        const addingModule = ref(null);

        function startAddItem(modKey) {
            addingModule.value = modKey;
            // 清空编辑字段
            Object.keys(editFields).forEach(k => delete editFields[k]);
        }

        function cancelAdd() {
            addingModule.value = null;
        }

        async function confirmAddItem(modKey) {
            const fields = getFields(modKey);
            const item = {sort_order: 0};
            fields.forEach(f => { item[f.key] = editFields[f.key] || ''; });
            // 至少要有名称
            if (!item.name && !item.school && !item.company && !item.title) {
                alert('请至少填写一项内容'); return;
            }
            try {
                await API.post(`/api/experiences/${modKey}`, item);
                await loadExperiences();
                cancelAdd();
            } catch(e) { alert('添加失败: ' + e.message); }
        }

        // 照片上传
        async function uploadPhoto(e) {
            const file = e.target.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            try {
                const r = await fetch('/api/experiences/upload-photo', { method: 'POST', body: formData });
                const data = await r.json();
                if (data.photo_path) {
                    basicInfo.photo_path = data.photo_path;
                    photoPreviewUrl.value = getPhotoUrl(data.photo_path);
                    await saveBasicInfo();
                    alert('照片已上传并保存');
                }
            } catch(err) {
                alert('照片上传失败: ' + err.message);
            }
        }

        function removePhoto() {
            if (!confirm('确认移除照片？')) return;
            basicInfo.photo_path = '';
            photoPreviewUrl.value = '';
            saveBasicInfo();
        }

        // AI 智能导入
        async function parseText() {
            if (!pasteText.value.trim()) { alert('请先粘贴经历文本'); return; }
            parsing.value = true;
            try {
                const r = await API.post('/api/experiences/parse-text', {text: pasteText.value});
                let count = 0;
                // 导入前本地去重（完全重复自动跳过，用户可确认）
                const skipSet = new Set();
                let dupSkipped = 0;
                try {
                    const dup = await API.post('/api/experiences/import-check', {items: r});
                    if (dup) {
                        // ① 完全重复（本地精确比对，零误判）
                        if (dup.duplicates && dup.duplicates.length > 0) {
                            const list = dup.duplicates.slice(0, 8).map(d => '· [' + (MODULE_LABELS[d.module] || d.module) + '] ' + (d.name || d.reason)).join('\n');
                            if (confirm('检测到 ' + dup.duplicates.length + ' 条内容与已有经历完全重复：\n\n' + list + (dup.duplicates.length > 8 ? '\n…等共 ' + dup.duplicates.length + ' 条' : '') + '\n\n点「确定」跳过重复，只导入不重复的；点「取消」全部导入。')) {
                                for (const d of dup.duplicates) skipSet.add(d.module + ':' + d.index);
                                dupSkipped = dup.duplicates.length;
                            }
                        }
                        // ② AI 疑似语义重复（文字不同但可能同一件事）→ 用户二次确认
                        if (dup.suspicious && dup.suspicious.length > 0) {
                            const list = dup.suspicious.slice(0, 8).map(d => '· [' + (MODULE_LABELS[d.module] || d.module) + '] ' + (d.name || d.reason)).join('\n');
                            if (confirm('AI 检测到以下内容可能与已有经历是同一件事（文字表述不同）：\n\n' + list + (dup.suspicious.length > 8 ? '\n…等共 ' + dup.suspicious.length + ' 条' : '') + '\n\n是否也跳过这些？')) {
                                for (const d of dup.suspicious) skipSet.add(d.module + ':' + d.index);
                                dupSkipped += dup.suspicious.length;
                            }
                        }
                    }
                } catch(e) { /* 去重失败不阻断导入 */ }
                if (r.basic_info && r.basic_info.name) {
                    await API.post('/api/experiences/basic-info', r.basic_info);
                }
                for (let i = 0; i < (r.education || []).length; i++) {
                    if (skipSet.has('education:' + i)) continue;
                    await API.post('/api/experiences/education', r.education[i]); count++;
                }
                // 兼容 work_experience 和 internships
                const workExps = r.work_experience || r.internships || [];
                for (let i = 0; i < workExps.length; i++) {
                    if (skipSet.has('work_experience:' + i) || skipSet.has('internships:' + i)) continue;
                    await API.post('/api/experiences/internships', workExps[i]); count++;
                }
                for (let i = 0; i < (r.projects || []).length; i++) {
                    if (skipSet.has('projects:' + i)) continue;
                    await API.post('/api/experiences/projects', r.projects[i]); count++;
                }
                for (let i = 0; i < (r.skills || []).length; i++) {
                    if (skipSet.has('skills:' + i)) continue;
                    await API.post('/api/experiences/skills', r.skills[i]); count++;
                }
                for (let i = 0; i < (r.awards || []).length; i++) {
                    if (skipSet.has('awards:' + i)) continue;
                    await API.post('/api/experiences/awards', r.awards[i]); count++;
                }
                for (let i = 0; i < (r.others || []).length; i++) {
                    if (skipSet.has('others:' + i)) continue;
                    await API.post('/api/experiences/others', r.others[i]); count++;
                }
                if (r.self_evaluation && r.self_evaluation.content) {
                    await API.post('/api/experiences/self-evaluation', r.self_evaluation);
                }
                await loadExperiences();
                pasteText.value = '';
                alert(`AI 解析完成！已导入 ${count} 条经历到各模块` + (dupSkipped ? `，跳过 ${dupSkipped} 条重复` : '') + `\n\n请逐模块检查信息是否准确。`);
            } catch(e) {
                alert('AI解析失败: ' + e.message + '\n\n请检查: 1) .env中是否配置了API Key 2) 网络是否正常');
            }
            parsing.value = false;
        }

        // ======== 简历生成 ========
        const jdText = ref('');
        const templateType = ref('default');
        const tplFileInput = ref(null);
        const templateList = ref([
            {id: 'default', name: '📋 项目经历优先（默认）'},
            {id: 'education', name: '🎓 教育背景优先'},
        ]);
        const generating = ref(false);
        const result = ref(null);

        // 行业侧重点分析
        const jdIndustry = ref('');
        const industryOptions = ref([
            '互联网/科技', '人工智能', '金融/银行/证券', '快消/消费品/零售',
            '制造/汽车/工业', '医疗/医药/生物', '教育/培训', '咨询/审计/专业服务',
            '传媒/内容/游戏', '能源/化工/材料', '建筑/地产/工程',
        ]);
        const industryAnalysis = ref(null);
        const analyzingIndustry = ref(false);

        // JD分析
        const jdAnalysis = ref(null);
        const analyzingJD = ref(false);

        async function analyzeJD() {
            if (!jdText.value.trim()) return;
            analyzingJD.value = true;
            analyzingIndustry.value = true;
            try {
                jdAnalysis.value = await API.post('/api/jd/clean', {jd_text: jdText.value});
            } catch(e) { alert('JD分析失败: ' + e.message); }
            try {
                industryAnalysis.value = await API.post('/api/jd/industry-analysis', {
                    jd_text: jdText.value,
                    industry: jdIndustry.value,
                });
            } catch(e) { /* 行业分析失败不阻断 */ }
            analyzingJD.value = false;
            analyzingIndustry.value = false;
        }

        function industryConfidenceClass(conf) {
            if (conf === 'high' || conf === 'user') return 'jd-tag-nice';
            if (conf === 'medium') return '';
            return 'jd-tag-hard';
        }

        function industryConfidenceLabel(conf) {
            if (conf === 'high') return '置信度：高';
            if (conf === 'medium') return '置信度：中';
            if (conf === 'low') return '置信度：低';
            if (conf === 'user') return '手动指定';
            return conf;
        }

        // 公司分析
        const companyResult = ref(null);
        const companyLoading = ref(false);

        async function analyzeCompany() {
            if (!jdText.value.trim()) return;
            companyLoading.value = true;
            companyResult.value = null;
            try {
                // 1. 从JD中提取公司名
                const jdR = await API.post('/api/jd/clean', {jd_text: jdText.value});
                const cn = jdR.company_name;
                if (!cn) { alert('未从JD中识别到公司名称，请确认JD中包含公司信息'); companyLoading.value = false; return; }
                // 2. AI分析公司
                const r = await API.post('/api/company/analyze', {company_name: cn, jd_text: jdText.value});
                r.company_name = cn;
                companyResult.value = r;
            } catch(e) { alert('公司分析失败: ' + e.message); }
            companyLoading.value = false;
        }

        // 粘贴工商数据AI解读
        const rawCompanyData = ref('');
        const dataInterpretation = ref(null);
        const interpreting = ref(false);

        async function interpretData() {
            if (!rawCompanyData.value.trim()) return;
            interpreting.value = true;
            dataInterpretation.value = null;
            try {
                const cn = companyResult.value ? companyResult.value.company_name : '';
                dataInterpretation.value = await API.post('/api/company/interpret', {
                    company_name: cn,
                    raw_data: rawCompanyData.value,
                });
            } catch(e) { alert('解读失败: ' + e.message); }
            interpreting.value = false;
        }

        // 一键清空经历库
        async function clearAllExperience() {
            if (!confirm('确定清空全部经历数据吗？\n\n包括：基本信息、教育、实习、项目、技能、获奖、自我评价\n\n此操作不可恢复！')) return;
            if (!confirm('再次确认：真的要清空吗？清空后需重新录入所有经历。')) return;
            try {
                await API.post('/api/experiences/clear-all', {});
                await loadExperiences();
                alert('✅ 经历库已清空');
            } catch(e) {
                alert('清空失败: ' + e.message);
            }
        }

        // 生成前内容量预检：偏少则提醒用户先补充真实经历
        function precheckExperience() {
            const projCount = ((modules.find(m=>m.key==='projects')||{}).items||[]).length;
            const internCount = ((modules.find(m=>m.key==='internships')||{}).items||[]).length;
            const skillCount = ((modules.find(m=>m.key==='skills')||{}).items||[]).length;
            const reasons = [];
            if (projCount === 0 && internCount === 0) reasons.push('还没有任何项目或实习经历，简历缺少核心内容');
            if (projCount + internCount < 2) reasons.push('项目/实习经历较少（当前 ' + (projCount+internCount) + ' 条），简历很可能填不满一页');
            if (skillCount < 3) reasons.push('技能只有 ' + skillCount + ' 项，建议补充到 6 项以上');
            return reasons;
        }

        // ======== 关键词覆盖率预览（生成前） ========
        const matchPreview = ref(null);
        const matchPreviewLoading = ref(false);
        let matchPreviewTimer = null;

        const matchPreviewScore = computed(() => {
            const p = matchPreview.value;
            if (!p) return null;
            return p.fillable_score != null ? p.fillable_score : p.score;
        });
        const matchPreviewHitText = computed(() => {
            const p = matchPreview.value;
            if (!p) return '';
            const hit = (p.matched || []).length;
            const total = p.total - (p.unfillable_n || 0);
            return hit + '/' + Math.max(total, 0);
        });
        const matchPreviewCardClass = computed(() => {
            const s = matchPreviewScore.value;
            if (s == null) return 'match-card-high';
            if (s < 60) return 'match-card-low';
            if (s < 70) return 'match-card-medium';
            return 'match-card-high';
        });
        const matchPreviewLevelLabel = computed(() => {
            const s = matchPreviewScore.value;
            if (s == null) return '';
            if (s >= 70) return '可补命中率达标 · 可生成';
            if (s >= 60) return '可补命中率良好 · 建议微调';
            return '可补命中率偏低 · 建议先补';
        });
        const matchPreviewLevelTag = computed(() => {
            const s = matchPreviewScore.value;
            if (s == null) return 'jd-tag-nice';
            if (s < 60) return 'jd-tag-hard';
            return 'jd-tag-nice';
        });
        const matchPreviewBarClass = computed(() => {
            const s = matchPreviewScore.value;
            if (s == null) return 'match-preview-bar-high';
            if (s < 60) return 'match-preview-bar-low';
            if (s < 70) return 'match-preview-bar-medium';
            return 'match-preview-bar-high';
        });
        const matchPreviewBarWidth = computed(() => {
            const s = matchPreviewScore.value;
            return (s == null ? 0 : Math.max(2, s)) + '%';
        });
        const matchPreviewSuggestions = computed(() => {
            const p = matchPreview.value;
            if (!p || !p.suggestions) return [];
            return p.suggestions.filter(s => s.type !== '专名' && s.type !== '行业属性');
        });
        const matchPreviewUnfillableText = computed(() => {
            const p = matchPreview.value;
            if (!p || !p.unfillable || !p.unfillable.length) return '';
            return '另有 ' + p.unfillable.length + ' 个行业/公司属性词（' + p.unfillable.join('、') + '）不计入命中率，可忽略';
        });

        async function refreshMatchPreview() {
            if (!jdText.value.trim()) { matchPreview.value = null; return; }
            matchPreviewLoading.value = true;
            try {
                matchPreview.value = await API.post('/api/match/preview', { jd_text: jdText.value });
            } catch(e) { /* 网络/接口异常静默，不打断用户 */ }
            matchPreviewLoading.value = false;
        }

        // JD 变化自动检测（防抖 500ms），粘贴即出覆盖率
        watch(jdText, () => {
            if (matchPreviewTimer) clearTimeout(matchPreviewTimer);
            matchPreviewTimer = setTimeout(() => { refreshMatchPreview(); }, 500);
        });

        async function generateResume() {
            if (!jdText.value.trim()) { alert('请先粘贴目标岗位的JD'); return; }
            // 生成前内容量预检：偏少先弹窗解释，避免生成后才发现问题
            try {
                const reasons = precheckExperience();
                if (reasons.length > 0) {
                    const ok = confirm('⚠️ 检测到你的经历内容偏少：\n\n' + reasons.map(r=>'· ' + r).join('\n') + '\n\n生成的简历可能填不满一页，内容不够充实。\n建议先去「经历管理」补充更多真实经历再生成，效果会更好。\n\n仍要继续生成吗？\n（点「确定」继续生成，点「取消」先去补充经历）');
                    if (!ok) { return; }
                }
            } catch(e) {}
            generating.value = true;
            result.value = null;
            // 生成前匹配度预览（零AI成本）：复用实时检测结果，低/中匹配度先征询用户
            if (!matchPreview.value) {
                await refreshMatchPreview();
            }
            const previewMatch = matchPreview.value;
            const pvScore = previewMatch
                ? (previewMatch.fillable_score != null ? previewMatch.fillable_score : previewMatch.score)
                : null;
            if (previewMatch && pvScore != null && pvScore < 70) {
                const hit = previewMatch.matched ? previewMatch.matched.length : 0;
                const fillTotal = (previewMatch.total || 0) - (previewMatch.unfillable_n || 0);
                const miss = (previewMatch.suggestions && previewMatch.suggestions.length)
                    ? previewMatch.suggestions.slice(0, 8).map(s => '· ' + s.keyword + '：' + s.suggestion).join('\n')
                    : ((previewMatch.missing_keywords || []).join('、') || '（未能识别关键词）');
                const ok = confirm(
                    '当前经历库可补关键词命中 ' + hit + '/' + Math.max(fillTotal, 0) + '（可补命中率 ' + pvScore + ' 分，低于 70% 达标线）。\n\n'
                    + '以下关键词暂未覆盖：\n' + miss + '\n\n'
                    + 'AI 将启用「匹配增强模式」：在不编造的前提下，按岗位视角重新提炼现有经历、补强技能区与自我评价。\n\n'
                    + '建议先去「经历管理」把确实会用/做过的补上，命中率可到 70%+。\n\n仍要继续生成吗？'
                );
                if (!ok) { generating.value = false; return; }
            }
            try {
                result.value = await API.post('/api/resumes/generate', {
                    jd_text: jdText.value,
                    template_type: templateType.value,
                    industry: jdIndustry.value,
                });
                currentTab.value = 'generate';
                compactLevel.value = 0;
                fillMode.value = false;
                fillFactor.value = 1;
                fitNotice.value = '';
                renderResumePreview();
                await autoFitToPage();
            } catch(e) {
                alert('简历生成失败: ' + e.message + '\n\n可能原因: 1) 经历库为空 2) API Key未配置 3) 网络问题');
            }
            generating.value = false;
        }

        // ======== A4 一页适配：压缩档位 / 自动填充 / 页数徽标 ========
        // 打印一页可用高度：A4高(297mm≈1123px) - 打印上下padding(0.7cm×2≈53px) ≈ 1070px，再留2%余量
        const PRINT_PAGE_H = 1060;
        const compactLevel = ref(0);   // 0=正常 1=轻压 2=最小字号
        const fillMode = ref(false);   // 内容过少时自动拉伸至接近一页
        const fillFactor = ref(1);       // 填充强度（动态计算）
        const pageCount = ref(1);
        const pageOverflow = ref(false);
        const fitNotice = ref('');       // 一页自动适配状态提示
        const fitAutoRun = ref(false);   // 防止自动适配递归
        const trimTried = ref(false);   // 本次适配是否已 AI 精简过（防重复调用）
        const expandTried = ref(false); // 本次适配是否已 AI 扩写过（防重复调用）

        const fitNoticeClass = computed(() => {
            if (fitNotice.value.startsWith('⚠️')) return 'fit-notice-warn';
            if (fitNotice.value.startsWith('✂️')) return 'fit-notice-info';
            return 'fit-notice-ok';
        });

        // 匹配度预警卡片
        const matchCardClass = computed(() => {
            const m = result.value && result.value.match_info;
            const s = m ? (m.fillable_score != null ? m.fillable_score : m.score) : null;
            if (s == null) return 'match-card-high';
            if (s < 60) return 'match-card-low';
            if (s < 70) return 'match-card-medium';
            return 'match-card-high';
        });
        const matchCardTitle = computed(() => {
            const lv = result.value && result.value.match_info ? result.value.match_info.level : '';
            if (lv === 'low') return '⚠️ 匹配度偏低 — 已启用增强模式';
            if (lv === 'medium') return '⚡ 匹配度一般 — 已启用增强模式';
            return '✅ 匹配度良好';
        });

        // 压缩/填充用的覆盖样式：CSS 变量 + calc，保证层级差（h1=正文+14 / h2=+4 / 条目标题=+2 / 辅助=-2）
        function buildResumeOverrideCss(level, fill, fillFactor) {
            const presets = [
                { base: 14, line: 1.8, space: 1 },   // 正常
                { base: 13.5, line: 1.7, space: 0.92 }, // 轻压
                { base: 13, line: 1.6, space: 0.85 },   // 中压
                { base: 12.5, line: 1.5, space: 0.78 }, // 重压
                { base: 12, line: 1.4, space: 0.72 },   // 极限
                { base: 11.5, line: 1.35, space: 0.68 },// 最小（硬下限，可读底线）
            ];
            const lv = presets[Math.min(Math.max(level, 0), 5)];
            let base = lv.base, line = lv.line, space = lv.space;
            if (fill) {
                // 填充模式：在当前字号档位基础上放大字号 + 行高 + 间距（层级差靠 calc 相对差值保持）
                const f = Math.max(1, Math.min(fillFactor || 1, 1.6));
                base = Math.min(lv.base + (f - 1) * 2, 16);
                line = Math.min(lv.line * Math.sqrt(f), 2.5);
                space = Math.min(lv.space * Math.sqrt(f), 1.7);
            }
            return [
                '@media screen { :host { width: 794px !important; max-width: 100% !important; padding: 0 0.8cm !important; box-sizing: border-box !important; } }',
                ':host { --r-base: ' + base + 'px; --r-line: ' + line + '; --r-space: ' + space + '; }',
                '.resume-body { font-size: var(--r-base) !important; line-height: var(--r-line) !important; }',
                '.resume-body h1, .resume-body .header-left h1 { font-size: calc(var(--r-base) + 14px) !important; line-height: 1.3 !important; margin-top: 0 !important; margin-bottom: calc(6px * var(--r-space)) !important; }',
                '.resume-body h2 { font-size: calc(var(--r-base) + 4px) !important; line-height: 1.3 !important; margin-top: calc(8px * var(--r-space)) !important; margin-bottom: calc(3px * var(--r-space)) !important; padding-bottom: calc(5px * var(--r-space)) !important; }',
                '.resume-body .item-title { font-size: calc(var(--r-base) + 2px) !important; }',
                '.resume-body .item-sub { font-size: calc(var(--r-base) - 2px) !important; }',
                '.resume-body .skills, .resume-body .project-bullets li { font-size: var(--r-base) !important; }',
                '.resume-body .project-bullets { margin-top: calc(6px * var(--r-space)) !important; }',
                '.resume-body .project-bullets li { margin-bottom: calc(6px * var(--r-space)) !important; line-height: calc(var(--r-line) * 0.9) !important; }',
                '.resume-body .item { margin-bottom: calc(4px * var(--r-space)) !important; }',
                '.resume-body .header { margin-top: calc(4px * var(--r-space)) !important; margin-bottom: calc(4px * var(--r-space)) !important; padding: calc(4px * var(--r-space)) !important; }',
                '.resume-body .info, .resume-body .info * { font-size: var(--r-base) !important; }',
                '.resume-body p { margin-top: calc(3px * var(--r-space)) !important; margin-bottom: calc(3px * var(--r-space)) !important; }',
                // 技能区紧凑：行高压低、段落间距收紧，避免技能区散开成多行大间隔
                '.resume-body .skills { line-height: 1.5 !important; }',
                '.resume-body .skills p { margin-top: 1px !important; margin-bottom: 1px !important; }',
                '.resume-body .skills hr.skill-divider { margin-top: 2px !important; margin-bottom: 2px !important; height: 1px !important; border: none; }',
                // A4 分页参考线（仅预览显示，导出不带出）
                '.preview-shell { position: relative; }',
                '.resume-page-guide { position: absolute; left: 0; right: 0; height: 0; border-top: 1.5px dashed #e0a800; pointer-events: none; z-index: 50; }',
                '.resume-page-guide::after { content: "▼ 第 " attr(data-page) " 页分页线（导出在此分页）"; position: absolute; right: 8px; top: 5px; font-size: 11px; color: #92400e; background: #fef3c7; padding: 1px 8px; border-radius: 10px; white-space: nowrap; box-shadow: 0 1px 3px rgba(0,0,0,0.15); }',
                '.resume-body .age-placeholder:empty::before { color: #aaa !important; font-size: 12px !important; }',
                // AI修改 diff：<del>旧内容(红删) <ins>新内容(绿增)，预览与打印均生效
                '.resume-body del { background: #fecaca !important; color: #991b1b !important; text-decoration: none !important; padding: 0 2px !important; border-radius: 2px !important; }',
                '.resume-body ins { background: #bbf7d0 !important; color: #166534 !important; text-decoration: none !important; padding: 0 2px !important; border-radius: 2px !important; font-weight: bold !important; }',
            ].join('\n');
        }

        // 根据内容高度估算页数（预览宽按 A4 比例 210:297 推算一页高度）
        function updatePageMeta() {
            const container = document.getElementById('resumePreview');
            if (!container || !container.shadowRoot) return;
            const wrapper = container.shadowRoot.querySelector('.resume-body');
            if (!wrapper) return;
            const pages = Math.max(0.1, wrapper.scrollHeight / PRINT_PAGE_H);
            pageCount.value = Math.max(1, Math.ceil(pages));
            pageOverflow.value = pages > 1.0;
            // 内容不足一页（< 0.95 页）→ 自动启用填充模式，目标接近 0.97 页（自动适配期间由 autoFitToPage 统一控制）
            if (!fillMode.value && !fitAutoRun.value && pages < 0.95) {
                fillMode.value = true;
                fillFactor.value = Math.max(1, Math.min(0.97 / pages, 3.0));
                renderResumePreview();
            }
        }

        // 绘制 A4 分页参考线：在每页结束处画一条虚线 + 页签
        function drawPageGuides(wrapper) {
            const shell = wrapper && wrapper.parentElement;
            if (!shell) return;
            shell.querySelectorAll('.resume-page-guide').forEach(el => el.remove());
            const lines = Math.floor(wrapper.scrollHeight / PRINT_PAGE_H);
            for (let i = 1; i <= lines; i++) {
                const g = document.createElement("div");
                g.className = "resume-page-guide";
                g.dataset.page = i;
                g.style.top = (PRINT_PAGE_H * i) + "px";
                shell.appendChild(g);
            }
        }

        // 当前内容折算页数
        function getPages() {
            const container = document.getElementById('resumePreview');
            if (!container || !container.shadowRoot) return 1;
            const w = container.shadowRoot.querySelector('.resume-body');
            return w ? Math.max(0.1, w.scrollHeight / PRINT_PAGE_H) : 1;
        }

        // 修改后一页适配：仅 CSS 压缩（保留 AI 修改的红绿 diff 标记，不调用 AI 精简）
        async function compressToFit() {
            if (!result.value || !result.value.resume_html) return;
            await renderResumePreview();
            for (let i = 0; i < 6; i++) {
                const pages = getPages();
                if (pages <= 1.0) break;
                if (compactLevel.value < 5) {
                    compactLevel.value++;
                    await renderResumePreview();
                } else break;
            }
            const finalPages = getPages();
            if (finalPages > 1.0) {
                fitNotice.value = '⚠️ 修改后内容偏多，已自动缩小字体至 11.5px，仍略超一页；接受修改后将自动精简至一页';
            } else {
                fitNotice.value = '';
            }
        }

        // 自动 AI 精简（超页兜底）：循环最多 2 轮，不劳用户手动用 AI 修改
        async function trimToFit() {
            for (let round = 0; round < 2; round++) {
                try {
                    const r = await API.post('/api/resumes/auto-trim', {
                        resume_html: result.value.resume_html,
                        jd_text: jdText.value,
                    });
                    if (r && r.revised_html) {
                        result.value.resume_html = r.revised_html;
                        compactLevel.value = 0;
                        fillMode.value = false;
                        fillFactor.value = 1;
                        await renderResumePreview();
                        if (!pageOverflow.value && getPages() >= 0.95) {
                            fitNotice.value = '✂️ 内容超出较多，已自动用 AI 精简至一页';
                            return;
                        }
                    }
                } catch(e) {
                    fitNotice.value = '⚠️ AI 精简失败，请直接在简历上删减次要内容';
                    return;
                }
            }
            fitNotice.value = '⚠️ 已压缩到最小字号并 AI 精简，仍超一页，请手动删减次要内容';
        }

        // 自动 AI 扩写（内容太少兜底）：基于真实经历展开句式，不编造事实
        async function expandToFit() {
            for (let round = 0; round < 2; round++) {
                try {
                    const r = await API.post('/api/resumes/auto-expand', {
                        resume_html: result.value.resume_html,
                        jd_text: jdText.value,
                    });
                    if (r && r.revised_html) {
                        result.value.resume_html = r.revised_html;
                        compactLevel.value = 0;
                        fillMode.value = false;
                        fillFactor.value = 1;
                        await renderResumePreview();
                        if (getPages() >= 0.95) return;
                    }
                } catch(e) {
                    fitNotice.value = '⚠️ AI 扩写失败，内容较少，建议补充更多真实经历';
                    return;
                }
            }
        }

        // 生成后自动适配一页（适配循环）：无论初始多少，收敛到 0.95~1.0 页（留白 0-2 行）
        // 超页 → 逐级压缩 → 仍超则 AI 精简（一次）；不足 → CSS 迭代填充 → 仍不足则 AI 扩写（一次，不编造）
        async function autoFitToPage() {
            if (!result.value || !result.value.resume_html) return;
            if (fitAutoRun.value) return;
            fitAutoRun.value = true;
            try {
                trimTried.value = false;
                expandTried.value = false;
                await renderResumePreview();
                for (let guard = 0; guard < 14; guard++) {
                    const pages = getPages();
                    // 达标：0.95~1.0 页（留白 0-2 行），静默交付
                    if (pages >= 0.985 && pages <= 1.0) {
                        fitNotice.value = '';
                        return;
                    }
                    if (pages > 1.0) {
                        // 超页：先退出填充态（fill 会忽略压缩档位，两者互斥），再压缩档位，压到底仍超则 AI 精简（最多一次）
                        if (fillMode.value) {
                            fillMode.value = false;
                            fillFactor.value = 1;
                            await renderResumePreview();
                            continue;
                        }
                        if (compactLevel.value < 5) {
                            compactLevel.value++;
                            await renderResumePreview();
                        } else if (!trimTried.value) {
                            // 已缩到最小字号(11.5px)仍超页：征询用户后 AI 精简（删次要内容）
                            if (confirm('内容已压缩到最小字号（11.5px）仍超出一页。是否允许 AI 精简次要内容（如自我评价、次要项目）以适配一页？')) {
                                trimTried.value = true;
                                fitNotice.value = '✂️ 内容超出较多，正在用 AI 精简…';
                                await trimToFit();
                            } else {
                                fitNotice.value = '⚠️ 内容仍超一页，请手动删减次要内容';
                                break;
                            }
                        } else {
                            break;
                        }
                        continue;
                    }
                    // 不足（<0.985）：用确定性二分求"最大不超一页"的 fillFactor
                    // （内容高度随 ff 基本单调，二分稳定收敛；替代原先"放大→超页→二分"的震荡式）
                    fillMode.value = true;
                    let lo = 1, hi = 1.6, best = 1, bestPages = getPages();
                    for (let i = 0; i < 10; i++) {
                        const mid = (lo + hi) / 2;
                        fillFactor.value = mid;
                        await renderResumePreview();
                        const p = getPages();
                        if (p > 1.0) { hi = mid; } else { best = mid; bestPages = p; lo = mid; }
                    }
                    fillFactor.value = best;
                    await renderResumePreview();
                    if (bestPages >= 0.985 && bestPages <= 1.0) { fitNotice.value = ''; return; }
                    // 二分后仍不足：AI 扩写兜底（最多一次，基于真实经历展开，不编造）
                    if (bestPages < 0.985 && !expandTried.value) {
                        expandTried.value = true;
                        fitNotice.value = '✍️ 内容偏少，正在用 AI 基于真实经历扩写…';
                        await expandToFit();
                        const after = getPages();
                        if (after >= 0.985 && after <= 1.0) { fitNotice.value = ''; return; }
                    } else if (bestPages < 0.985) {
                        break;
                    }
                }
                // 达到循环上限或已尝试兜底仍未收敛
                const finalPages = getPages();
                if (finalPages > 1.0) {
                    fitNotice.value = '⚠️ 内容仍超一页，请手动删减次要内容';
                } else if (finalPages < 0.9) {
                    fitNotice.value = '⚠️ 内容较少，建议在「经历管理」补充更多真实经历后重新生成';
                } else {
                    fitNotice.value = '';
                }
            } finally {
                fitAutoRun.value = false;
            }
        }
        // 简历预览：Shadow DOM 直接平铺渲染（无 iframe 框、完整显示、可编辑）
        async function renderResumePreview() {
            await nextTick();
            const container = document.getElementById('resumePreview');
            if (!container || !result.value || !result.value.resume_html) return;
            const doc = new DOMParser().parseFromString(result.value.resume_html, "text/html");
            const shadow = container.shadowRoot || container.attachShadow({mode: "open"});
            shadow.innerHTML = "";
            // 样式：body 选择器改为 :host（应用到预览容器），其余选择器在 shadow 内天然隔离
            doc.querySelectorAll("style").forEach(s => {
                const st = document.createElement("style");
                st.textContent = s.textContent.replace(/\bbody\b/g, ":host");
                shadow.appendChild(st);
            });
            // 注入 A4 适配覆盖样式（压缩档位 / 内容填充）
            const ov = document.createElement("style");
            ov.textContent = buildResumeOverrideCss(compactLevel.value, fillMode.value, fillFactor.value);
            shadow.appendChild(ov);
            // 内容包一层可编辑容器（保留预览中直接修改的能力），跳过 script
            const wrapper = document.createElement("div");
            wrapper.className = "resume-body";
            wrapper.setAttribute("contenteditable", "true");
            while (doc.body.firstChild) {
                const node = doc.body.firstChild;
                if (node.nodeName === "SCRIPT") { doc.body.removeChild(node); continue; }
                wrapper.appendChild(node);
            }
            // 外面套定位容器，承载 A4 分页参考线（参考线在 wrapper 外，导出时不带出）
            const shell = document.createElement("div");
            shell.className = "preview-shell";
            shell.appendChild(wrapper);
            shadow.appendChild(shell);
            drawPageGuides(wrapper);
            wrapper.addEventListener('input', () => {
                drawPageGuides(wrapper);
                updatePageMeta();
            });
            updatePageMeta();
        }
        // 简历质量诊断（客观分 + AI找茬）
        const diagnosing = ref(false);
        const diagnosis = ref(null);

        async function diagnoseResume() {
            if (!result.value || !result.value.resume_html) { alert('请先生成简历'); return; }
            diagnosing.value = true;
            diagnosis.value = null;
            try {
                diagnosis.value = await API.post('/api/resumes/diagnose', {
                    resume_html: result.value.resume_html,
                    jd_text: jdText.value,
                });
            } catch(e) { alert('诊断失败: ' + e.message); }
            diagnosing.value = false;
        }

        // 加载模板列表
        async function loadTemplates() {
            try {
                const data = await API.get('/api/templates');
                // 保持前两个内置模板不变，追加自定义模板
                const builtins = [
                    {id: 'default', name: '📋 项目经历优先（默认）', is_builtin: true},
                    {id: 'education', name: '🎓 教育背景优先', is_builtin: true},
                ];
                const customs = data.filter(t => !t.is_builtin).map(t => ({
                    id: String(t.id),
                    name: '📁 ' + t.name,
                    is_builtin: false,
                }));
                templateList.value = [...builtins, ...customs];
            } catch(e) {
                console.error('加载模板列表失败:', e);
            }
        }

        // 自定义下拉框状态
        const tplDropdownOpen = ref(false);
        function toggleTplDropdown() {
            tplDropdownOpen.value = !tplDropdownOpen.value;
        }

        // 在下拉框内删除指定模板
        async function deleteTemplateById(tid) {
            if (!confirm('确定要删除这个模板吗？')) return;
            try {
                await API.del('/api/templates/' + tid);
                if (templateType.value === String(tid)) {
                    templateType.value = 'default';
                }
                await loadTemplates();
            } catch(e) {
                alert('删除失败: ' + e.message);
            }
        }

        // 删除当前选中的自定义模板
        async function deleteSelectedTemplate() {
            const tid = templateType.value;
            if (!tid || tid === 'default' || tid === 'education') return;

            if (!confirm('确定要删除这个模板吗？此操作不可恢复。')) return;

            try {
                await API.del('/api/templates/' + tid);
                templateType.value = 'default';
                await loadTemplates();
            } catch(e) {
                alert('删除失败: ' + e.message);
            }
        }

        // 导入自定义模板
        async function importTemplate(event) {
            const file = event.target.files[0];
            if (!file) return;

            const name = file.name.toLowerCase();
            const validExts = ['.html', '.htm', '.docx', '.doc', '.pdf'];
            if (!validExts.some(ext => name.endsWith(ext))) {
                alert('只支持 HTML(.html) / Word(.docx) / PDF 格式');
                event.target.value = '';
                return;
            }

            const isHtml = name.endsWith('.html') || name.endsWith('.htm');

            if (!isHtml) {
                const ok = confirm(
                    '⚠️ 注意：Word/PDF 模板可能无法完美保留颜色和排版。\n\n' +
                    '推荐使用 HTML 格式的模板（效果最好，格式100%保留）。\n\n' +
                    '你可以：\n' +
                    '1. 用 Word 打开模板 → 另存为 → 网页(.html)\n' +
                    '2. 或使用内置模板修改\n\n' +
                    '是否继续导入此 Word/PDF 文件？'
                );
                if (!ok) { event.target.value = ''; return; }
            }

            if (file.size > 10 * 1024 * 1024) {
                alert('文件大小不能超过 10MB');
                event.target.value = '';
                return;
            }

            try {
                // 通过 FormData 上传文件，服务端自动识别格式并转换
                const formData = new FormData();
                formData.append('file', file);

                const r = await fetch('/api/templates/import-file', {
                    method: 'POST',
                    body: formData,
                });
                if (!r.ok) {
                    const err = await r.json();
                    throw new Error(err.detail || '上传失败');
                }
                const result = await r.json();

                // 刷新模板列表
                await loadTemplates();

                // 自动选中刚导入的模板
                if (result.id) {
                    templateType.value = String(result.id);
                }

                const extLabel = name.endsWith('.pdf') ? 'PDF' : name.endsWith('.docx') || name.endsWith('.doc') ? 'Word' : 'HTML';
                alert(`模板导入成功（${extLabel} → HTML）：` + file.name);
            } catch (e) {
                alert('模板导入失败：' + e.message);
            }
            event.target.value = '';
        }

        // ======== AI简历修改 ========
        const reviseInstruction = ref('');
        const revising = ref(false);
        const hasRevision = ref(false);
        const reviseError = ref('');
        const previousResumeHtml = ref('');

        // 一键按诊断结果修改：把 AI 找茬的 issue+fix 转成修改指令，填入修改框并自动触发
        function applyDiagnosisToRevise() {
            if (!diagnosis.value || !diagnosis.value.ai_findings || !diagnosis.value.ai_findings.suggestions || !diagnosis.value.ai_findings.suggestions.length) {
                alert('暂无诊断建议，请先点击「AI质量诊断」');
                return;
            }
            const tips = diagnosis.value.ai_findings.suggestions
                .map((s, i) => (i + 1) + '. ' + [s.area, s.issue, s.fix].filter(Boolean).join('：') + (s.fix ? '（改法：' + s.fix + '）' : ''))
                .join('\n');
            reviseInstruction.value = '请根据以下质量诊断逐条修改简历（保留原意，只改该改的，不要编造事实）。重要约束：总篇幅必须控制在一页 A4 内，若会超页，优先精简自我评价/次要项目，不要无脑扩写。\n' + tips;
            hasRevision.value = false;
            reviseError.value = '';
            // 滚动到修改面板并自动触发修改
            const panel = document.querySelector('.revise-panel') || document.getElementById('revisePanel');
            if (panel) panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
            sendRevise();
        }

        async function sendRevise() {
            if (!reviseInstruction.value.trim()) return;
            if (!result.value || !result.value.resume_html) {
                reviseError.value = '请先生成简历';
                return;
            }
            revising.value = true;
            reviseError.value = '';
            hasRevision.value = false;
            try {
                const currentHtml = result.value.resume_html;
                const r = await API.post('/api/resumes/revise', {
                    current_html: currentHtml,
                    instruction: reviseInstruction.value.trim(),
                });
                previousResumeHtml.value = currentHtml;
                result.value.resume_html = r.revised_html;
                // 刷新预览：展示 <del>/<ins> 红绿 diff
                await renderResumePreview();
                // 修改后自动压缩（仅 CSS，保留 diff；超页才降档）
                await compressToFit();
                hasRevision.value = true;
                reviseInstruction.value = '';
            } catch(e) {
                reviseError.value = '修改失败: ' + e.message;
            }
            revising.value = false;
        }

        async function acceptRevision() {
            if (!result.value || !result.value.resume_html) return;
            try {
                const r = await API.post('/api/resumes/accept-revision', {
                    html_content: result.value.resume_html,
                });
                result.value.resume_html = r.clean_html;
                await renderResumePreview();
                hasRevision.value = false;
                previousResumeHtml.value = '';
                reviseInstruction.value = '';
                reviseError.value = '';
                // 接受修改后重置回正常字号，重新完整适配一页（能大则大，含 AI 精简兜底）
                compactLevel.value = 0;
                fillMode.value = false;
                fillFactor.value = 1;
                await autoFitToPage();
            } catch(e) {
                reviseError.value = '接受修改失败: ' + e.message;
            }
        }

        function rejectRevision() {
            if (previousResumeHtml.value) {
                result.value.resume_html = previousResumeHtml.value;
                renderResumePreview();
                previousResumeHtml.value = '';
                hasRevision.value = false;
                reviseInstruction.value = '';
                reviseError.value = '';
            }
        }

        async function exportFile() {
            if (!result.value || !result.value.resume_html) {
                alert('请先生成简历'); return;
            }
            // 取预览中的最新内容（含用户直接编辑），无预览则用生成结果
            let html = result.value.resume_html;
            const container = document.getElementById('resumePreview');
            if (container && container.shadowRoot) {
                const wrapper = container.shadowRoot.querySelector('.resume-body');
                if (wrapper) {
                    const doc = new DOMParser().parseFromString(result.value.resume_html, "text/html");
                    const headHtml = doc.querySelector('head') ? doc.querySelector('head').innerHTML : '';
                    // 把预览中应用的压缩/填充样式一并带入打印（:host/.resume-body 换成 body，打印 iframe 无 Shadow DOM）
                    let overrideCss = '';
                    try {
                        overrideCss = buildResumeOverrideCss(compactLevel.value, fillMode.value, fillFactor.value)
                            .replace(/:host/g, 'body')
                            .replace(/\.resume-body/g, 'body')
                            // 去掉预览专用的分页参考线样式（打印不需要）
                            .split('\n')
                            .filter(l => !l.includes('preview-shell') && !l.includes('resume-page-guide'))
                            .join('\n')
                            // 打印边距兜底：恢复 body 上下 0.7cm / 左右 0.8cm（覆盖模板 @media print 对 body padding 的误伤）
                            + '\nbody { margin: 0 !important; padding: 0.7cm 0.8cm !important; }';
                    } catch(e) { overrideCss = ''; }
                    html = '<!DOCTYPE html><html><head>' + headHtml + '\n<style>' + overrideCss + '</style></head><body contenteditable="true">' + wrapper.innerHTML + '</body></html>';
                }
            }
            // 直接触发浏览器打印 → 另存为PDF（中文完美渲染，格式与预览一致）
            const pf = document.getElementById('resumePrintFrame');
            if (!pf) { alert('请在预览框中按 Ctrl+P → 另存为PDF'); return; }
            pf.srcdoc = '';
            setTimeout(() => {
                pf.srcdoc = html;
                pf.onload = () => { pf.contentWindow.focus(); pf.contentWindow.print(); };
            }, 60);
        }
        // ======== 公司洞察 ========
        const companySearchName = ref('');
        const companySearchLocation = ref('');
        const companySearching = ref(false);
        const companyReport = ref(null);
        const companySearchError = ref('');

        async function searchCompany() {
            if (!companySearchName.value.trim()) return;
            companySearching.value = true;
            companyReport.value = null;
            companySearchError.value = '';
            try {
                const r = await API.post('/api/company/search', {
                    company_name: companySearchName.value.trim(),
                    location: companySearchLocation.value.trim(),
                });
                if (r.success) {
                    companyReport.value = r;
                } else {
                    companySearchError.value = r.error || '分析失败';
                }
            } catch(e) {
                companySearchError.value = '请求失败: ' + e.message;
            }
            companySearching.value = false;
        }

        function renderMarkdown(text) {
            if (!text) return '';
            // 简单markdown渲染
            let html = text
                .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                .replace(/^### (.+)$/gm, '<h4>$1</h4>')
                .replace(/^## (.+)$/gm, '<h3>$1</h3>')
                .replace(/^# (.+)$/gm, '<h2>$1</h2>')
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/^- (.+)$/gm, '<li>$1</li>')
                .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>');
            html = '<p>' + html + '</p>';
            return html;
        }

        // ======== 模拟面试 ========
        const interviewSessionId = ref('');
        const interviewCurrentQuestion = ref('');
        const interviewCurrentPurpose = ref('');
        const interviewCurrentIndex = ref(0);
        const interviewTotalQuestions = ref(0);
        const interviewIsFollowup = ref(false);
        const interviewAnswer = ref('');
        const interviewHistory = ref([]);
        const interviewComplete = ref(false);
        const interviewEvaluation = ref(null);
        const interviewLoading = ref(false);
        const interviewSubmitting = ref(false);

        async function startInterview() {
            if (!jdText.value.trim()) { alert('请先在「简历生成」Tab粘贴目标岗位JD'); return; }
            interviewLoading.value = true;
            try {
                const r = await API.post('/api/interview/start', { jd_text: jdText.value });
                interviewSessionId.value = r.session_id;
                interviewCurrentQuestion.value = r.question;
                interviewCurrentPurpose.value = r.purpose || '';
                interviewCurrentIndex.value = r.current_index;
                interviewTotalQuestions.value = r.total_questions;
                interviewIsFollowup.value = false;
                interviewHistory.value = [];
                interviewComplete.value = false;
                interviewEvaluation.value = null;
                currentTab.value = 'interview';
                // 语音模式：朗读开场白和首题
                if (voiceEnabled.value) {
                    initRecognition();
                    setTimeout(() => {
                        speakInterviewStart(r.total_questions);
                        setTimeout(() => speakText(r.question), 1000);
                    }, 500);
                }
            } catch(e) { alert('面试启动失败: ' + e.message); }
            interviewLoading.value = false;
        }

        async function submitInterviewAnswer() {
            if (!interviewAnswer.value.trim() || !interviewSessionId.value) return;
            interviewSubmitting.value = true;
            const answer = interviewAnswer.value.trim();
            interviewAnswer.value = '';

            try {
                const r = await API.post('/api/interview/answer', {
                    session_id: interviewSessionId.value,
                    answer: answer,
                });

                if (r.is_complete) {
                    interviewComplete.value = true;
                    interviewEvaluation.value = r.evaluation;
                    interviewSessionId.value = '';
                } else {
                    const historyItem = {
                        question: interviewCurrentQuestion.value,
                        answer: answer,
                        ai_text: r.ai_text || '',
                        followup: r.is_followup ? r.question : '',
                    };
                    if (r.is_followup) {
                        interviewIsFollowup.value = true;
                    } else {
                        interviewIsFollowup.value = false;
                        interviewCurrentIndex.value = r.current_index;
                    }
                    interviewHistory.value.push(historyItem);
                    interviewCurrentQuestion.value = r.question;
                    interviewCurrentPurpose.value = r.purpose || '';
                }
                // 语音模式：朗读下一题/追问
                if (voiceEnabled.value && !r.is_complete) {
                    setTimeout(() => speakText(r.question), 300);
                }
            } catch(e) { alert('提交失败: ' + e.message); }
            interviewSubmitting.value = false;
        }

        async function endInterview() {
            if (!interviewSessionId.value) return;
            if (!confirm('确认结束面试？结束后将生成评估报告。')) return;
            try {
                const r = await API.post('/api/interview/end', { session_id: interviewSessionId.value });
                interviewComplete.value = true;
                interviewEvaluation.value = r.evaluation;
                interviewSessionId.value = '';
            } catch(e) { alert('结束面试失败: ' + e.message); }
        }

        function resetInterview() {
            stopVoiceRecognition();
            interviewSessionId.value = '';
            interviewCurrentQuestion.value = '';
            interviewCurrentPurpose.value = '';
            interviewCurrentIndex.value = 0;
            interviewTotalQuestions.value = 0;
            interviewIsFollowup.value = false;
            interviewAnswer.value = '';
            interviewHistory.value = [];
            interviewComplete.value = false;
            interviewEvaluation.value = null;
        }

        // ======== 语音模式 ========
        const voiceEnabled = ref(false);
        const voiceStatus = ref('');  // listening | thinking | speaking | null
        let recognition = null;
        let silenceTimer = null;
        let finalTranscript = '';

        function initRecognition() {
            if (recognition) return;
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert('当前浏览器不支持语音识别，请使用Chrome浏览器');
                voiceEnabled.value = false;
                return;
            }
            recognition = new SpeechRecognition();
            recognition.lang = 'zh-CN';
            recognition.interimResults = true;
            recognition.continuous = true;
            recognition.maxAlternatives = 1;

            recognition.onresult = (event) => {
                let interim = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const r = event.results[i];
                    if (r.isFinal) {
                        finalTranscript += r[0].transcript;
                    } else {
                        interim += r[0].transcript;
                    }
                }
                interviewAnswer.value = finalTranscript + interim;
                // 重置静默计时器
                clearTimeout(silenceTimer);
                silenceTimer = setTimeout(() => {
                    if (finalTranscript.trim() && voiceEnabled.value) {
                        stopVoiceRecognition();
                        voiceStatus.value = 'thinking';
                        submitInterviewAnswer();
                    }
                }, 2500);  // 2.5秒不说话 → 自动提交
            };

            recognition.onerror = (event) => {
                console.error('Speech error:', event.error);
                if (event.error === 'no-speech' || event.error === 'aborted') {
                    voiceStatus.value = 'listening';
                    // 静默重启监听
                    setTimeout(() => { if (voiceEnabled.value && interviewSessionId.value) startListening(); }, 1000);
                } else if (event.error === 'not-allowed') {
                    alert('请允许麦克风权限');
                    voiceStatus.value = '';
                }
            };

            recognition.onend = () => {
                if (voiceStatus.value === 'listening') {
                    // 意外停止时重启
                    setTimeout(() => {
                        if (voiceEnabled.value && interviewSessionId.value && !interviewComplete.value) {
                            startListening();
                        }
                    }, 500);
                }
            };
        }

        function startListening() {
            if (!recognition) initRecognition();
            if (!recognition) return;
            finalTranscript = '';
            interviewAnswer.value = '';
            voiceStatus.value = 'listening';
            try {
                recognition.start();
            } catch(e) {
                // 可能已经在监听中
            }
        }

        function stopVoiceRecognition() {
            clearTimeout(silenceTimer);
            if (recognition) {
                try { recognition.stop(); } catch(e) {}
            }
            voiceStatus.value = '';
        }

        function speakText(text) {
            if (!voiceEnabled.value) return;
            const synth = window.speechSynthesis;
            if (!synth) return;
            synth.cancel(); // 取消之前的朗读
            voiceStatus.value = 'speaking';
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'zh-CN';
            utterance.rate = 0.95;
            utterance.pitch = 1.0;
            // 选择最佳中文语音：优先 Huihui(女声) > Yaoyao(女声) > Kangkang(男声) > 任意中文
            const voices = synth.getVoices();
            const zhVoice = voices.find(v => v.name.includes('Huihui'))
                || voices.find(v => v.name.includes('Yaoyao'))
                || voices.find(v => v.name.includes('Kangkang'))
                || voices.find(v => v.lang.startsWith('zh-CN'))
                || voices.find(v => v.lang.startsWith('zh'))
                || voices[0];
            if (zhVoice) utterance.voice = zhVoice;
            utterance.onend = () => {
                voiceStatus.value = '';
                // 朗读完后开始听
                if (voiceEnabled.value && interviewSessionId.value && !interviewComplete.value) {
                    startListening();
                }
            };
            synth.speak(utterance);
        }

        // 开场白朗读
        function speakInterviewStart(totalQuestions) {
            if (!voiceEnabled.value) return;
            const text = `面试开始，本次共${totalQuestions}道题。请认真回答每一个问题，尽量详细。`;
            speakText(text);
        }

        // ======== 投递记录 ========
        const deliverySearch = ref('');
        const deliveryRecords = ref([]);
        const deliveryPage = ref(1);
        const deliveryPageSize = ref(20);
        const deliveryTotal = ref(0);
        const deliveryDetail = ref(null);

        async function loadDeliveryRecords(page = 1) {
            deliveryPage.value = page;
            try {
                const params = new URLSearchParams({
                    search: deliverySearch.value,
                    page: String(page),
                    page_size: String(deliveryPageSize.value),
                });
                const r = await API.get('/api/delivery/records?' + params.toString());
                deliveryRecords.value = r.records || [];
                deliveryTotal.value = r.total || 0;
            } catch(e) { console.error('加载投递记录失败:', e); }
        }

        async function viewDeliveryDetail(id) {
            try {
                deliveryDetail.value = await API.get('/api/delivery/records/' + id);
            } catch(e) { alert('加载详情失败: ' + e.message); }
        }

        async function deleteDeliveryRecord(id) {
            if (!confirm('确认删除此投递记录？')) return;
            try {
                await API.del('/api/delivery/records/' + id);
                await loadDeliveryRecords(deliveryPage.value);
            } catch(e) { alert('删除失败: ' + e.message); }
        }

        async function submitDelivery() {
            if (!result.value || !result.value.resume_html) {
                alert('请先生成简历'); return;
            }
            const cn = (jdAnalysis.value && jdAnalysis.value.company_name) ? jdAnalysis.value.company_name : '';
            const jt = (jdAnalysis.value && jdAnalysis.value.job_title) ? jdAnalysis.value.job_title : '';

            try {
                const r = await API.post('/api/delivery/submit', {
                    resume_html: result.value.resume_html,
                    jd_text: jdText.value,
                    company_name: cn,
                    job_title: jt,
                });
                if (r.success) {
                    let msg = '✅ 已记录到「我的投递」！' + '\n' + '\n';
                    if (r.company_name) msg += '公司：' + r.company_name + '\n';
                    if (r.job_title) msg += '岗位：' + r.job_title + '\n';
                    msg += '时间：' + r.delivery_time + '\n' + '\n';
                    msg += '投递记录和简历快照已保存，可在「我的投递」Tab 随时查看。\n';
                    msg += '真正投递：用「🖨 打印/导出PDF」导出简历，到招聘平台上传即可。';
                    if (jdText.value) {
                        const urlMatch = jdText.value.match(/https?:\/\/[^\s一-鿿]+/);
                        if (urlMatch) {
                            msg += '\n' + '\n检测到JD中的链接，是否打开投递页面？';
                            if (confirm(msg)) {
                                window.open(urlMatch[0], '_blank');
                            }
                        } else {
                            msg += '\n' + '\n未检测到招聘链接，请打开招聘App对应岗位页面投递。';
                            alert(msg);
                        }
                    } else {
                        alert(msg);
                    }                } else {
                    alert('投递失败: ' + (r.error || '未知错误'));
                }
            } catch(e) { alert('投递请求失败: ' + e.message); }
        }

        // ======== 求职材料（求职信 + 面试题） ========
        const coverLetter = ref('');
        const genCoverLoading = ref(false);
        const interviewQs = ref(null);
        const genIntvLoading = ref(false);

        async function genCoverLetter() {
            if (!jdText.value.trim()) { alert('请先在「简历生成」Tab粘贴JD'); return; }
            genCoverLoading.value = true;
            try {
                const r = await API.post('/api/resumes/cover-letter', {jd_text: jdText.value});
                coverLetter.value = r.cover_letter;
            } catch(e) { alert('生成失败: ' + e.message); }
            genCoverLoading.value = false;
        }

        async function genInterview() {
            if (!jdText.value.trim()) { alert('请先在「简历生成」Tab粘贴JD'); return; }
            genIntvLoading.value = true;
            try {
                interviewQs.value = await API.post('/api/resumes/interview-questions', {jd_text: jdText.value});
            } catch(e) { alert('生成失败: ' + e.message); }
            genIntvLoading.value = false;
        }

        function copyText(text) {
            navigator.clipboard.writeText(text).then(
                () => alert('已复制到剪贴板'),
                () => alert('复制失败，请手动选中文字 Ctrl+C')
            );
        }

        // ======== AI 采集提示词（档2）========
        async function copyCollectPrompt() {
            collectingPrompt.value = true;
            try {
                const r = await API.get('/api/experiences/collect-prompt');
                if (r && r.prompt) {
                    await navigator.clipboard.writeText(r.prompt);
                    alert('✅ 采集提示词已复制到剪贴板！\n\n用法：\n1. 打开豆包/任意大模型\n2. 粘贴这段提示词\n3. 按提示词说出你的经历\n4. 把 AI 返回的 JSON 复制回来，粘到下方输入框\n5. 点「AI 解析并导入」');
                } else {
                    alert('获取提示词失败，请重试');
                }
            } catch(e) {
                alert('获取提示词失败: ' + e.message);
            }
            collectingPrompt.value = false;
        }

        // ======== 已有简历文件导入（方案B）========
        async function importResumeFile(event) {
            const file = event.target.files && event.target.files[0];
            if (!file) return;
            fileImporting.value = true;
            try {
                const r = await API.upload('/api/experiences/import-file', file);
                if (r && r.text) {
                    pasteText.value = r.text;
                    alert('✅ 已从「' + (r.filename || file.name) + '」提取到 ' + r.text.length + ' 字，填入下方输入框。\n\n点「✨ AI 解析并导入」完成结构化导入。\n\n若文字缺失/乱码，说明是扫描件或图片型 PDF，暂不支持，请改用「方式二」采集。');
                }
            } catch(e) {
                alert('导入失败: ' + e.message);
            }
            fileImporting.value = false;
            event.target.value = '';
        }

        // ======== 初始化 ========
        onMounted(async () => {
            await loadExperiences();
            await loadTemplates();
            // 点击外部关闭自定义下拉
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.custom-select')) {
                    tplDropdownOpen.value = false;
                }
            });
        });

        return {
            tabs, coreTabs, extraTabs, currentTab, switchTab,
            jumpToCompanyTab, jumpToInterviewTab, quickAnalyzeCompany,
            basicInfo, modules, selfEval, pasteText, parsing, photoPreviewUrl,
            getPhotoUrl,
            saveBasicInfo, saveSelfEval, formatItem,
            addingModule, startAddItem, cancelAdd, confirmAddItem,
            editingId, editFields, getFields, startEdit, cancelEdit, confirmEdit,
            deleteItem, loadExperiences, clearAllExperience,
            otherModules, moveItem,
            uploadPhoto, removePhoto, parseText,
            resumeFileInput, fileImporting, collectingPrompt,
            copyCollectPrompt, importResumeFile,
            jdText, templateType, tplFileInput, templateList, generating, result,
            toggleTplDropdown, tplDropdownOpen, deleteTemplateById, deleteSelectedTemplate,
            importTemplate,
            jdAnalysis, analyzingJD, analyzeJD,
            jdIndustry, industryOptions, industryAnalysis, analyzingIndustry,
            industryConfidenceClass, industryConfidenceLabel,
            diagnosing, diagnosis, diagnoseResume, applyDiagnosisToRevise,
            companyResult, companyLoading, analyzeCompany, quickAnalyzeCompany,
            rawCompanyData, dataInterpretation, interpreting, interpretData,
            generateResume, exportFile,
            matchPreview, matchPreviewLoading, refreshMatchPreview,
            matchPreviewScore, matchPreviewHitText,
            matchPreviewCardClass, matchPreviewLevelLabel, matchPreviewLevelTag,
            matchPreviewBarClass, matchPreviewBarWidth,
            matchPreviewSuggestions, matchPreviewUnfillableText,
            compactLevel, fillMode, fillFactor, pageCount, pageOverflow,
            fitNotice, fitNoticeClass, autoFitToPage,
            matchCardClass, matchCardTitle,
            reviseInstruction, revising, hasRevision, reviseError,
            sendRevise, acceptRevision, rejectRevision,
            coverLetter, genCoverLoading, genCoverLetter,
            interviewQs, genIntvLoading, genInterview, copyText, renderMarkdown,
            // 公司洞察
            companySearchName, companySearchLocation, companySearching, companyReport, companySearchError,
            searchCompany,
            // 面试准备
            interviewSessionId, interviewCurrentQuestion, interviewCurrentPurpose,
            interviewCurrentIndex, interviewTotalQuestions, interviewIsFollowup,
            interviewAnswer, interviewHistory, interviewComplete, interviewEvaluation,
            interviewLoading, interviewSubmitting,
            voiceEnabled, voiceStatus,
            startInterview, submitInterviewAnswer, endInterview, resetInterview,
            // 投递记录
            deliverySearch, deliveryRecords, deliveryPage, deliveryPageSize, deliveryTotal,
            deliveryDetail,
            loadDeliveryRecords, viewDeliveryDetail, deleteDeliveryRecord, submitDelivery,
        };
    }
}).mount('#app');
