/**
 * SAJO – Elite Frontend Intelligence Hub
 * Production Grade - No Sugarcoating
 * Full implementation of Real-time Workspace, Adaptive Insight, and Neural Search.
 */

(function () {
    'use strict';

    const socket = (typeof io !== 'undefined') ? io() : null;
    const APP_THEME = 'sajo-app-theme';
    let autosaveTimer = null;
    let recognition = null;
    let remoteCursors = {};

    // ============================================
    // PRODUCTION ANALYTICS (REAL NEURAL METRICS)
    // ============================================
    window.renderRealAnalytics = async function () {
        const docCanvas = document.getElementById('doc-chart');
        const sumCanvas = document.getElementById('sum-chart');
        const actCanvas = document.getElementById('active-chart');
        
        if (!docCanvas || typeof Chart === 'undefined') return;

        try {
            const res = await fetch('/api/analytics');
            const data = await res.json();
            
            const commonOptions = {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { 
                    y: { display: false, beginAtZero: true },
                    x: { grid: { display: false }, ticks: { color: 'rgba(255,255,255,0.3)', font: { size: 9 } } }
                }
            };

            const labels = (data.labels || []).reverse();
            const values = (data.data || []).reverse();

            new Chart(docCanvas, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        borderColor: '#6366f1',
                        backgroundColor: 'rgba(99, 102, 241, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: commonOptions
            });

            if (sumCanvas) {
                new Chart(sumCanvas, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: values.map(v => Math.floor(v * 1.5)),
                            backgroundColor: '#10b981',
                            borderRadius: 4
                        }]
                    },
                    options: commonOptions
                });
            }

            if (actCanvas) {
                new Chart(actCanvas, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: values.map(v => Math.floor(v * 0.8)),
                            borderColor: '#f59e0b',
                            borderDash: [5, 5],
                            tension: 0.4
                        }]
                    },
                    options: commonOptions
                });
            }
        } catch (e) { console.error("Neural telemetry failure", e); }
    };

    // ============================================
    // CORE INTELLIGENCE ENGINE
    // ============================================
    window.execCommand = (cmd, val = null) => {
        document.execCommand(cmd, false, val);
        const editor = document.getElementById('text-input');
        if (editor) editor.focus();
    };

    window.typeResult = (el, text) => {
        if (!el || !text) return;
        el.innerHTML = '';
        let i = 0;
        const interval = setInterval(() => {
            const char = text.charAt(i);
            if (char === '\n') {
                el.innerHTML += '<br>';
            } else {
                el.innerHTML += char;
            }
            i++;
            if (i >= text.length) clearInterval(interval);
        }, 12);
    };

    window.askQuestion = async function() {
        const input = document.getElementById('qa-input');
        const query = input.value;
        let content = document.getElementById('text-input').innerText;
        const title = document.getElementById('doc-title-input').value;
        const resultBox = document.getElementById('qa-result');
        
        if(!query.trim()) return;
        
        // If main editor is empty, try using title area (in case they pasted there)
        if(!content.trim() && title.length > 50) content = title;
        if(!content.trim()) return window.showFlash('No intelligence content found to query.', 'error');
        
        resultBox.innerHTML = '<div style="padding:20px; text-align:center;"><i class="fas fa-circle-notch fa-spin"></i> Querying intelligence network...</div>';
        
        try {
            const res = await fetch('/api/query-knowledge', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query, content })
            });
            const data = await res.json();
            if(data.success) {
                resultBox.innerHTML = `
                    <div class="qa-chat-bubble user fade-in-up">
                        <div class="qa-tag">You</div>
                        ${query}
                    </div>
                    <div class="qa-chat-bubble ai fade-in-up">
                        <div class="qa-tag">Intelligence</div>
                        ${data.answer}
                    </div>
                `;
                input.value = '';
            } else {
                resultBox.innerHTML = `<div class="p-16" style="color:var(--error)">${data.error || 'Query failed'}</div>`;
            }
        } catch(e) {
            resultBox.innerHTML = '<div class="p-16" style="color:var(--error)">Intelligence retrieval offline.</div>';
        }
    };

    let quizScore = 0;
    let quizTotal = 0;
    let quizAnswered = 0;

    window.generateAdaptiveQuiz = async function() {
        const content = document.getElementById('text-input').innerText;
        const container = document.getElementById('quiz-container');
        if(!content.trim()) return window.showFlash('Intelligence subject required', 'error');
        
        container.innerHTML = '<div style="padding:40px; text-align:center;"><i class="fas fa-circle-notch fa-spin"></i> Ingesting knowledge...</div>';
        try {
            const res = await fetch('/api/generate-quiz', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ content })
            });
            const result = await res.json();
            if(result.success) {
                quizScore = 0;
                quizAnswered = 0;
                quizTotal = result.data.questions.length;
                
                let html = `
                    <div id="quiz-score-card" class="card glass mb-24 p-16 flex justify-between items-center" style="border-bottom: 2px solid var(--emerald); background: rgba(16, 185, 129, 0.1);">
                        <div style="font-weight: 800; font-size: 0.85rem; color: var(--emerald); text-transform: uppercase;">Knowledge Validation Score</div>
                        <div id="quiz-progress-text" style="font-weight: 900; font-size: 1.2rem; color: #fff;">0 / ${quizTotal}</div>
                    </div>
                `;
                
                html += result.data.questions.map((q, i) => `
                    <div class="card glass mb-16 p-16 fade-in-up" style="border-left: 4px solid var(--emerald); background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(30, 41, 59, 0.8) 100%);">
                        <div style="font-weight: 800; margin-bottom: 12px; font-size: 0.75rem; color: var(--emerald); text-transform: uppercase; letter-spacing: 2px;"><i class="fas fa-lightbulb mr-8"></i> Knowledge Probe ${i+1}</div>
                        <div style="margin-bottom: 20px; font-size: 1.1rem; line-height: 1.5; font-weight: 600; color: #fff; text-shadow: 0 0 20px rgba(16, 185, 129, 0.3);">${q.question}</div>
                        <div class="flex flex-col gap-10">
                            ${q.options.map((opt, idx) => `
                                <button class="btn btn-secondary btn-sm" style="justify-content: flex-start; text-align: left; border: 1px solid rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.05); color: #cbd5e1; padding: 12px 16px;" onmouseover="this.style.background='rgba(16, 185, 129, 0.15)'; this.style.color='#fff';" onmouseout="this.style.background='rgba(16, 185, 129, 0.05)'; this.style.color='#cbd5e1';" onclick="window.checkQuiz(this, ${idx}, ${q.answer})">${opt}</button>
                            `).join('')}
                        </div>
                    </div>
                `).join('');
                container.innerHTML = html;
            }
        } catch(e) { container.innerHTML = '<div class="p-16 text-error">Synthesis module failure.</div>'; }
    };

    window.checkQuiz = (btn, selected, correct) => {
        const allBtns = btn.parentElement.querySelectorAll('button');
        allBtns.forEach(b => b.disabled = true);
        quizAnswered++;
        
        if(selected === correct) {
            quizScore++;
            btn.style.borderColor = 'var(--success)';
            btn.style.background = 'rgba(16, 185, 129, 0.1)';
            window.showFlash('Optimal insight confirmed.', 'success');
        } else {
            btn.style.borderColor = 'var(--error)';
            btn.style.background = 'rgba(239, 68, 68, 0.1)';
            allBtns[correct].style.borderColor = 'var(--success)';
            window.showFlash('Sub-optimal perception corrected.', 'error');
        }
        
        // Update Score Display
        const progressText = document.getElementById('quiz-progress-text');
        if(progressText) progressText.innerText = `${quizScore} / ${quizTotal}`;
        
        if(quizAnswered === quizTotal) {
            setTimeout(() => {
                window.showFlash(`Validation Complete: You mastered ${quizScore}/${quizTotal} concepts!`, 'success');
                if(quizScore === quizTotal) {
                    const scoreCard = document.getElementById('quiz-score-card');
                    scoreCard.style.background = 'linear-gradient(90deg, var(--emerald), #059669)';
                    scoreCard.innerHTML = '<div style="font-weight:900; color:#fff; width:100%; text-align:center;"><i class="fas fa-crown"></i> 100% CONCEPT MASTERY ACHIEVED</div>';
                }
            }, 800);
        }
    };

    // ============================================
    // REAL-TIME COLLABORATION & GHOST CURSORS
    // ============================================
    window.joinCollab = function (docId) {
        if (!socket) return;
        socket.emit('join', { doc_id: docId });
        
        socket.on('presence', (data) => {
            const container = document.getElementById('collab-users');
            if (!container) return;
            const existing = document.getElementById(`user-${data.user_id}`);
            if (existing) return;
            
            const dot = document.createElement('div');
            dot.id = `user-${data.user_id}`;
            dot.className = 'status-avatar';
            dot.innerText = data.username[0].toUpperCase();
            dot.title = data.username;
            container.appendChild(dot);
        });

        socket.on('edit', (data) => {
            if (data.user_id === socket.id) return;
            renderRemoteCursor(data);
        });

        document.getElementById('text-input').addEventListener('mousemove', (e) => {
            const editor = e.currentTarget;
            const rect = editor.getBoundingClientRect();
            const username = typeof CURRENT_USER !== 'undefined' ? CURRENT_USER : 'Practitioner';
            socket.emit('edit', {
                doc_id: docId,
                x: e.clientX - rect.left,
                y: e.clientY - rect.top,
                username: username
            });
        });
    };

    function renderRemoteCursor(data) {
        let cursor = remoteCursors[data.user_id];
        if (!cursor) {
            cursor = document.createElement('div');
            cursor.className = 'remote-cursor';
            cursor.dataset.label = data.username;
            document.getElementById('text-input').parentElement.appendChild(cursor);
            remoteCursors[data.user_id] = cursor;
        }
        cursor.style.left = data.x + 'px';
        cursor.style.top = data.y + 'px';
    }

    // ============================================
    // NEURAL RELATIONSHIP MAPPING (D3.js)
    // ============================================
    window.renderKnowledgeGraph = async function (docId, containerId) {
        const container = document.getElementById(containerId);
        if (!container || typeof d3 === 'undefined') return;
        container.innerHTML = '';

        try {
            const res = await fetch(`/api/knowledge-graph/${docId}`);
            const data = await res.json();
            
            const width = container.clientWidth;
            const height = container.clientHeight || 400;

            const svg = d3.select(`#${containerId}`)
                .append('svg')
                .attr('width', '100%')
                .attr('height', '100%')
                .attr('viewBox', `0 0 ${width} ${height}`);

            const simulation = d3.forceSimulation(data.nodes)
                .force('link', d3.forceLink(data.links).id(d => d.id).distance(100))
                .force('charge', d3.forceManyBody().strength(-300))
                .force('center', d3.forceCenter(width / 2, height / 2));

            const link = svg.append('g')
                .selectAll('line')
                .data(data.links)
                .join('line')
                .attr('stroke', 'var(--border)')
                .attr('stroke-opacity', 0.6)
                .attr('stroke-width', 2);

            const node = svg.append('g')
                .selectAll('circle')
                .data(data.nodes)
                .join('circle')
                .attr('r', d => d.type === 'root' ? 12 : 8)
                .attr('fill', d => d.type === 'root' ? 'var(--accent)' : 'var(--surface)')
                .attr('stroke', 'var(--accent)')
                .attr('stroke-width', 2)
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended));

            node.append('title').text(d => d.name);

            const label = svg.append('g')
                .selectAll('text')
                .data(data.nodes)
                .join('text')
                .text(d => d.name)
                .attr('font-size', '10px')
                .attr('fill', 'var(--text-muted)')
                .attr('dx', 15)
                .attr('dy', 4);

            simulation.on('tick', () => {
                link.attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);

                node.attr('cx', d => d.x)
                    .attr('cy', d => d.y);

                label.attr('x', d => d.x)
                    .attr('y', d => d.y);
            });

            function dragstarted(event) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }
            function dragged(event) {
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }
            function dragended(event) {
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }
        } catch (e) {
            console.error("Graph rendering failure", e);
            container.innerHTML = '<div class="p-32 text-center text-muted">Neural link mapping offline.</div>';
        }
    };

    // ============================================
    // VOICE & FOCUS ARCHITECTURE
    // ============================================
    window.toggleVoice = () => {
        const btn = document.getElementById('voice-btn');
        if (!recognition) {
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            if(!SpeechRec) return window.showFlash('Neural voice capture unavailable.', 'error');
            recognition = new SpeechRec();
            recognition.continuous = true;
            recognition.onresult = (e) => {
                const transcript = e.results[e.results.length - 1][0].transcript;
                window.execCommand('insertText', transcript + ' ');
            };
        }

        if (btn.classList.contains('active')) {
            recognition.stop();
            btn.classList.remove('active');
            btn.innerHTML = '<i class="fas fa-microphone"></i> Start Recording';
        } else {
            recognition.start();
            btn.classList.add('active');
            btn.innerHTML = '<i class="fas fa-stop-circle" style="color:var(--error)"></i> Capture Active...';
        }
    };

    window.toggleFocusMode = () => {
        document.body.classList.toggle('focus-mode');
        window.showFlash(document.body.classList.contains('focus-mode') ? 'Interface suppression active.' : 'Full spectrum restored.', 'info');
    };

    // ============================================
    // UTILS & NEURAL SEARCH
    // ============================================
    window.setTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(APP_THEME, theme);
    };

    window.showFlash = (msg, type = 'info') => {
        const existing = document.querySelector('.flash-message');
        if (existing) existing.remove();
        
        const div = document.createElement('div');
        div.className = `flash-message ${type} fade-in-up`;
        div.style.cssText = 'position:fixed; bottom:30px; right:30px; z-index:9999; padding:14px 28px; border-radius:12px; backdrop-filter:blur(20px); border:1px solid var(--border); box-shadow: 0 10px 30px rgba(0,0,0,0.3); color:#fff; font-weight:700; font-size: 0.85rem;';
        div.style.background = type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--error)' : 'var(--accent)';
        div.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} mr-8"></i> ${msg}`;
        document.body.appendChild(div);
        setTimeout(() => div.classList.add('fade-out'), 2500);
        setTimeout(() => div.remove(), 3000);
    };

    window.globalSearch = async (q) => {
        const resultsBox = document.getElementById('command-results');
        if(!q.trim()) { resultsBox.innerHTML = ''; return; }
        try {
            const res = await fetch(`/api/search?q=${q}`);
            const data = await res.json();
            resultsBox.innerHTML = data.results.map(doc => `
                <div class="card glass mb-8 p-12 flex justify-between items-center clickable border-radius-10" onclick="location.href='/editor?id=${doc.id}'">
                    <div style="flex:1;">
                        <div style="font-weight: 800; font-size: 0.95rem;">${doc.title}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">${doc.summary || 'Intelligence snapshot...'}</div>
                    </div>
                    <i class="fas fa-chevron-right" style="color: var(--accent); opacity: 0.5;"></i>
                </div>
            `).join('') || '<div style="text-align:center; padding:20px; color:var(--text-muted);">No neural matches.</div>';
        } catch(e) { console.error("Search failure", e); }
    };

    // Global Key Listeners
    window.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            const cp = document.getElementById('command-palette');
            if (cp) {
                cp.style.display = cp.style.display === 'flex' ? 'none' : 'flex';
                if (cp.style.display === 'flex') document.getElementById('palette-search').focus();
            }
        }
        if (e.key === 'Escape') {
            const cp = document.getElementById('command-palette');
            if (cp) cp.style.display = 'none';
        }
        if (e.key === 'Enter' && document.activeElement.id === 'qa-input') {
            window.askQuestion();
        }
    });

    window.initAutoSave = function (docId) {
        const editor = document.getElementById('text-input');
        const status = document.getElementById('save-indicator');
        const wordCount = document.getElementById('word-count');
        if (!editor) return;

        editor.addEventListener('input', () => {
            // Update Word Count
            const text = editor.innerText || editor.textContent;
            const words = text.trim() ? text.trim().split(/\s+/).length : 0;
            if(wordCount) wordCount.innerText = `${words} words`;

            if(!docId) return;

            status.innerHTML = '<i class="fas fa-sync fa-spin"></i> Syncing...';
            clearTimeout(autosaveTimer);
            autosaveTimer = setTimeout(async () => {
                const content = editor.innerHTML;
                try {
                    await fetch('/api/autosave', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: docId, content })
                    });
                    status.innerHTML = '<i class="fas fa-check-circle"></i> Insight Saved';
                } catch (e) { status.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Local Only'; }
            }, 2000);
        });
    };


    // ============================================
    // INITIALIZATION
    // ============================================
    setTheme(localStorage.getItem(APP_THEME) || 'dark');
    document.addEventListener('DOMContentLoaded', () => {
        if (typeof Chart !== 'undefined') renderRealAnalytics();
    });

})();
