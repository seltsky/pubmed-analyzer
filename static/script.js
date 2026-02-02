// 상태 관리
let currentSearch = {
    query: '',
    author: '',
    start_date: '',
    end_date: '',
    page: 1,
    page_size: 20,
    total: 0,
    papers: [],
    sort_by: 'relevance'
};

let selectedPmids = new Set();
let trendsChart = null;
let keywordsChart = null;
let chatHistory = [];
let generatedQuery = null;

// localStorage 키
const BOOKMARKS_KEY = 'pubmed_bookmarks';
const HISTORY_KEY = 'pubmed_search_history';

// DOM 요소
const searchForm = document.getElementById('search-form');
const resultsSection = document.getElementById('results-section');
const papersList = document.getElementById('papers-list');
const totalCount = document.getElementById('total-count');
const pagination = document.getElementById('pagination');
const loading = document.getElementById('loading');
const exportBtn = document.getElementById('export-csv');
const summarizeBtn = document.getElementById('summarize-selected');
const chatBtn = document.getElementById('chat-with-ai');
const selectAllCheckbox = document.getElementById('select-all');
const summaryModal = document.getElementById('summary-modal');
const summaryContent = document.getElementById('summary-content');
const chatModal = document.getElementById('chat-modal');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const chatSendBtn = document.getElementById('chat-send');
const chatPaperCount = document.getElementById('chat-paper-count');
const aiSearchMode = document.getElementById('ai-search-mode');
const queryLabel = document.getElementById('query-label');
const queryInput = document.getElementById('query');
const aiQueryResult = document.getElementById('ai-query-result');
const aiQueryContent = document.getElementById('ai-query-content');
const useAiQueryBtn = document.getElementById('use-ai-query');
const showBookmarksBtn = document.getElementById('show-bookmarks');
const showHistoryBtn = document.getElementById('show-history');
const bookmarkCountSpan = document.getElementById('bookmark-count');
const historyPanel = document.getElementById('history-panel');
const historyList = document.getElementById('history-list');
const clearHistoryBtn = document.getElementById('clear-history');
const bookmarksModal = document.getElementById('bookmarks-modal');
const bookmarksList = document.getElementById('bookmarks-list');
const exportBookmarksBtn = document.getElementById('export-bookmarks');
const summarizeBookmarksBtn = document.getElementById('summarize-bookmarks');
const clearBookmarksBtn = document.getElementById('clear-bookmarks');
const sortBySelect = document.getElementById('sort-by');

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    updateBookmarkCount();
    toggleSearchMode();
});

// 이벤트 리스너
searchForm.addEventListener('submit', handleSearch);
exportBtn.addEventListener('click', handleExport);
summarizeBtn.addEventListener('click', handleSummarize);
chatBtn.addEventListener('click', openChatModal);
selectAllCheckbox.addEventListener('change', handleSelectAll);
aiSearchMode.addEventListener('change', toggleSearchMode);
useAiQueryBtn.addEventListener('click', useGeneratedQuery);
showBookmarksBtn.addEventListener('click', openBookmarksModal);
showHistoryBtn.addEventListener('click', toggleHistoryPanel);
clearHistoryBtn.addEventListener('click', clearHistory);
exportBookmarksBtn.addEventListener('click', exportBookmarksToCSV);
summarizeBookmarksBtn.addEventListener('click', summarizeAllBookmarks);
clearBookmarksBtn.addEventListener('click', clearAllBookmarks);
sortBySelect.addEventListener('change', handleSortChange);

// 모달 닫기 버튼
document.querySelectorAll('.close-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const modalType = btn.dataset.modal;
        if (modalType === 'summary') summaryModal.style.display = 'none';
        else if (modalType === 'chat') chatModal.style.display = 'none';
        else if (modalType === 'bookmarks') bookmarksModal.style.display = 'none';
    });
});

// 모달 외부 클릭 시 닫기
window.addEventListener('click', (e) => {
    if (e.target === summaryModal) summaryModal.style.display = 'none';
    if (e.target === chatModal) chatModal.style.display = 'none';
    if (e.target === bookmarksModal) bookmarksModal.style.display = 'none';
});

// 채팅 전송
chatSendBtn.addEventListener('click', sendChatMessage);
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
    }
});

// 탭 전환
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`${btn.dataset.tab}-tab`).classList.add('active');
    });
});

// ==================== 북마크 기능 ====================

function getBookmarks() {
    const data = localStorage.getItem(BOOKMARKS_KEY);
    return data ? JSON.parse(data) : [];
}

