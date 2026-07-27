/**
 * VidVelocity PRO — Client-Side Logic & Interactive Engine
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const urlInput = document.getElementById('url-input');
    const pasteBtn = document.getElementById('paste-btn');
    const fetchBtn = document.getElementById('fetch-btn');
    const fetchSpinner = document.getElementById('fetch-spinner');
    const errorMessage = document.getElementById('error-message');
    
    const previewSection = document.getElementById('preview-section');
    const videoThumb = document.getElementById('video-thumb');
    const videoDuration = document.getElementById('video-duration');
    const videoPlatform = document.getElementById('video-platform');
    const videoTitle = document.getElementById('video-title');
    const videoUploader = document.querySelector('#video-uploader span');
    const formatOptionsContainer = document.getElementById('format-options');
    const downloadBtn = document.getElementById('download-btn');
    
    const progressContainer = document.getElementById('progress-container');
    const progressStatusText = document.getElementById('progress-status-text');
    const progressPercentage = document.getElementById('progress-percentage');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const statSpeed = document.getElementById('stat-speed');
    const statEta = document.getElementById('stat-eta');
    const statSize = document.getElementById('stat-size');
    const completedActions = document.getElementById('completed-actions');
    const openFileBtn = document.getElementById('open-file-btn');
    
    const historyList = document.getElementById('history-list');
    const refreshHistoryBtn = document.getElementById('refresh-history-btn');
    const openRootBtn = document.getElementById('open-root-btn');
    
    // State
    let currentVideoData = null;
    let selectedFormatId = 'best';
    let activeTaskId = null;
    let pollInterval = null;

    // Load initial history
    fetchHistory();

    // --- 1. Clipboard Paste ---
    pasteBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text && text.trim().startsWith('http')) {
                urlInput.value = text.trim();
                fetchVideoInfo();
            } else if (text) {
                urlInput.value = text.trim();
                showError("The copied text doesn't look like a valid web URL.");
            } else {
                showError("Clipboard is empty.");
            }
        } catch (err) {
            // Fallback for browsers without clipboard read permission
            urlInput.focus();
            showError("Please paste your link directly using Ctrl+V or right-click.");
        }
    });

    // --- 2. Fetch Video Info ---
    fetchBtn.addEventListener('click', fetchVideoInfo);
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') fetchVideoInfo();
    });

    async function fetchVideoInfo() {
        const url = urlInput.value.trim();
        if (!url) {
            showError("Please paste a video URL first.");
            urlInput.focus();
            return;
        }

        hideError();
        setLoading(true);
        previewSection.classList.add('hidden');
        progressContainer.classList.add('hidden');
        completedActions.classList.add('hidden');

        try {
            const res = await fetch('/api/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await res.json();
            if (!res.ok || data.error) {
                throw new Error(data.error || "Failed to fetch video details.");
            }

            currentVideoData = data;
            renderPreview(data);
        } catch (err) {
            showError(err.message);
        } finally {
            setLoading(false);
        }
    }

    function renderPreview(data) {
        videoThumb.src = data.thumbnail || 'https://via.placeholder.com/640x360/121520/6366f1?text=No+Thumbnail';
        videoDuration.textContent = data.duration || 'N/A';
        videoPlatform.textContent = data.platform || 'Video';
        videoTitle.textContent = data.title || 'Untitled Video';
        videoUploader.textContent = data.uploader || 'Unknown Creator';

        // Render Format Buttons
        formatOptionsContainer.innerHTML = '';
        data.formats.forEach((f, idx) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `format-option-btn ${f.id === 'best' ? 'active' : ''}`;
            btn.innerHTML = `
                <span class="f-label">${f.label}</span>
                <span class="f-desc">${f.desc}</span>
            `;
            btn.addEventListener('click', () => {
                document.querySelectorAll('.format-option-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedFormatId = f.id;
            });
            formatOptionsContainer.appendChild(btn);
        });
        
        selectedFormatId = 'best';
        previewSection.classList.remove('hidden');
        previewSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // --- 3. Start Download ---
    downloadBtn.addEventListener('click', async () => {
        if (!currentVideoData) return;

        downloadBtn.disabled = true;
        downloadBtn.style.opacity = '0.7';
        progressContainer.classList.remove('hidden');
        completedActions.classList.add('hidden');
        
        progressStatusText.textContent = "Connecting to download server...";
        progressPercentage.textContent = "0%";
        progressBarFill.style.width = "0%";
        statSpeed.textContent = "Starting...";
        statEta.textContent = "Calculating...";
        statSize.textContent = "N/A";

        try {
            const res = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: currentVideoData.url,
                    format: selectedFormatId,
                    title: currentVideoData.title,
                    thumbnail: currentVideoData.thumbnail,
                    platform: currentVideoData.platform
                })
            });

            const data = await res.json();
            if (!res.ok || data.error) {
                throw new Error(data.error || "Could not initiate download.");
            }

            activeTaskId = data.task_id;
            startPolling(activeTaskId);
            fetchHistory(); // Update history list
        } catch (err) {
            showError(err.message);
            downloadBtn.disabled = false;
            downloadBtn.style.opacity = '1';
        }
    });

    // --- 4. Progress Polling ---
    function startPolling(taskId) {
        if (pollInterval) clearInterval(pollInterval);

        pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/status/${taskId}`);
                if (!res.ok) return;

                const data = await res.json();
                
                if (data.status === 'downloading') {
                    const prog = data.progress || 0;
                    progressPercentage.textContent = `${prog}%`;
                    progressBarFill.style.width = `${prog}%`;
                    progressStatusText.textContent = "Downloading high-speed streams...";
                    statSpeed.textContent = data.speed || 'N/A';
                    statEta.textContent = data.eta || 'N/A';
                    statSize.textContent = data.total_size || 'N/A';
                } else if (data.status === 'processing') {
                    progressPercentage.textContent = "100%";
                    progressBarFill.style.width = "100%";
                    progressStatusText.textContent = "Merging HD Video & Audio streams...";
                    statSpeed.textContent = "Processing...";
                    statEta.textContent = "0s";
                } else if (data.status === 'finished') {
                    clearInterval(pollInterval);
                    progressPercentage.textContent = "100%";
                    progressBarFill.style.width = "100%";
                    progressStatusText.textContent = "Download Completed!";
                    statSpeed.textContent = "Done";
                    statEta.textContent = "0s";
                    
                    completedActions.classList.remove('hidden');
                    downloadBtn.disabled = false;
                    downloadBtn.style.opacity = '1';
                    
                    // Bind open file button
                    openFileBtn.onclick = () => openFolder(data.filepath, taskId);
                    fetchHistory();
                } else if (data.status === 'error') {
                    clearInterval(pollInterval);
                    showError(`Download error: ${data.error || 'Unknown error occurred.'}`);
                    progressStatusText.textContent = "Failed";
                    downloadBtn.disabled = false;
                    downloadBtn.style.opacity = '1';
                    fetchHistory();
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }, 600);
    }

    // --- 5. Open Folders & Files ---
    async function openFolder(filepath, taskId) {
        try {
            await fetch('/api/open-folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filepath, task_id: taskId })
            });
        } catch (err) {
            console.error("Failed to open folder:", err);
        }
    }

    openRootBtn.addEventListener('click', async () => {
        try {
            await fetch('/api/open-root-folder', { method: 'POST' });
        } catch (err) {
            console.error("Failed to open root folder:", err);
        }
    });

    // --- 6. History Management ---
    refreshHistoryBtn.addEventListener('click', fetchHistory);

    async function fetchHistory() {
        try {
            const res = await fetch('/api/history');
            if (!res.ok) return;
            const data = await res.json();
            renderHistory(data.downloads);
        } catch (err) {
            console.error("Error fetching history:", err);
        }
    }

    function renderHistory(downloads) {
        if (!downloads || downloads.length === 0) {
            historyList.innerHTML = `
                <div class="empty-history">
                    <p>No downloads yet in this session. Paste a video link above to get started!</p>
                </div>
            `;
            return;
        }

        historyList.innerHTML = '';
        downloads.forEach(d => {
            const item = document.createElement('div');
            item.className = 'history-item';
            
            let statusText = d.status;
            let statusClass = d.status;
            if (d.status === 'finished') statusText = 'Completed';
            else if (d.status === 'downloading') statusText = `${d.progress || 0}%`;

            item.innerHTML = `
                <div class="h-info">
                    <img class="h-thumb" src="${d.thumbnail || 'https://via.placeholder.com/64x36/121520/6366f1?text=Vid'}" alt="thumb">
                    <div class="h-text">
                        <div class="h-title" title="${d.title}">${d.title || d.url}</div>
                        <div class="h-meta">
                            <span>${d.platform || 'Video'}</span>
                            <span>•</span>
                            <span class="badge-status ${statusClass}">${statusText}</span>
                        </div>
                    </div>
                </div>
                <div class="h-actions">
                    <button class="btn-open-folder-sm" title="Show in Folder">
                        📂 Show in Folder
                    </button>
                </div>
            `;

            const openBtn = item.querySelector('.btn-open-folder-sm');
            openBtn.addEventListener('click', () => openFolder(d.filepath, d.id));
            historyList.appendChild(item);
        });
    }

    // --- Helper Functions ---
    function setLoading(isLoading) {
        if (isLoading) {
            fetchBtn.disabled = true;
            fetchBtn.querySelector('.btn-text').classList.add('hidden');
            fetchSpinner.classList.remove('hidden');
        } else {
            fetchBtn.disabled = false;
            fetchBtn.querySelector('.btn-text').classList.remove('hidden');
            fetchSpinner.classList.add('hidden');
        }
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorMessage.classList.remove('hidden');
    }

    function hideError() {
        errorMessage.textContent = '';
        errorMessage.classList.add('hidden');
    }
});
