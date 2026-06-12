/* DSE.Assist Dashboard JS — Vanilla SPA Logic */

document.addEventListener('DOMContentLoaded', () => {
    // Navigation Tabs
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanels = document.querySelectorAll('.tab-panel');
    const pageTitle = document.getElementById('page-title');
    const pageSubtitle = document.getElementById('page-subtitle');
    
    // Subtitles for each page
    const pageSubtitles = {
        'dashboard': 'Visão geral do desempenho e saúde do assistente',
        'config-ia': 'Gerencie o modelo de linguagem natural e canais de atuação',
        'config-rag': 'Ajuste a base de dados vetorial e parâmetros de busca semântica',
        'logs': 'Rastreabilidade e histórico de auditoria criptográfica'
    };

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.getAttribute('data-tab');
            
            // Toggle active sidebar items
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            
            // Toggle active panels
            tabPanels.forEach(panel => {
                panel.classList.remove('active');
                if (panel.id === `tab-${targetTab}`) {
                    panel.classList.add('active');
                }
            });

            // Update titles
            pageTitle.textContent = item.innerText.trim();
            pageSubtitle.textContent = pageSubtitles[targetTab] || '';
            
            // Fetch relevant data on tab entry
            if (targetTab === 'dashboard') {
                loadDashboardData();
            } else if (targetTab === 'config-ia' || targetTab === 'config-rag') {
                loadConfigData();
            } else if (targetTab === 'logs') {
                loadLogsData();
            }
        });
    });

    // Toggle password fields
    document.querySelectorAll('.btn-toggle-password').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = btn.previousElementSibling;
            if (input.type === 'password') {
                input.type = 'text';
                btn.innerHTML = `
                    <svg class="eye-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                        <line x1="1" y1="1" x2="23" y2="23"/>
                    </svg>
                `;
            } else {
                input.type = 'password';
                btn.innerHTML = `
                    <svg class="eye-open" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                        <circle cx="12" cy="12" r="3"/>
                    </svg>
                `;
            }
        });
    });

    // RAG Min Similarity slider live value indicator
    const ragSimInput = document.getElementById('RAG_MIN_SIMILARITY');
    const ragSimVal = document.getElementById('label-sim-val');
    if (ragSimInput && ragSimVal) {
        ragSimInput.addEventListener('input', (e) => {
            ragSimVal.textContent = parseFloat(e.target.value).toFixed(2);
        });
    }

    // Chart.js Instance
    let dailyChart = null;

    // Toast Notifications
    window.showToast = function(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let iconSvg = '';
        if (type === 'success') {
            iconSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>';
        } else if (type === 'error') {
            iconSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
        } else {
            iconSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>';
        }

        toast.innerHTML = `
            <div class="toast-icon">${iconSvg}</div>
            <div class="toast-text">${message}</div>
        `;
        
        container.appendChild(toast);
        
        // Remove toast after 4s
        setTimeout(() => {
            toast.classList.add('removing');
            toast.addEventListener('transitionend', () => {
                toast.remove();
            });
        }, 4000);
    };

    // Load Bot General Status
    async function loadBotStatus() {
        try {
            const res = await fetch('/api/status');
            if (!res.ok) throw new Error("Erro ao carregar status do bot");
            const data = await res.json();
            
            // Update Sidebar status card
            const nameDisplay = document.getElementById('bot-name-display');
            const statusDot = document.getElementById('bot-status-dot');
            const statusText = document.getElementById('bot-status-text');

            nameDisplay.textContent = data.bot_name || "Desconectado";
            
            if (data.bot_status === 'ONLINE') {
                statusDot.className = 'status-indicator online';
                statusText.textContent = 'Online';
            } else {
                statusDot.className = 'status-indicator offline';
                statusText.textContent = 'Offline';
            }

            // Update Instance Information on Dashboard
            document.getElementById('inst-latency').textContent = `${data.latency ? Math.round(data.latency) : '-'} ms`;
            document.getElementById('inst-uptime').textContent = data.uptime || '-';
            document.getElementById('inst-servers').textContent = data.guild_count !== undefined ? data.guild_count : '-';
            
            const providerBadge = document.getElementById('inst-provider');
            providerBadge.textContent = data.ai_provider || 'Nenhum';

            // Update Chroma counts on main dashboard
            const kbCountEl = document.getElementById('chroma-kb-count');
            const dhCountEl = document.getElementById('chroma-dh-count');
            if (kbCountEl) kbCountEl.textContent = data.chroma_kb_count !== undefined ? `${data.chroma_kb_count} chunks` : '-';
            if (dhCountEl) dhCountEl.textContent = data.chroma_dh_count !== undefined ? `${data.chroma_dh_count} itens` : '-';

            // Update Chroma counts in RAG config tab if they exist
            const ragKbBadge = document.getElementById('rag-kb-badge');
            const ragDhBadge = document.getElementById('rag-dh-badge');
            if (ragKbBadge) ragKbBadge.textContent = data.chroma_kb_count !== undefined ? `${data.chroma_kb_count} chunks` : '0 chunks';
            if (ragDhBadge) ragDhBadge.textContent = data.chroma_dh_count !== undefined ? `${data.chroma_dh_count} itens` : '0 itens';
            
        } catch (err) {
            console.error(err);
        }
    }

    // Initialize/Update daily transactions chart
    function updateDailyChart(chartData) {
        const ctx = document.getElementById('dailyChart').getContext('2d');
        
        const labels = chartData.map(d => d.date);
        const approved = chartData.map(d => d.approved);
        const rejected = chartData.map(d => d.rejected);
        const errors = chartData.map(d => d.errors);

        if (dailyChart) {
            dailyChart.destroy();
        }

        // Create elegant color gradients
        const gradientApproved = ctx.createLinearGradient(0, 0, 0, 300);
        gradientApproved.addColorStop(0, 'rgba(16, 185, 129, 0.25)');
        gradientApproved.addColorStop(1, 'rgba(16, 185, 129, 0.01)');

        const gradientRejected = ctx.createLinearGradient(0, 0, 0, 300);
        gradientRejected.addColorStop(0, 'rgba(239, 68, 68, 0.2)');
        gradientRejected.addColorStop(1, 'rgba(239, 68, 68, 0.01)');

        dailyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Aprovadas',
                        data: approved,
                        borderColor: '#10b981',
                        backgroundColor: gradientApproved,
                        fill: true,
                        tension: 0.35,
                        borderWidth: 2.5,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#10b981'
                    },
                    {
                        label: 'Barradas (Segurança)',
                        data: rejected,
                        borderColor: '#ef4444',
                        backgroundColor: gradientRejected,
                        fill: true,
                        tension: 0.35,
                        borderWidth: 2,
                        pointRadius: 2,
                        pointHoverRadius: 5,
                        pointBackgroundColor: '#ef4444'
                    },
                    {
                        label: 'Erros Técnicos',
                        data: errors,
                        borderColor: '#f59e0b',
                        fill: false,
                        tension: 0.3,
                        borderWidth: 1.5,
                        pointRadius: 1,
                        pointBackgroundColor: '#f59e0b'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#8b9bb4',
                            font: {
                                family: 'Outfit',
                                size: 12,
                                weight: 500
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: '#161a26',
                        titleColor: '#fff',
                        bodyColor: '#f1f3f9',
                        borderColor: 'rgba(255,255,255,0.08)',
                        borderWidth: 1,
                        padding: 10,
                        titleFont: { family: 'Outfit', weight: 600 },
                        bodyFont: { family: 'Outfit' }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255,255,255,0.02)',
                        },
                        ticks: {
                            color: '#8b9bb4',
                            font: { family: 'Outfit' }
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255,255,255,0.03)',
                        },
                        ticks: {
                            color: '#8b9bb4',
                            font: { family: 'Outfit' },
                            precision: 0
                        }
                    }
                }
            }
        });
    }

    // Load Metrics Cards & Lists on Dashboard tab
    async function loadDashboardData() {
        // Run Bot status update
        loadBotStatus();

        try {
            const res = await fetch('/api/stats');
            if (!res.ok) throw new Error("Erro ao carregar métricas");
            const data = await res.json();
            
            // Total metrics
            const total = data.total_req || 0;
            const approved = data.approved_req || 0;
            const rejected = data.rejected_req || 0;
            const errors = data.error_req || 0;

            document.getElementById('val-total-req').textContent = total;
            document.getElementById('val-approved-req').textContent = approved;
            document.getElementById('val-rejected-req').textContent = rejected;
            document.getElementById('val-error-req').textContent = errors;

            // Calculate percentages
            document.getElementById('pct-approved').textContent = total > 0 ? `${Math.round((approved / total) * 100)}% do total` : '0% do total';
            document.getElementById('pct-rejected').textContent = total > 0 ? `${Math.round((rejected / total) * 100)}% barrados` : '0% barrados';
            document.getElementById('pct-error').textContent = total > 0 ? `${Math.round((errors / total) * 100)}% falhas` : '0% falhas';

            // User rankings
            const rankingUsers = document.getElementById('ranking-users');
            rankingUsers.innerHTML = '';
            
            if (data.top_users && data.top_users.length > 0) {
                data.top_users.forEach((u, i) => {
                    const initials = u.username.substring(0, 2).toUpperCase();
                    const percentage = total > 0 ? Math.round((u.count / total) * 100) : 0;
                    
                    const div = document.createElement('div');
                    div.className = 'ranking-item';
                    div.innerHTML = `
                        <div class="ranking-item-left">
                            <div class="ranking-avatar">${initials}</div>
                            <div class="ranking-name-container">
                                <div class="ranking-name">${u.username}</div>
                                <div class="ranking-sub">Posição #${i+1}</div>
                            </div>
                        </div>
                        <div class="ranking-item-right">
                            <span class="ranking-val">${u.count}</span>
                            <span class="ranking-percent">${percentage}%</span>
                        </div>
                    `;
                    rankingUsers.appendChild(div);
                });
            } else {
                rankingUsers.innerHTML = '<div class="loading-placeholder">Nenhuma interação registrada no ledger.</div>';
            }

            // Command rankings
            const rankingCmds = document.getElementById('ranking-commands');
            rankingCmds.innerHTML = '';
            
            if (data.top_commands && data.top_commands.length > 0) {
                data.top_commands.forEach((c, i) => {
                    const percentage = total > 0 ? Math.round((c.count / total) * 100) : 0;
                    
                    const div = document.createElement('div');
                    div.className = 'ranking-item';
                    div.innerHTML = `
                        <div class="ranking-item-left">
                            <div class="ranking-name-container">
                                <div class="ranking-name">${c.command}</div>
                                <div class="ranking-sub">Destaque de uso</div>
                            </div>
                        </div>
                        <div class="ranking-item-right">
                            <span class="ranking-val">${c.count}</span>
                            <span class="ranking-percent">${percentage}%</span>
                        </div>
                    `;
                    rankingCmds.appendChild(div);
                });
            } else {
                rankingCmds.innerHTML = '<div class="loading-placeholder">Nenhum comando computado ainda.</div>';
            }

            // Daily Chart
            if (data.daily_data) {
                updateDailyChart(data.daily_data);
            }

        } catch (err) {
            console.error(err);
            showToast("Erro ao carregar dados do painel: " + err.message, "error");
        }
    }

    // Load configurations from .env
    async function loadConfigData() {
        // Refresh bot status and chroma counts
        await loadBotStatus();

        try {
            const res = await fetch('/api/config');
            if (!res.ok) throw new Error("Erro ao ler configurações");
            const config = await res.json();
            
            // IA fields
            if (config.AI_PROVIDER) document.getElementById('AI_PROVIDER').value = config.AI_PROVIDER;
            if (config.AI_MODEL) document.getElementById('AI_MODEL').value = config.AI_MODEL;
            if (config.AI_CHANNEL_NAME) document.getElementById('AI_CHANNEL_NAME').value = config.AI_CHANNEL_NAME;
            if (config.WELCOME_CHANNEL_NAME) document.getElementById('WELCOME_CHANNEL_NAME').value = config.WELCOME_CHANNEL_NAME;
            
            // RAG fields
            const isRagEnabled = config.RAG_ENABLED === 'true' || config.RAG_ENABLED === true || config.RAG_ENABLED === '1';
            document.getElementById('RAG_ENABLED').checked = isRagEnabled;
            
            if (config.RAG_COLLECTION) document.getElementById('RAG_COLLECTION').value = config.RAG_COLLECTION;
            if (config.RAG_N_RESULTS) document.getElementById('RAG_N_RESULTS').value = config.RAG_N_RESULTS;
            
            if (config.RAG_MIN_SIMILARITY) {
                document.getElementById('RAG_MIN_SIMILARITY').value = config.RAG_MIN_SIMILARITY;
                document.getElementById('label-sim-val').textContent = parseFloat(config.RAG_MIN_SIMILARITY).toFixed(2);
            }
            
            if (config.CHROMA_HOST) document.getElementById('CHROMA_HOST').value = config.CHROMA_HOST;
            if (config.CHROMA_TENANT) document.getElementById('CHROMA_TENANT').value = config.CHROMA_TENANT;
            if (config.CHROMA_DATABASE) document.getElementById('CHROMA_DATABASE').value = config.CHROMA_DATABASE;
            
            // Password placeholders
            document.getElementById('AI_API_KEY').value = '';
            document.getElementById('AI_API_KEY').placeholder = config.AI_API_KEY_MASKED || '••••••••••••••••••••••••';
            
            document.getElementById('CHROMA_API_KEY').value = '';
            document.getElementById('CHROMA_API_KEY').placeholder = config.CHROMA_API_KEY_MASKED || '••••••••••••••••••••••••';

        } catch (err) {
            console.error(err);
            showToast("Falha ao ler variáveis do arquivo .env: " + err.message, "error");
        }
    }

    // Save configurations
    async function saveConfig(formData, btnId) {
        const btn = document.getElementById(btnId);
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = `<div class="spinner"></div> Salvando...`;

        try {
            const res = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            const result = await res.json();
            if (!res.ok) throw new Error(result.error || "Falha no salvamento");
            
            showToast("Configuração salva e aplicada via Hot Reload!", "success");
            
            // Refresh configs to update placeholders
            await loadConfigData();
            // Refresh bot status (to check if provider changed correctly)
            await loadBotStatus();

        } catch (err) {
            console.error(err);
            showToast("Erro ao gravar e recarregar dados: " + err.message, "error");
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }

    // Submit IA Configuration Form
    document.getElementById('form-config-ia').addEventListener('submit', (e) => {
        e.preventDefault();
        const data = {
            AI_PROVIDER: document.getElementById('AI_PROVIDER').value,
            AI_MODEL: document.getElementById('AI_MODEL').value,
            AI_CHANNEL_NAME: document.getElementById('AI_CHANNEL_NAME').value,
            WELCOME_CHANNEL_NAME: document.getElementById('WELCOME_CHANNEL_NAME').value,
        };
        // Only include API key if the user typed a new one
        const key = document.getElementById('AI_API_KEY').value.trim();
        if (key) {
            data.AI_API_KEY = key;
        }
        saveConfig(data, 'btn-save-ia');
    });

    // Submit RAG Configuration Form
    document.getElementById('form-config-rag').addEventListener('submit', (e) => {
        e.preventDefault();
        const data = {
            RAG_ENABLED: document.getElementById('RAG_ENABLED').checked ? 'true' : 'false',
            RAG_COLLECTION: document.getElementById('RAG_COLLECTION').value,
            RAG_N_RESULTS: document.getElementById('RAG_N_RESULTS').value,
            RAG_MIN_SIMILARITY: document.getElementById('RAG_MIN_SIMILARITY').value,
            CHROMA_HOST: document.getElementById('CHROMA_HOST').value,
            CHROMA_TENANT: document.getElementById('CHROMA_TENANT').value,
            CHROMA_DATABASE: document.getElementById('CHROMA_DATABASE').value,
        };
        // Only include API key if typed a new one
        const key = document.getElementById('CHROMA_API_KEY').value.trim();
        if (key) {
            data.CHROMA_API_KEY = key;
        }
        saveConfig(data, 'btn-save-rag');
    });

    // Ledger Log Array
    let allLogs = [];

    // Load Logs Data
    async function loadLogsData() {
        try {
            const res = await fetch('/api/logs');
            if (!res.ok) throw new Error("Erro ao ler logs de auditoria");
            allLogs = await res.json();
            
            renderLogsTable(allLogs);

        } catch (err) {
            console.error(err);
            showToast("Falha ao ler o ledger do auditor de logs: " + err.message, "error");
        }
    }

    // Render Logs Table with Filter/Search
    function renderLogsTable(logs) {
        const tbody = document.getElementById('logs-table-body');
        tbody.innerHTML = '';

        const searchVal = document.getElementById('logs-search').value.toLowerCase().trim();
        const statusVal = document.getElementById('logs-filter-status').value;

        const filtered = logs.filter(log => {
            const matchesSearch = 
                (log.username && log.username.toLowerCase().includes(searchVal)) || 
                (log.command && log.command.toLowerCase().includes(searchVal)) ||
                (log.prompt && log.prompt.toLowerCase().includes(searchVal));
                
            const matchesStatus = statusVal ? log.status === statusVal : true;
            
            return matchesSearch && matchesStatus;
        });

        if (filtered.length > 0) {
            filtered.forEach((log, index) => {
                const tr = document.createElement('tr');
                
                // Formata Data/Hora
                const localDate = log.timestamp ? new Date(log.timestamp).toLocaleString('pt-BR') : '-';
                
                let statusBadge = '';
                if (log.status === 'APPROVED') {
                    statusBadge = '<span class="badge badge-approved">APPROVED</span>';
                } else if (log.status === 'REJECTED') {
                    statusBadge = '<span class="badge badge-rejected">REJECTED</span>';
                } else {
                    statusBadge = `<span class="badge badge-error">${log.status || 'ERROR'}</span>`;
                }

                tr.innerHTML = `
                    <td>${localDate}</td>
                    <td class="font-semibold">${log.username || 'Sistema'}</td>
                    <td>#${log.channel || 'direct'}</td>
                    <td><code>${log.command || '-'}</code></td>
                    <td>${statusBadge}</td>
                    <td>
                        <button class="btn btn-secondary btn-icon py-1 px-2 text-xs btn-view-log" data-index="${index}">
                            Ver
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });

            // Add Click Handlers for View buttons
            tbody.querySelectorAll('.btn-view-log').forEach(btn => {
                btn.addEventListener('click', () => {
                    const idx = btn.getAttribute('data-index');
                    showLogModal(filtered[idx]);
                });
            });

        } else {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Nenhum registro encontrado correspondente aos filtros.</td></tr>';
        }
    }

    // Attach search and filter events
    document.getElementById('logs-search').addEventListener('input', () => renderLogsTable(allLogs));
    document.getElementById('logs-filter-status').addEventListener('change', () => renderLogsTable(allLogs));

    // Show Detail Modal
    function showLogModal(log) {
        const modal = document.getElementById('log-modal');
        
        document.getElementById('modal-user').textContent = `${log.username || 'Sistema'} (ID: ${log.user_id || '0'})`;
        document.getElementById('modal-channel-cmd').textContent = `Canal: #${log.channel} | Comando: ${log.command}`;
        
        let statusBadge = '';
        if (log.status === 'APPROVED') {
            statusBadge = '<span class="badge badge-approved">APPROVED</span>';
        } else if (log.status === 'REJECTED') {
            statusBadge = '<span class="badge badge-rejected">REJECTED</span>';
        } else {
            statusBadge = `<span class="badge badge-error">${log.status || 'ERROR'}</span>`;
        }
        document.getElementById('modal-status').innerHTML = statusBadge;
        document.getElementById('modal-prompt').textContent = log.prompt || '-';
        document.getElementById('modal-response').textContent = log.response || '-';
        document.getElementById('modal-prev-hash').textContent = log.prev_hash || '0'.repeat(64);
        document.getElementById('modal-curr-hash').textContent = log.hash || '0'.repeat(64);

        // Sources tags
        const sourcesContainer = document.getElementById('modal-sources');
        const contextSection = document.getElementById('modal-context-section');
        sourcesContainer.innerHTML = '';
        
        if (log.retrieved_sources && log.retrieved_sources.length > 0) {
            contextSection.style.display = 'flex';
            log.retrieved_sources.forEach(src => {
                const span = document.createElement('span');
                span.className = 'badge-source';
                span.textContent = src;
                sourcesContainer.appendChild(span);
            });
        } else {
            contextSection.style.display = 'none';
        }

        modal.classList.add('open');
    }

    // Close Modal
    const closeModal = () => {
        document.getElementById('log-modal').classList.remove('open');
    };
    document.getElementById('btn-close-modal').addEventListener('click', closeModal);
    document.getElementById('log-modal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('log-modal')) {
            closeModal();
        }
    });

    // Validate Ledger Integrity
    async function runIntegrityAudit() {
        const badge = document.getElementById('integrity-badge');
        badge.className = 'integrity-badge loading';
        badge.innerHTML = `<div class="spinner"></div> <span>Validando Ledger...</span>`;

        try {
            const res = await fetch('/api/verify', { method: 'POST' });
            if (!res.ok) throw new Error("Erro na verificação de integridade");
            const result = await res.json();
            
            if (result.valid) {
                badge.className = 'integrity-badge valid';
                badge.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="16" height="16">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                    <span>Ledger Íntegro (SHA-256 Validado)</span>
                `;
                showToast("Integridade do ledger confirmada com sucesso! Sem violações.", "success");
            } else {
                badge.className = 'integrity-badge invalid';
                badge.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="16" height="16">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    </svg>
                    <span>Ledger Violado (Falha de Hash!)</span>
                `;
                showToast("ALERTA DE SEGURANÇA: Quebra detectada na cadeia de hashes!", "error");
            }
        } catch (err) {
            badge.className = 'integrity-badge invalid';
            badge.innerHTML = `<span>Falha na Auditoria</span>`;
            showToast("Erro durante a auditoria criptográfica: " + err.message, "error");
        }
    }

    document.getElementById('btn-run-audit').addEventListener('click', runIntegrityAudit);

    // Refresh dashboard stats on sync click
    document.getElementById('btn-refresh-stats').addEventListener('click', async () => {
        const syncSvg = document.querySelector('.btn-svg-icon');
        syncSvg.classList.add('spinning');
        
        const activeTab = document.querySelector('.nav-item.active').getAttribute('data-tab');
        
        if (activeTab === 'dashboard') {
            await loadDashboardData();
        } else if (activeTab === 'config-ia' || activeTab === 'config-rag') {
            await loadConfigData();
        } else if (activeTab === 'logs') {
            await loadLogsData();
        }
        
        await runIntegrityAudit();
        
        // Remove spinning class after 800ms
        setTimeout(() => {
            syncSvg.classList.remove('spinning');
            showToast("Métricas e estado sincronizados com sucesso!", "info");
        }, 800);
    });

    // Initial load
    loadDashboardData();
    runIntegrityAudit();
    
    // Poll status periodically (every 15 seconds)
    setInterval(loadBotStatus, 15000);
});