function saveBookmarks(bookmarks) {
    localStorage.setItem(BOOKMARKS_KEY, JSON.stringify(bookmarks));
    updateBookmarkCount();
}

function updateBookmarkCount() {
    const bookmarks = getBookmarks();
    bookmarkCountSpan.textContent = bookmarks.length;
}

function isBookmarked(pmid) {
    const bookmarks = getBookmarks();
    return bookmarks.some(b => b.pmid === pmid);
}

function toggleBookmark(pmid) {
    const bookmarks = getBookmarks();
    const index = bookmarks.findIndex(b => b.pmid === pmid);

    if (index > -1) {
        // 북마크 제거
        bookmarks.splice(index, 1);
        saveBookmarks(bookmarks);
    } else {
        // 북마크 추가
        const paper = currentSearch.papers.find(p => p.pmid === pmid);
        if (paper) {
            bookmarks.push({
                pmid: paper.pmid,
                title: paper.title,
                authors: paper.authors,
                journal: paper.journal,
                pub_date: paper.pub_date,
                abstract: paper.abstract,
                keywords: paper.keywords,
                pmc_id: paper.pmc_id,
                citation_count: paper.citation_count,
                bookmarked_at: new Date().toISOString()
            });
            saveBookmarks(bookmarks);
        }
    }

    // UI 업데이트
    const btn = document.querySelector(`.bookmark-btn[data-pmid="${pmid}"]`);
    if (btn) {
        btn.classList.toggle('bookmarked');
        btn.textContent = isBookmarked(pmid) ? '📑 북마크됨' : '📄 북마크';
    }
}

function openBookmarksModal() {
    const bookmarks = getBookmarks();

    if (bookmarks.length === 0) {
        bookmarksList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📑</div>
                <p>북마크된 논문이 없습니다</p>
            </div>
        `;
    } else {
        bookmarksList.innerHTML = bookmarks.map(paper => `
            <div class="paper-card" data-pmid="${paper.pmid}">
                <div class="paper-content">
                    <div class="paper-title" onclick="window.open('https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}/', '_blank')">
                        ${paper.title}
                    </div>
                    <div class="paper-meta">
                        <strong>PMID:</strong> ${paper.pmid} |
                        <strong>저널:</strong> ${paper.journal || 'N/A'} |
                        <strong>출판일:</strong> ${paper.pub_date || 'N/A'}
                    </div>
                    <div class="paper-meta">
                        <strong>저자:</strong> ${paper.authors.slice(0, 3).join(', ')}${paper.authors.length > 3 ? ' 외' : ''}
                    </div>
                    <div class="paper-actions">
                        <button class="paper-action-btn" onclick="removeBookmark('${paper.pmid}')">🗑️ 삭제</button>
                        ${paper.pmc_id ? `
                            <button class="paper-action-btn pdf-available" onclick="openPDF('${paper.pmc_id}')">📄 무료 PDF</button>
                        ` : `
                            <button class="paper-action-btn pdf-unavailable" onclick="alert('이 논문은 무료 PDF를 제공하지 않습니다.')">📄 PDF 없음</button>
                        `}
                    </div>
                </div>
            </div>
        `).join('');
    }

    bookmarksModal.style.display = 'flex';
}

function removeBookmark(pmid) {
    const bookmarks = getBookmarks();
    const index = bookmarks.findIndex(b => b.pmid === pmid);
    if (index > -1) {
        bookmarks.splice(index, 1);
        saveBookmarks(bookmarks);
        openBookmarksModal(); // 새로고침
    }
}

function clearAllBookmarks() {
    if (confirm('모든 북마크를 삭제하시겠습니까?')) {
        localStorage.removeItem(BOOKMARKS_KEY);
        updateBookmarkCount();
        openBookmarksModal();
    }
}

function exportBookmarksToCSV() {
    const bookmarks = getBookmarks();
    if (bookmarks.length === 0) {
        alert('북마크된 논문이 없습니다.');
        return;
    }

    const headers = ['PMID', '제목', '저자', '저널', '출판일', '초록'];
    const rows = bookmarks.map(p => [
        p.pmid,
        `"${p.title.replace(/"/g, '""')}"`,
        `"${p.authors.join('; ')}"`,
        `"${p.journal || ''}"`,
        p.pub_date || '',
        `"${(p.abstract || '').replace(/"/g, '""')}"`
    ]);

    const csv = '\uFEFF' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pubmed_bookmarks_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
}

