const { createApp, ref, reactive, onMounted } = Vue;

createApp({
    setup() {
        const tabs = [
            {id: 'experience', label: '📝 经历管理'},
            {id: 'generate', label: '🎯 简历生成'},
            {id: 'extra', label: '📋 求职材料'},
        ];
        const currentTab = ref('experience');

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
        });

        return {
            tabs, currentTab,
            basicInfo, modules, selfEval, pasteText, parsing, photoPreviewUrl,
            getPhotoUrl,
            saveBasicInfo, saveSelfEval, formatItem,
            addingModule, startAddItem, cancelAdd, confirmAddItem,
            editingId, editFields, getFields, startEdit, cancelEdit, confirmEdit,
            deleteItem, loadExperiences,
            uploadPhoto, removePhoto, parseText,
            jdText, templateType, generating, result,
            jdAnalysis, analyzingJD, analyzeJD,
            companyResult, companyLoading, analyzeCompany,
            rawCompanyData, dataInterpretation, interpreting, interpretData,
            generateResume, exportFile,
            coverLetter, genCoverLoading, genCoverLetter,
            interviewQs, genIntvLoading, genInterview, copyText,
        };
    }
}).mount('#app');
