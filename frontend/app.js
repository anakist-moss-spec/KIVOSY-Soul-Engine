/**
 * KIVOSY Global Multi-Channel Dashboard
 * Version: 3.0 FINAL
 * 다국어 지원 + 채널 필터링 + 강화된 사고 과정 추출
 */

// ═══════════════════════════════════════════════════════════
// 전역 상태 (Global State)
// ═══════════════════════════════════════════════════════════
let currentFilter = 'all';
let allNodes = [];


// ═══════════════════════════════════════════════════════════
// 액션 실행 엔진 (Action Dispatcher) - 🆕 3교시 추가 // 🛡️ 중복 방지 강화 버전
// ═══════════════════════════════════════════════════════════
const ActionDispatcher = {
    // 이미 처리된 노드 ID를 저장 (메모리 상에 유지)
    processedIds: new Set(),

    dispatch: function(nodeId, rawText) {
        if (!rawText || !nodeId) return;
        
        // [중복 체크] 이미 이 ID의 액션을 처리했다면 즉시 종료!
        if (this.processedIds.has(nodeId)) {
            return; 
        }

        const actionRegex = /\[ACTION:\s*(\w+),\s*params:\s*({.*?})\]/g;
        let match;
        let hasAction = false;
        
        while ((match = actionRegex.exec(rawText)) !== null) {
            hasAction = true;
            const type = match[1];
            try {
                const params = JSON.parse(match[2]);
                console.log(`🚀 [KIVOSY ACTION] 실행 (ID: ${nodeId}): ${type}`, params);
                
                switch(type) {
                    case 'SAVE_MEMO':
                        this.saveToStorage(params.content);
                        break;
                    case 'CREATE_UI':
                        if(window.triggerAppFactory) window.triggerAppFactory(params);
                        break;
                    default:
                        console.warn(`⚠️ 정의되지 않은 액션: ${type}`);
                }
            } catch (e) {
                console.error("❌ 액션 파싱 실패:", e);
            }
        }

        // 액션 처리가 끝났다면 이 ID를 '완료 목록'에 추가
        if (hasAction) {
            this.processedIds.add(nodeId);
            // 메모리 관리를 위해 너무 많아지면 오래된 건 비워줄 수도 있습니다.
        }
    },
    
    saveToStorage: function(content) {
        console.log("📝 로컬 메모리에 저장 완료:", content);
    }
};

// ═══════════════════════════════════════════════════════════
// 채널 설정 (Channel Configuration)
// ═══════════════════════════════════════════════════════════
const CHANNELS = {
    'all': { name: '전체', icon: '🌍', color: '#667eea' },
    'kakao': { name: 'KakaoTalk', icon: '💬', color: '#FAE100' },
    'whatsapp': { name: 'WhatsApp', icon: '🟢', color: '#25D366' },
    'line': { name: 'LINE', icon: '💚', color: '#00B900' }
};

const LANGUAGES = {
    'ko': '🇰🇷 한국어',
    'en': '🇺🇸 English',
    'vi': '🇻🇳 Tiếng Việt'
};

// ═══════════════════════════════════════════════════════════
// 메인 함수 (Main Functions)
// ═══════════════════════════════════════════════════════════

/**
 * 노드 로드 (Load Nodes with Filtering)
 */
async function loadNodes(channelFilter = 'all') {
    try {
        console.log(`[로드] 필터: ${channelFilter}`);
        
        // API URL 구성
        const url = channelFilter === 'all' 
            ? '/api/nodes' 
            : `/api/nodes?channel=${channelFilter}`;
        
        const response = await fetch(url);
        const nodes = await response.json();
        
        allNodes = nodes;
        
        console.log(`[로드] ${nodes.length}개 노드 로드 완료`);
        
        // UI 업데이트
        updateStats(nodes);
        renderNodes(nodes);
        
    } catch (error) {
        console.error('[로드 오류]', error);
        showEmptyState('⚠️ 데이터 로드 실패');
    }
}

/**
 * 통계 업데이트 (Update Statistics)
 */