async function summarizeAllBookmarks() {
    const bookmarks = getBookmarks();
    if (bookmarks.length === 0) {
        alert('북마크된 논문이 없습니다.');
        return;
    }

    showLoading();

    try {
        const response = await fetch('/api/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pmids: bookmarks.map(b => b.pmid),
                language: 'korean'
            })
        });

        const data = await response.json();

        if (response.ok) {
            bookmarksModal.style.display = 'none';
            summaryContent.innerHTML = renderMarkdown(data.summary);
            summaryModal.style.display = 'flex';
        } else {
            alert('요약 생성 실패: ' + (data.detail || '알 수 없는 오류'));
        }
    } catch (error) {
        alert('요약 중 오류가 발생했습니다: ' + error.message);
    } finally {
        hideLoading();
    }
}

// ==================== 검색 히스토리 기능 ====================

function getHistory() {
    const data = localStorage.getItem(HISTORY_KEY);
    return data ? JSON.parse(data) : [];
}

function saveHistory(history) {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
}

function addToHistory(query, aiQuery = null) {
    const history = getHistory();

    // 중복 제거
    const existingIndex = history.findIndex(h => h.query === query);
    if (existingIndex > -1) {
        history.splice(existingIndex, 1);
    }

    // 앞에 추가
    history.unshift({
        query: query,
        aiQuery: aiQuery,
        date: new Date().toISOString()
    });

    // 최대 20개 유지
    if (history.length > 20) {
        history.pop();
    }

    saveHistory(history);
}

function toggleHistoryPanel() {
    if (historyPanel.style.display === 'none') {
        renderHistoryList();
        historyPanel.style.display = 'block';
    } else {
        historyPanel.style.display = 'none';
    }
}

function renderHistoryList() {
    const history = getHistory();

    if (history.length === 0) {
        historyList.innerHTML = '<div class="empty-state">검색 기록이 없습니다</div>';
        return;
    }

    historyList.innerHTML = history.map((item, index) => `
        <div class="history-item" onclick="useHistoryItem(${index})">
            <span class="history-query">${item.query}</span>
            <span class="history-date">${formatDate(item.date)}</span>
            <button class="history-delete" onclick="event.stopPropagation(); deleteHistoryItem(${index})">✕</button>
        </div>
    `).join('');
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return '방금 전';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}분 전`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}시간 전`;
    return date.toLocaleDateString('ko-KR');
}

function useHistoryItem(index) {
    const history = getHistory();
    const item = history[index];

    if (item.aiQuery) {
        aiSearchMode.checked = true;
        toggleSearchMode();
        queryInput.value = item.query;
        generatedQuery = { pubmed_query: item.aiQuery };
    } else {
        aiSearchMode.checked = false;
        toggleSearchMode();
        queryInput.value = item.query;
    }

    historyPanel.style.display = 'none';
    searchForm.dispatchEvent(new Event('submit'));
}

function deleteHistoryItem(index) {
    const history = getHistory();
    history.splice(index, 1);
    saveHistory(history);
    renderHistoryList();
}

function clearHistory() {
    if (confirm('모든 검색 기록을 삭제하시겠습니까?')) {
        localStorage.removeItem(HISTORY_KEY);
        renderHistoryList();
    }
}

// ==================== PDF 다운로드 기능 ====================

function openPDF(pmcId) {
    // PubMed Central PDF 링크
    const pdfUrl = `https://www.ncbi.nlm.nih.gov/pmc/articles/${pmcId}/pdf/`;
    window.open(pdfUrl, '_blank');
}

// ==================== 정렬 기능 ====================

async function handleSortChange() {
    currentSearch.sort_by = sortBySelect.value;
    currentSearch.page = 1; // 정렬 변경 시 첫 페이지로
    await searchPapers();
}

// ==================== 검색 모드 토글 ====================

function toggleSearchMode() {
    if (aiSearchMode.checked) {
        queryLabel.textContent = '검색하고 싶은 내용을 자연어로 입력하세요 *';
        queryInput.placeholder = '예: 폐결절 CT 진단에서 AI 활용 최신 연구';
    } else {
        queryLabel.textContent = '검색 키워드 *';
        queryInput.placeholder = '예: lung nodule CT AI diagnosis';
        aiQueryResult.style.display = 'none';
    }
}

// ==================== 검색 처리 ====================

