const { createApp, ref, reactive, onMounted } = Vue;

createApp({
    setup() {
        const tabs = [
            {id: 'import', label: '🤖 AI导入'},
            {id: 'experience', label: '📝 经历管理'},
            {id: 'generate', label: '🎯 简历生成'},
            {id: 'company', label: '🏢 公司洞察'},
            {id: 'interview', label: '🎤 面试准备'},
            {id: 'delivery', label: '📬 我的投递'},
        ];
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
        ]);
        const selfEval = reactive({content:''});
        const pasteText = ref('');
        const parsing = ref(false);
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
            if (!item.name && !item.school && !item.company) {
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
                if (r.basic_info && r.basic_info.name) {
                    await API.post('/api/experiences/basic-info', r.basic_info);
                }
                for (const edu of (r.education || [])) {
                    await API.post('/api/experiences/education', edu); count++;
                }
                // 兼容 work_experience 和 internships
                const workExps = r.work_experience || r.internships || [];
                for (const exp of workExps) {
                    await API.post('/api/experiences/internships', exp); count++;
                }
                for (const proj of (r.projects || [])) {
                    await API.post('/api/experiences/projects', proj); count++;
                }
                for (const skill of (r.skills || [])) {
                    await API.post('/api/experiences/skills', skill); count++;
                }
                for (const award of (r.awards || [])) {
                    await API.post('/api/experiences/awards', award); count++;
                }
                if (r.self_evaluation && r.self_evaluation.content) {
                    await API.post('/api/experiences/self-evaluation', r.self_evaluation);
                }
                await loadExperiences();
                pasteText.value = '';
                alert(`AI 解析完成！已导入 ${count} 条经历到各模块\n\n请逐模块检查信息是否准确。`);
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

        // JD分析
        const jdAnalysis = ref(null);
        const analyzingJD = ref(false);

        async function analyzeJD() {
            if (!jdText.value.trim()) return;
            analyzingJD.value = true;
            try {
                jdAnalysis.value = await API.post('/api/jd/clean', {jd_text: jdText.value});
            } catch(e) { alert('JD分析失败: ' + e.message); }
            analyzingJD.value = false;
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

        async function generateResume() {
            if (!jdText.value.trim()) { alert('请先粘贴目标岗位的JD'); return; }
            generating.value = true;
            result.value = null;
            try {
                result.value = await API.post('/api/resumes/generate', {
                    jd_text: jdText.value,
                    template_type: templateType.value
                });
                currentTab.value = 'generate';
            } catch(e) {
                alert('简历生成失败: ' + e.message + '\n\n可能原因: 1) 经历库为空 2) API Key未配置 3) 网络问题');
            }
            generating.value = false;
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
                hasRevision.value = false;
                previousResumeHtml.value = '';
                reviseInstruction.value = '';
                reviseError.value = '';
            } catch(e) {
                reviseError.value = '接受修改失败: ' + e.message;
            }
        }

        function rejectRevision() {
            if (previousResumeHtml.value) {
                result.value.resume_html = previousResumeHtml.value;
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
            // 直接触发浏览器打印 → 另存为PDF（中文完美渲染，格式与预览一致）
            const iframe = document.getElementById('resumeFrame');
            if (iframe && iframe.contentWindow) {
                iframe.contentWindow.focus();
                iframe.contentWindow.print();
            } else {
                alert('请在预览框中按 Ctrl+P → 另存为PDF');
            }
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
                    if (r.is_followup) {
                        interviewIsFollowup.value = true;
                        interviewHistory.value.push({ answer: answer, followup: r.question });
                    } else {
                        interviewIsFollowup.value = false;
                        interviewHistory.value.push({ answer: answer, followup: '' });
                        interviewCurrentIndex.value = r.current_index;
                    }
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
                    await navigator.clipboard.writeText(
                        new DOMParser().parseFromString(result.value.resume_html, 'text/html').body.textContent || ''
                    ).catch(() => {});
                    let msg = '✅ 投递成功！\n\n';
                    if (r.company_name) msg += '公司：' + r.company_name + '\n';
                    if (r.job_title) msg += '岗位：' + r.job_title + '\n';
                    msg += '时间：' + r.delivery_time + '\n\n';
                    msg += '简历内容已复制到剪贴板。';
                    if (jdText.value) {
                        const urlMatch = jdText.value.match(/https?:\/\/[^\s一-鿿]+/);
                        if (urlMatch) {
                            msg += '\n\n检测到JD中的链接，是否打开投递页面？';
                            if (confirm(msg)) {
                                window.open(urlMatch[0], '_blank');
                            }
                        } else {
                            msg += '\n\n未检测到投递链接，请手动打开招聘App对应岗位页面进行投递。';
                            alert(msg);
                        }
                    } else {
                        alert(msg);
                    }
                } else {
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
            tabs, currentTab, switchTab,
            jumpToCompanyTab, jumpToInterviewTab, quickAnalyzeCompany,
            basicInfo, modules, selfEval, pasteText, parsing, photoPreviewUrl,
            getPhotoUrl,
            saveBasicInfo, saveSelfEval, formatItem,
            addingModule, startAddItem, cancelAdd, confirmAddItem,
            editingId, editFields, getFields, startEdit, cancelEdit, confirmEdit,
            deleteItem, loadExperiences,
            uploadPhoto, removePhoto, parseText,
            jdText, templateType, tplFileInput, templateList, generating, result,
            toggleTplDropdown, tplDropdownOpen, deleteTemplateById, deleteSelectedTemplate,
            jdAnalysis, analyzingJD, analyzeJD,
            companyResult, companyLoading, analyzeCompany, quickAnalyzeCompany,
            rawCompanyData, dataInterpretation, interpreting, interpretData,
            generateResume, exportFile,
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