function updateStats(nodes) {
    // 전체 노드 수
    document.getElementById('totalNodes').textContent = nodes.length;
    
    // 사고 과정 포함 노드 수 (강화된 감지)
    const thinkingCount = nodes.filter(n => {
        if (n.ai?.has_thinking) return true;
        if (n.ai_response) {
            return /<think|<Think|<생각/i.test(n.ai_response);
        }
        return false;
    }).length;
    document.getElementById('thinkingNodes').textContent = thinkingCount;
    
    // 활성 채널 수
    const activeChannels = new Set(nodes.map(n => n.channel));
    document.getElementById('channelCount').textContent = activeChannels.size;
    
    // 채널 필터 버튼 업데이트
    updateChannelButtons(nodes);
}

/**
 * 채널 필터 버튼 업데이트 (Update Channel Filter Buttons)
 */
function updateChannelButtons(nodes) {
    const counts = {
        'all': nodes.length,
        'kakao': nodes.filter(n => n.channel === 'kakao').length,
        'whatsapp': nodes.filter(n => n.channel === 'whatsapp').length,
        'line': nodes.filter(n => n.channel === 'line').length
    };
    
    Object.keys(CHANNELS).forEach(channel => {
        const btn = document.querySelector(`[data-channel="${channel}"]`);
        if (btn) {
            const countSpan = btn.querySelector('.filter-count');
            if (countSpan) {
                countSpan.textContent = counts[channel] || 0;
            }
            
            // 데이터 없으면 반투명 처리
            if (channel !== 'all' && counts[channel] === 0) {
                btn.style.opacity = '0.4';
            } else {
                btn.style.opacity = '1';
            }
        }
    });
}

/**
 * 노드 렌더링 (Render Nodes)
 */
function renderNodes(nodes) {
    const nodesGrid = document.getElementById('nodesGrid');
    const emptyState = document.getElementById('emptyState');
    
    if (nodes.length === 0) {
        nodesGrid.style.display = 'none';
        emptyState.style.display = 'block';
        
        const filterInfo = CHANNELS[currentFilter];
        emptyState.innerHTML = `
            <div style="font-size: 64px; margin-bottom: 20px;">${filterInfo.icon}</div>
            <div style="font-size: 24px; font-weight: bold; margin-bottom: 10px;">
                ${filterInfo.name} 데이터 없음
            </div>
            <div style="color: gray;">
                ${filterInfo.name}로 메시지를 전송하면 여기에 표시됩니다.
            </div>
        `;
        return;
    }
    
    nodesGrid.style.display = 'grid';
    emptyState.style.display = 'none';
    
    // 노드 카드 렌더링 (최신순)
    nodesGrid.innerHTML = nodes.reverse().map(node => renderNodeCard(node)).join('');
}

/**
 * 개별 노드 카드 렌더링 (Render Individual Node Card)
 */