async function handleSearch(e) {
    e.preventDefault();

    const userQuery = queryInput.value.trim();

    if (aiSearchMode.checked) {
        await generateAndShowQuery(userQuery);
    } else {
        currentSearch.query = userQuery;
        currentSearch.author = document.getElementById('author').value;
        currentSearch.start_date = document.getElementById('start_date').value;
        currentSearch.end_date = document.getElementById('end_date').value;
        currentSearch.page = 1;

        addToHistory(userQuery);
        await searchPapers();
        await loadAnalysis();
    }

    historyPanel.style.display = 'none';
}

async function generateAndShowQuery(naturalQuery) {
    showLoading();

    try {
        const response = await fetch('/api/generate-query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: naturalQuery })
        });

        const data = await response.json();

        if (response.ok) {
            generatedQuery = data;

            aiQueryContent.innerHTML = `
                <div><strong>원본 질문:</strong> ${data.original_query}</div>
                <div class="query-box">${data.pubmed_query}</div>
                <div class="explanation">💡 ${data.explanation}</div>
                <div class="keywords">
                    ${data.keywords.map(k => `<span class="keyword-badge">${k}</span>`).join('')}
                </div>
            `;
            aiQueryResult.style.display = 'block';

            addToHistory(naturalQuery, data.pubmed_query);
            await useGeneratedQuery();
        } else {
            alert('쿼리 생성 실패: ' + (data.detail || '알 수 없는 오류'));
        }
    } catch (error) {
        alert('쿼리 생성 중 오류가 발생했습니다: ' + error.message);
    } finally {
        hideLoading();
    }
}

async function useGeneratedQuery() {
    if (!generatedQuery) return;

    currentSearch.query = generatedQuery.pubmed_query;
    currentSearch.author = document.getElementById('author').value;
    currentSearch.start_date = document.getElementById('start_date').value;
    currentSearch.end_date = document.getElementById('end_date').value;
    currentSearch.page = 1;

    await searchPapers();
    await loadAnalysis();
}

async function searchPapers() {
    showLoading();

    try {
        const params = new URLSearchParams({
            query: currentSearch.query,
            page: currentSearch.page,
            page_size: currentSearch.page_size,
            sort_by: currentSearch.sort_by
        });

        if (currentSearch.author) params.append('author', currentSearch.author);
        if (currentSearch.start_date) params.append('start_date', currentSearch.start_date);
        if (currentSearch.end_date) params.append('end_date', currentSearch.end_date);

        const response = await fetch(`/api/search?${params}`);
        const data = await response.json();

        currentSearch.total = data.total;
        currentSearch.papers = data.papers;

        renderResults();
        resultsSection.style.display = 'block';
        exportBtn.disabled = false;
    } catch (error) {
        alert('검색 중 오류가 발생했습니다: ' + error.message);
    } finally {
        hideLoading();
    }
}

// ==================== 결과 렌더링 ====================

