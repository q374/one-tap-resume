const { createApp, ref, reactive, onMounted } = Vue;

createApp({
    setup() {
        const tabs = [
            {id: 'experience', label: '经历管理'},
            {id: 'generate', label: '简历生成'},
            {id: 'ai-chat', label: 'AI修改'},
            {id: 'templates', label: '模板'},
        ];
        const currentTab = ref('experience');

        // === 经历管理 ===
        const basicInfo = reactive({name:'', phone:'', email:'', age:'', job_target:'', photo_path:''});
        const modules = reactive([
            {key:'education', label:'教育背景', items:[]},
            {key:'internships', label:'实习经历', items:[]},
            {key:'projects', label:'项目经历', items:[]},
            {key:'skills', label:'技能', items:[]},
            {key:'awards', label:'获奖情况', items:[]},
        ]);
        const selfEval = reactive({content:''});
        const pasteText = ref('');
        const parsing = ref(false);

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
            } catch(e) { console.error(e); }
        }

        async function saveBasicInfo() { await API.post('/api/experiences/basic-info', {...basicInfo}); alert('已保存'); }
        async function saveSelfEval() { await API.post('/api/experiences/self-evaluation', {content: selfEval.content}); alert('已保存'); }

        function formatItem(item) {
            const vals = Object.entries(item).filter(([k,v]) => typeof v === 'string' && v && k !== 'id' && k !== 'sort_order');
            return vals.slice(0, 4).map(([k,v]) => v).join(' | ');
        }

        async function editItem(modKey, item) {
            const fields = Object.keys(item).filter(k => k !== 'id' && k !== 'sort_order' && typeof item[k] === 'string');
            let promptStr = fields.map(f => item[f] || '').join(' | ');
            promptStr = prompt(`编辑 (${fields.join(',')}):`, promptStr);
            if (!promptStr) return;
            item[fields[0]] = promptStr;
            await API.put(`/api/experiences/${modKey}/${item.id}`, item);
            await loadExperiences();
        }

        async function deleteItem(modKey, id) {
            if (!confirm('确认删除？')) return;
            await API.del(`/api/experiences/${modKey}/${id}`);
            await loadExperiences();
        }

        async function addItem(modKey) {
            const emptyItem = {name:'', sort_order: 0};
            await API.post(`/api/experiences/${modKey}`, emptyItem);
            await loadExperiences();
        }

        async function parseText() {
            if (!pasteText.value.trim()) return;
            parsing.value = true;
            try {
                const r = await API.post('/api/experiences/parse-text', {text: pasteText.value});
                if (r.basic_info && r.basic_info.name) await API.post('/api/experiences/basic-info', r.basic_info);
                for (const edu of (r.education || [])) await API.post('/api/experiences/education', edu);
                for (const intern of (r.internships || [])) await API.post('/api/experiences/internships', intern);
                for (const proj of (r.projects || [])) await API.post('/api/experiences/projects', proj);
                for (const skill of (r.skills || [])) await API.post('/api/experiences/skills', skill);
                for (const award of (r.awards || [])) await API.post('/api/experiences/awards', award);
                if (r.self_evaluation && r.self_evaluation.content) await API.post('/api/experiences/self-evaluation', r.self_evaluation);
                await loadExperiences();
                pasteText.value = '';
                alert('AI 解析完成，经历已自动导入！');
            } catch(e) {
                alert('解析失败: ' + e.message);
            }
            parsing.value = false;
        }

        // === 简历生成 ===
        const jdText = ref('');
        const templateType = ref('default');
        const generating = ref(false);
        const result = ref(null);
        const ocrText = ref('');

        async function generateResume() {
            if (!jdText.value.trim()) { alert('请先粘贴 JD'); return; }
            generating.value = true;
            result.value = null;
            try {
                result.value = await API.post('/api/resumes/generate', {
                    jd_text: jdText.value,
                    template_type: templateType.value
                });
                currentTab.value = 'generate';
            } catch(e) {
                alert('生成失败: ' + e.message);
            }
            generating.value = false;
        }

        async function handleOCRUpload(e) {
            const files = e.target.files;
            if (!files.length) return;
            const formData = new FormData();
            for (const f of files) formData.append('files', f);
            const r = await fetch('/api/ocr/extract', {method:'POST', body: formData});
            const data = await r.json();
            ocrText.value = data.merged_text;
        }

        async function exportPDF() {
            if (!result.value || !result.value.resume_html) return;
            try {
                const r = await fetch('/api/export/pdf', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({html_content: result.value.resume_html})
                });
                const blob = await r.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = 'resume.pdf'; a.click();
                URL.revokeObjectURL(url);
            } catch(e) {
                alert('PDF导出失败: ' + e.message);
            }
        }

        function copyText(text) {
            navigator.clipboard.writeText(text).then(() => alert('已复制'));
        }

        // === AI 修改 ===
        const modifyInstruction = ref('');
        const selectedText = ref('');
        const modifiedText = ref('');
        const modifying = ref(false);

        async function aiModify() {
            if (!selectedText.value.trim() || !modifyInstruction.value.trim()) {
                alert('请输入要修改的原文和修改要求');
                return;
            }
            modifying.value = true;
            try {
                const r = await API.post('/api/ai/modify', {
                    selected_text: selectedText.value,
                    instruction: modifyInstruction.value,
                });
                modifiedText.value = r.modified_text;
            } catch(e) {
                alert('修改失败: ' + e.message);
            }
            modifying.value = false;
        }

        // === 模板管理 ===
        const allTemplates = ref([]);
        const customTemplates = ref([]);
        const newTemplateName = ref('');
        const templateFile = ref(null);

        async function loadTemplates() {
            try {
                allTemplates.value = await API.get('/api/templates');
                customTemplates.value = allTemplates.value.filter(t => !t.is_builtin);
            } catch(e) { console.error(e); }
        }

        function handleTemplateUpload(e) { templateFile.value = e.target.files[0]; }

        async function uploadTemplate() {
            if (!templateFile.value || !newTemplateName.value.trim()) return;
            const html = await templateFile.value.text();
            await API.post('/api/templates/upload', {name: newTemplateName.value, html_content: html});
            newTemplateName.value = '';
            templateFile.value = null;
            await loadTemplates();
            alert('模板已上传，AI已自动解析');
        }

        async function deleteTemplate(id) {
            if (!confirm('确认删除？')) return;
            await API.del(`/api/templates/${id}`);
            await loadTemplates();
        }

        onMounted(async () => {
            await loadExperiences();
            await loadTemplates();
        });

        return {
            tabs, currentTab,
            basicInfo, modules, selfEval, pasteText, parsing,
            saveBasicInfo, saveSelfEval, formatItem,
            editItem, deleteItem, addItem, parseText,
            jdText, templateType, generating, result, ocrText,
            generateResume, handleOCRUpload, exportPDF, copyText,
            modifyInstruction, selectedText, modifiedText, modifying, aiModify,
            allTemplates, customTemplates, newTemplateName, templateFile,
            loadTemplates, handleTemplateUpload, uploadTemplate, deleteTemplate,
        };
    }
}).mount('#app');