function renderNodeCard(node) {
    const channelInfo = CHANNELS[node.channel] || CHANNELS['kakao'];
    
    // 강화된 사고 과정 추출 (Enhanced Thinking Extraction)
    let thinking = '';
    let summary = '';
    
    if (node.ai) {
        // 신규 구조
        thinking = node.ai.thinking || '';
        summary = node.ai.summary || '';
    } else if (node.ai_response) {
        // 레거시 구조 (정규식으로 추출)
        const thinkMatch = node.ai_response.match(/<(think|Think|생각)>([\s\S]*?)<\/(think|Think|생각)>/i);
        thinking = thinkMatch ? thinkMatch[2].trim() : '';
        
        // 요약 추출 (태그 제거)
        summary = node.ai_response
            .replace(/<(think|Think|생각)>[\s\S]*?<\/(think|Think|생각)>/gi, '')
            .replace(/<(final|Final|결론|요약)>([\s\S]*?)<\/(final|Final|결론|요약)>/gi, '$2')
            .trim();
    }
    
    // 폴백 처리
    if (!thinking) thinking = '추론 기록 없음';
    if (!summary) summary = node.content || '요약 없음';
    
    // 언어 표시
    const language = node.ai?.language || detectLanguage(node.content);
    const languageLabel = LANGUAGES[language] || '🌐 Auto';
    
    // 시간 포맷팅
    const timestamp = new Date(node.timestamp);
    const timeAgo = getTimeAgo(timestamp);

    // 🆕 [핵심 추가] AI 응답이 있을 때 액션 검사 및 실행
    // 🆕 변경된 호출 방식 (ID를 함께 전달!)
    if (node.ai_response) {
        ActionDispatcher.dispatch(node.id, node.ai_response);
    }
        
    return `
        <div class="node-card" data-channel="${node.channel}">
            <!-- 헤더 -->
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:15px;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="font-size:32px;">${channelInfo.icon}</div>
                    <div>
                        <div style="font-weight:bold; font-size:15px; color:var(--user-bubble);">
                            ${channelInfo.name}
                        </div>
                        <div style="font-size:11px; color:gray;">
                            ${timeAgo} • ${languageLabel}
                        </div>
                    </div>
                </div>
                <div style="font-size:11px; color:gray;">#${node.id.substring(0,6)}</div>
            </div>
            
            <!-- 원본 메시지 -->
            <div style="margin-bottom:15px;">
                <div style="font-weight:bold; font-size:12px; color:gray; margin-bottom:5px;">
                    📥 수신 메시지
                </div>
                <div style="font-size:15px; line-height:1.5;">
                    ${escapeHtml(node.content)}
                </div>
            </div>
            
            <!-- 사고 과정 -->
            <div class="thinking-section">
                <div style="font-size:11px; font-weight:bold; color:var(--thinking-text); margin-bottom:8px;">
                    💭 14B 과장님의 사고 회로
                </div>
                <div class="thinking-text">${escapeHtml(thinking)}</div>
            </div>
            
            <!-- 요약 결과 -->
            <div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:15px; margin-top:15px;">
                <div style="font-weight:bold; font-size:12px; color:var(--user-bubble); margin-bottom:5px;">
                    📝 요약 결과
                </div>
                <div style="font-size:14px; line-height:1.6;">
                    ${escapeHtml(summary)}
                </div>
            </div>
        </div>
    `;
}

/**
 * 채널 필터 설정 (Set Channel Filter)
 */
function setChannelFilter(channel) {
    if (!CHANNELS[channel]) {
        console.warn(`지원하지 않는 채널: ${channel}`);
        return;
    }
    
    currentFilter = channel;
    
    // 버튼 활성화 상태
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.channel === channel);
    });
    
    // 노드 재로드
    loadNodes(channel);
    
    console.log(`[필터] ${channel} 적용`);
}

// ═══════════════════════════════════════════════════════════
// 유틸리티 함수 (Utility Functions)
// ═══════════════════════════════════════════════════════════

/**
 * HTML 이스케이프 (XSS 방지)
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 언어 감지
 */
function detectLanguage(text) {
    if (/[가-힣]/.test(text)) return 'ko';
    if (/[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệ]/i.test(text)) return 'vi';
    return 'en';
}

/**
 * 시간 경과 표시
 */
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return '방금 전';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}분 전`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}시간 전`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}일 전`;
    return date.toLocaleDateString('ko-KR');
}

/**
 * 빈 상태 표시
 */
function showEmptyState(message) {
    const emptyState = document.getElementById('emptyState');
    emptyState.innerHTML = `<div style="color:#f44336;">${message}</div>`;
    emptyState.style.display = 'block';
    document.getElementById('nodesGrid').style.display = 'none';
}

// ═══════════════════════════════════════════════════════════
// 초기화 (Initialization)
// ═══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    console.log('[KIVOSY] Global Multi-Channel Dashboard 초기화...');
    
    // 초기 로드
    loadNodes('all');
    
    // 자동 새로고침 (10초마다)
    setInterval(() => {
        loadNodes(currentFilter);
    }, 10000);
    
    console.log('[KIVOSY] 대시보드 준비 완료! 🚀');
});