function renderResults() {
    totalCount.textContent = currentSearch.total.toLocaleString();

    papersList.innerHTML = currentSearch.papers.map(paper => {
        const bookmarked = isBookmarked(paper.pmid);
        return `
            <div class="paper-card ${selectedPmids.has(paper.pmid) ? 'selected' : ''}" data-pmid="${paper.pmid}">
                <div class="paper-header">
                    <input type="checkbox" class="paper-checkbox"
                        ${selectedPmids.has(paper.pmid) ? 'checked' : ''}
                        onchange="togglePaper('${paper.pmid}')">
                    <div class="paper-content">
                        <div class="paper-title" onclick="window.open('https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}/', '_blank')">
                            ${paper.title}
                        </div>
                        <div class="paper-meta">
                            <strong>PMID:</strong> ${paper.pmid} |
                            <strong>저널:</strong> ${paper.journal || 'N/A'} |
                            <strong>출판일:</strong> ${paper.pub_date || 'N/A'} |
                            <span class="citation-count" title="피인용 횟수">📊 인용: <strong>${paper.citation_count !== null ? paper.citation_count : '-'}</strong></span>
                        </div>
                        <div class="paper-meta">
                            <strong>저자:</strong> ${paper.authors.slice(0, 5).join(', ')}${paper.authors.length > 5 ? ' 외 ' + (paper.authors.length - 5) + '명' : ''}
                        </div>
                        <div class="paper-abstract" onclick="this.classList.toggle('expanded')">
                            ${paper.abstract || '초록 없음'}
                        </div>
                        ${paper.keywords.length > 0 ? `
                            <div class="paper-keywords">
                                ${paper.keywords.slice(0, 5).map(kw => `<span class="keyword-tag">${kw}</span>`).join('')}
                                ${paper.keywords.length > 5 ? `<span class="keyword-tag">+${paper.keywords.length - 5}</span>` : ''}
                            </div>
                        ` : ''}
                        <div class="paper-actions">
                            <button class="paper-action-btn bookmark-btn ${bookmarked ? 'bookmarked' : ''}"
                                    data-pmid="${paper.pmid}"
                                    onclick="toggleBookmark('${paper.pmid}')">
                                ${bookmarked ? '📑 북마크됨' : '📄 북마크'}
                            </button>
                            ${paper.pmc_id ? `
                                <button class="paper-action-btn pdf-btn pdf-available" onclick="openPDF('${paper.pmc_id}')">
                                    📄 무료 PDF
                                </button>
                            ` : `
                                <button class="paper-action-btn pdf-btn pdf-unavailable" onclick="alert('이 논문은 PubMed Central에서 무료 PDF를 제공하지 않습니다.\\n출판사 사이트에서 확인해주세요.')" title="무료 PDF 없음">
                                    📄 PDF 없음
                                </button>
                            `}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    renderPagination();
    updateActionButtons();
}

function renderPagination() {
    const totalPages = Math.ceil(currentSearch.total / currentSearch.page_size);
    const currentPage = currentSearch.page;

    let buttons = [];

    if (currentPage > 1) {
        buttons.push(`<button class="page-btn" onclick="goToPage(${currentPage - 1})">이전</button>`);
    }

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    for (let i = startPage; i <= endPage; i++) {
        buttons.push(`<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`);
    }

    if (currentPage < totalPages) {
        buttons.push(`<button class="page-btn" onclick="goToPage(${currentPage + 1})">다음</button>`);
    }

    pagination.innerHTML = buttons.join('');
}

async function goToPage(page) {
    currentSearch.page = page;
    await searchPapers();
}

function togglePaper(pmid) {
    if (selectedPmids.has(pmid)) {
        selectedPmids.delete(pmid);
    } else {
        selectedPmids.add(pmid);
    }

    const card = document.querySelector(`.paper-card[data-pmid="${pmid}"]`);
    if (card) {
        card.classList.toggle('selected', selectedPmids.has(pmid));
    }

    updateActionButtons();
    selectAllCheckbox.checked = selectedPmids.size === currentSearch.papers.length;
}

function handleSelectAll() {
    if (selectAllCheckbox.checked) {
        currentSearch.papers.forEach(p => selectedPmids.add(p.pmid));
    } else {
        currentSearch.papers.forEach(p => selectedPmids.delete(p.pmid));
    }

    document.querySelectorAll('.paper-checkbox').forEach(cb => {
        cb.checked = selectAllCheckbox.checked;
    });

    document.querySelectorAll('.paper-card').forEach(card => {
        card.classList.toggle('selected', selectAllCheckbox.checked);
    });

    updateActionButtons();
}

function updateActionButtons() {
    const count = selectedPmids.size;

    summarizeBtn.disabled = count === 0;
    summarizeBtn.textContent = count > 0
        ? `선택한 논문 AI 요약 (${count}개)`
        : '선택한 논문 AI 요약';

    chatBtn.disabled = count === 0;
    chatBtn.textContent = count > 0
        ? `💬 AI와 대화 (${count}개)`
        : '💬 AI와 대화';
}

function handleExport() {
    const params = new URLSearchParams({
        query: currentSearch.query,
        max_results: 100
    });

    if (currentSearch.author) params.append('author', currentSearch.author);
    if (currentSearch.start_date) params.append('start_date', currentSearch.start_date);
    if (currentSearch.end_date) params.append('end_date', currentSearch.end_date);

    window.location.href = `/api/export/csv?${params}`;
}

// ==================== 마크다운 렌더링 ====================

function renderMarkdown(text) {
    if (typeof marked !== 'undefined') {
        return marked.parse(text);
    }
    return text.replace(/\n/g, '<br>');
}

// ==================== AI 요약 ====================

async function handleSummarize() {
    if (selectedPmids.size === 0) return;

    showLoading();

    try {
        const response = await fetch('/api/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pmids: Array.from(selectedPmids),
                language: 'korean'
            })
        });

        const data = await response.json();

        if (response.ok) {
            summaryContent.innerHTML = renderMarkdown(data.summary);
            summaryModal.style.display = 'flex';
        } else {
            alert('요약 생성 실패: ' + (data.detail || '알 수 없는 오류'));
        }
    } catch (error) {
        alert('요약 중 오류가 발생했습니다: ' + error.message);
    } finally {
        hideLoading();
    }
}

// ==================== 채팅 ====================

function openChatModal() {
    if (selectedPmids.size === 0) return;

    chatPaperCount.textContent = selectedPmids.size;
    chatHistory = [];
    chatMessages.innerHTML = `
        <div class="chat-message assistant">
            <div class="markdown-content">
                안녕하세요! 선택하신 <strong>${selectedPmids.size}개</strong>의 논문에 대해 질문해 주세요.<br>
                일반 의학 + 인터벤션 영상의학과 관점에서 답변해 드립니다.<br><br>
                예를 들어:<br>
                • 이 연구들의 주요 결과를 요약해줘<br>
                • 시술 성공률과 합병증은?<br>
                • 어떤 접근법/기법이 사용되었나?<br>
                • 임상에서 적용할 때 주의점은?
            </div>
        </div>
    `;
    chatModal.style.display = 'flex';
    chatInput.focus();
}

async function sendChatMessage() {
    const message = chatInput.value.trim();
    if (!message || selectedPmids.size === 0) return;

    appendChatMessage('user', message);
    chatInput.value = '';

    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'chat-message assistant';
    loadingMsg.innerHTML = '<div class="markdown-content">🤔 분석 중...</div>';
    chatMessages.appendChild(loadingMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pmids: Array.from(selectedPmids),
                message: message,
                history: chatHistory,
                language: 'korean'
            })
        });

        const data = await response.json();
        loadingMsg.remove();

        if (response.ok) {
            chatHistory.push({ role: 'user', content: message });
            chatHistory.push({ role: 'assistant', content: data.response });
            appendChatMessage('assistant', data.response);
        } else {
            appendChatMessage('assistant', '오류가 발생했습니다: ' + (data.detail || '알 수 없는 오류'));
        }
    } catch (error) {
        loadingMsg.remove();
        appendChatMessage('assistant', '오류가 발생했습니다: ' + error.message);
    }
}

function appendChatMessage(role, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${role}`;

    if (role === 'assistant') {
        msgDiv.innerHTML = `<div class="markdown-content">${renderMarkdown(content)}</div>`;
    } else {
        msgDiv.textContent = content;
    }

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ==================== 분석 ====================

async function loadAnalysis() {
    const params = new URLSearchParams({ query: currentSearch.query });
    if (currentSearch.author) params.append('author', currentSearch.author);
    if (currentSearch.start_date) params.append('start_date', currentSearch.start_date);
    if (currentSearch.end_date) params.append('end_date', currentSearch.end_date);

    try {
        const [trendsRes, keywordsRes, authorsRes] = await Promise.all([
            fetch(`/api/analyze/trends?${params}`),
            fetch(`/api/analyze/keywords?${params}`),
            fetch(`/api/analyze/authors?${params}`)
        ]);

        const trends = await trendsRes.json();
        const keywords = await keywordsRes.json();
        const authors = await authorsRes.json();

        renderTrendsChart(trends);
        renderKeywordsChart(keywords);
        renderAuthorsList(authors);
    } catch (error) {
        console.error('분석 데이터 로드 실패:', error);
    }
}

function renderTrendsChart(data) {
    const ctx = document.getElementById('trends-chart').getContext('2d');
    if (trendsChart) trendsChart.destroy();

    trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.year),
            datasets: [{
                label: '논문 수',
                data: data.map(d => d.count),
                borderColor: '#159895',
                backgroundColor: 'rgba(21, 152, 149, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

function renderKeywordsChart(data) {
    const ctx = document.getElementById('keywords-chart').getContext('2d');
    if (keywordsChart) keywordsChart.destroy();

    const topData = data.slice(0, 10);

    keywordsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topData.map(d => d.keyword.length > 20 ? d.keyword.slice(0, 20) + '...' : d.keyword),
            datasets: [{
                label: '빈도',
                data: topData.map(d => d.count),
                backgroundColor: '#1a5f7a'
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            plugins: { legend: { display: false } }
        }
    });
}

function renderAuthorsList(data) {
    const authorsList = document.getElementById('authors-list');
    authorsList.innerHTML = data.slice(0, 15).map(d => `
        <div class="stats-item">
            <span>${d.author}</span>
            <strong>${d.count}</strong>
        </div>
    `).join('');
}

// ==================== 로딩 ====================

function showLoading() {
    loading.style.display = 'flex';
}

function hideLoading() {
    loading.style.display = 'none';
}
