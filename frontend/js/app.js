// MediaGrab - Social Media Video Downloader Client Application

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    if (window.lucide) {
        lucide.createIcons();
    }

    // DOM Elements
    const downloadForm = document.getElementById('downloadForm');
    const videoUrlInput = document.getElementById('videoUrl');
    const clearBtn = document.getElementById('clearBtn');
    const pasteBtn = document.getElementById('pasteBtn');
    const submitBtn = document.getElementById('submitBtn');
    const submitIcon = document.getElementById('submitIcon');
    const submitText = document.getElementById('submitText');
    const detectedIcon = document.getElementById('detectedIcon');

    const loadingState = document.getElementById('loadingState');
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    const closeErrorBtn = document.getElementById('closeErrorBtn');

    const resultsSection = document.getElementById('resultsSection');
    const videoThumbnail = document.getElementById('videoThumbnail');
    const videoDuration = document.getElementById('videoDuration');
    const videoPlatformBadge = document.getElementById('videoPlatformBadge');
    const videoTitle = document.getElementById('videoTitle');
    const videoAuthor = document.getElementById('videoAuthor');

    const tabVideoBtn = document.getElementById('tabVideoBtn');
    const tabAudioBtn = document.getElementById('tabAudioBtn');
    const videoFormatsPane = document.getElementById('videoFormatsPane');
    const audioFormatsPane = document.getElementById('audioFormatsPane');
    const videoFormatsList = document.getElementById('videoFormatsList');
    const audioFormatsList = document.getElementById('audioFormatsList');
    const videoCountBadge = document.getElementById('videoCountBadge');
    const audioCountBadge = document.getElementById('audioCountBadge');

    // Modal elements
    const progressModal = document.getElementById('progressModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const modalTitle = document.getElementById('modalTitle');
    const modalStatusMsg = document.getElementById('modalStatusMsg');
    const modalProgressBar = document.getElementById('modalProgressBar');
    const modalProgressText = document.getElementById('modalProgressText');
    const modalMetaText = document.getElementById('modalMetaText');
    const modalIconContainer = document.getElementById('modalIconContainer');
    const modalActions = document.getElementById('modalActions');
    const modalDownloadLink = document.getElementById('modalDownloadLink');

    let currentVideoData = null;
    let pollInterval = null;

    // Detect platform as user types or pastes
    function updateDetectedPlatform(url) {
        const val = url.toLowerCase().trim();
        if (!val) {
            detectedIcon.innerHTML = `<i data-lucide="link" class="w-5 h-5"></i>`;
            clearBtn.classList.add('hidden');
            if (window.lucide) lucide.createIcons();
            return;
        }

        clearBtn.classList.remove('hidden');

        if (val.includes('youtube.com') || val.includes('youtu.be')) {
            detectedIcon.innerHTML = `<span class="text-red-500 font-extrabold text-lg">▶</span>`;
        } else if (val.includes('instagram.com')) {
            detectedIcon.innerHTML = `<span class="text-pink-500 font-extrabold text-base">📷</span>`;
        } else if (val.includes('tiktok.com')) {
            detectedIcon.innerHTML = `<span class="text-cyan-400 font-extrabold text-base">🎵</span>`;
        } else if (val.includes('twitter.com') || val.includes('x.com')) {
            detectedIcon.innerHTML = `<span class="text-sky-400 font-extrabold text-base">𝕏</span>`;
        } else if (val.includes('facebook.com') || val.includes('fb.watch')) {
            detectedIcon.innerHTML = `<span class="text-blue-500 font-extrabold text-base">📘</span>`;
        } else if (val.includes('reddit.com')) {
            detectedIcon.innerHTML = `<span class="text-orange-500 font-extrabold text-base">💬</span>`;
        } else {
            detectedIcon.innerHTML = `<i data-lucide="video" class="w-5 h-5 text-indigo-400"></i>`;
            if (window.lucide) lucide.createIcons();
        }
    }

    videoUrlInput.addEventListener('input', (e) => {
        updateDetectedPlatform(e.target.value);
    });

    clearBtn.addEventListener('click', () => {
        videoUrlInput.value = '';
        updateDetectedPlatform('');
        videoUrlInput.focus();
    });

    // Clipboard Paste Button
    pasteBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                videoUrlInput.value = text.trim();
                updateDetectedPlatform(videoUrlInput.value);
                showToast('Link pasted from clipboard', 'info');
                // Automatically fetch
                fetchVideoMetadata(videoUrlInput.value);
            }
        } catch (err) {
            showToast('Please allow clipboard permission or paste manually.', 'error');
        }
    });

    // Sample Links
    document.querySelectorAll('.sample-link').forEach(btn => {
        btn.addEventListener('click', () => {
            const sampleUrl = btn.getAttribute('data-url');
            videoUrlInput.value = sampleUrl;
            updateDetectedPlatform(sampleUrl);
            fetchVideoMetadata(sampleUrl);
        });
    });

    // Close error
    closeErrorBtn.addEventListener('click', () => {
        errorAlert.classList.add('hidden');
    });

    // Form Submit
    downloadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const url = videoUrlInput.value.trim();
        if (!url) return;
        fetchVideoMetadata(url);
    });

    // Fetch video info API
    async function fetchVideoMetadata(url) {
        // Reset states
        errorAlert.classList.add('hidden');
        resultsSection.classList.add('hidden');
        loadingState.classList.remove('hidden');

        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-75', 'cursor-not-allowed');
        submitText.textContent = 'Analyzing...';

        try {
            const response = await fetch('/api/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to extract video information.');
            }

            currentVideoData = data;
            renderResults(data);

        } catch (err) {
            errorMessage.textContent = err.message || 'An error occurred while fetching video.';
            errorAlert.classList.remove('hidden');
        } finally {
            loadingState.classList.add('hidden');
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-75', 'cursor-not-allowed');
            submitText.textContent = 'Fetch Video';
        }
    }

    // Render results
    function renderResults(data) {
        // Thumbnail & Info
        videoThumbnail.src = data.thumbnail || 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg"/>';
        videoDuration.textContent = data.duration_str || '00:00';
        videoTitle.textContent = data.title;
        videoAuthor.textContent = data.uploader;

        // Platform badge
        videoPlatformBadge.textContent = data.platform?.name || 'Video';
        if (data.platform?.color) {
            videoPlatformBadge.style.backgroundColor = data.platform.color;
        }

        // Render Video Qualities
        videoFormatsList.innerHTML = '';
        const vList = data.video_qualities || [];
        videoCountBadge.textContent = vList.length;

        vList.forEach(item => {
            const row = document.createElement('div');
            row.className = 'format-item p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between gap-3';
            
            row.innerHTML = `
                <div class="flex items-center gap-3">
                    <span class="px-2 py-1 rounded-md text-xs font-bold ${item.is_best ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-300'}">
                        ${item.badge}
                    </span>
                    <div>
                        <div class="font-bold text-sm text-white flex items-center gap-2">
                            <span>${item.label}</span>
                            ${item.is_best ? '<span class="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Best</span>' : ''}
                        </div>
                        <div class="text-[11px] text-slate-400 uppercase tracking-wide">${item.ext} • High Definition Video</div>
                    </div>
                </div>

                <div class="text-xs font-semibold text-slate-300">
                    ${item.size_human}
                </div>

                <div>
                    <button
                        type="button"
                        class="download-action-btn px-4 py-2 rounded-lg text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/20 flex items-center gap-1.5 cursor-pointer active:scale-95 transition-all"
                        data-type="video"
                        data-quality="${item.id}"
                        data-label="${item.label}"
                    >
                        <i data-lucide="download" class="w-3.5 h-3.5"></i>
                        <span>Download</span>
                    </button>
                </div>
            `;
            videoFormatsList.appendChild(row);
        });

        // Render Audio Qualities
        audioFormatsList.innerHTML = '';
        const aList = data.audio_qualities || [];
        audioCountBadge.textContent = aList.length;

        aList.forEach(item => {
            const row = document.createElement('div');
            row.className = 'format-item p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between gap-3';

            row.innerHTML = `
                <div class="flex items-center gap-3">
                    <span class="px-2 py-1 rounded-md text-xs font-bold bg-purple-600 text-white">
                        ${item.badge}
                    </span>
                    <div>
                        <div class="font-bold text-sm text-white flex items-center gap-2">
                            <span>${item.label}</span>
                            ${item.bitrate === '320' ? '<span class="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">Studio</span>' : ''}
                        </div>
                        <div class="text-[11px] text-slate-400">${item.note}</div>
                    </div>
                </div>

                <div class="text-xs font-semibold text-slate-300">
                    ${item.size_human}
                </div>

                <div>
                    <button
                        type="button"
                        class="download-action-btn px-4 py-2 rounded-lg text-xs font-bold text-white bg-purple-600 hover:bg-purple-500 shadow-md shadow-purple-600/20 flex items-center gap-1.5 cursor-pointer active:scale-95 transition-all"
                        data-type="audio"
                        data-quality="${item.id}"
                        data-label="${item.label}"
                    >
                        <i data-lucide="music" class="w-3.5 h-3.5"></i>
                        <span>Download MP3</span>
                    </button>
                </div>
            `;
            audioFormatsList.appendChild(row);
        });

        // Show results section
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Bind download buttons
        document.querySelectorAll('.download-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const type = btn.getAttribute('data-type');
                const qualityId = btn.getAttribute('data-quality');
                const label = btn.getAttribute('data-label');
                startDownloadProcess(type, qualityId, label);
            });
        });

        if (window.lucide) {
            lucide.createIcons();
        }
    }

    // Tab Switching
    tabVideoBtn.addEventListener('click', () => {
        tabVideoBtn.className = "px-4 py-1.5 rounded-lg text-xs sm:text-sm font-semibold flex items-center gap-2 transition-all bg-indigo-600 text-white shadow-sm";
        tabAudioBtn.className = "px-4 py-1.5 rounded-lg text-xs sm:text-sm font-semibold flex items-center gap-2 transition-all text-slate-400 hover:text-white hover:bg-slate-800";
        videoFormatsPane.classList.remove('hidden');
        audioFormatsPane.classList.add('hidden');
    });

    tabAudioBtn.addEventListener('click', () => {
        tabAudioBtn.className = "px-4 py-1.5 rounded-lg text-xs sm:text-sm font-semibold flex items-center gap-2 transition-all bg-purple-600 text-white shadow-sm";
        tabVideoBtn.className = "px-4 py-1.5 rounded-lg text-xs sm:text-sm font-semibold flex items-center gap-2 transition-all text-slate-400 hover:text-white hover:bg-slate-800";
        audioFormatsPane.classList.remove('hidden');
        videoFormatsPane.classList.add('hidden');
    });

    // Start Download & Track Progress
    async function startDownloadProcess(type, qualityId, label) {
        if (!currentVideoData) return;

        // Open modal
        progressModal.classList.remove('hidden');
        modalTitle.textContent = `Preparing ${label}`;
        modalStatusMsg.textContent = 'Connecting to media stream...';
        modalProgressBar.style.width = '0%';
        modalProgressText.textContent = '0%';
        modalMetaText.textContent = '';
        modalActions.classList.add('hidden');
        modalIconContainer.innerHTML = `<i data-lucide="loader-2" class="w-7 h-7 text-indigo-400 animate-spin"></i>`;
        if (window.lucide) lucide.createIcons();

        try {
            const startRes = await fetch('/api/download/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: currentVideoData.url,
                    type: type,
                    quality_id: qualityId
                })
            });

            const startData = await startRes.json();
            if (!startRes.ok) throw new Error(startData.detail || 'Could not start download');

            const jobId = startData.job_id;
            pollJobStatus(jobId);

        } catch (err) {
            modalTitle.textContent = 'Download Failed';
            modalStatusMsg.textContent = err.message || 'An error occurred.';
            modalIconContainer.innerHTML = `<i data-lucide="alert-circle" class="w-7 h-7 text-rose-500"></i>`;
            if (window.lucide) lucide.createIcons();
        }
    }

    // Poll Job Status
    function pollJobStatus(jobId) {
        if (pollInterval) clearInterval(pollInterval);

        pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/download/status/${jobId}`);
                if (!res.ok) throw new Error('Status check failed');

                const data = await res.json();
                const percent = Math.min(Math.max(data.percent || 0, 5), 100);

                modalProgressBar.style.width = `${percent}%`;
                modalProgressText.textContent = `${percent}%`;
                modalStatusMsg.textContent = data.message || 'Processing media...';

                if (data.speed || data.eta) {
                    modalMetaText.textContent = `${data.speed} ${data.eta ? '• ETA ' + data.eta : ''}`;
                }

                if (data.status === 'ready') {
                    clearInterval(pollInterval);
                    modalTitle.textContent = 'Download Ready!';
                    modalStatusMsg.textContent = `File created successfully (${data.file_size || ''})`;
                    modalProgressBar.style.width = '100%';
                    modalProgressText.textContent = '100%';
                    modalIconContainer.innerHTML = `<i data-lucide="check-circle" class="w-7 h-7 text-emerald-400"></i>`;
                    modalActions.classList.remove('hidden');
                    modalDownloadLink.href = data.download_url;

                    if (window.lucide) lucide.createIcons();

                    // Auto-trigger browser download
                    triggerBrowserDownload(data.download_url);
                    showToast('Your download has started!', 'success');
                } else if (data.status === 'error') {
                    clearInterval(pollInterval);
                    modalTitle.textContent = 'Processing Failed';
                    modalStatusMsg.textContent = data.error || 'Failed to download or convert media.';
                    modalIconContainer.innerHTML = `<i data-lucide="alert-triangle" class="w-7 h-7 text-rose-500"></i>`;
                    if (window.lucide) lucide.createIcons();
                }
            } catch (err) {
                clearInterval(pollInterval);
                modalTitle.textContent = 'Connection Error';
                modalStatusMsg.textContent = err.message;
            }
        }, 800);
    }

    function triggerBrowserDownload(url) {
        const tempLink = document.createElement('a');
        tempLink.href = url;
        tempLink.setAttribute('download', '');
        document.body.appendChild(tempLink);
        tempLink.click();
        document.body.removeChild(tempLink);
    }

    closeModalBtn.addEventListener('click', () => {
        if (pollInterval) clearInterval(pollInterval);
        progressModal.classList.add('hidden');
    });

    // Toast notification helper
    function showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `p-3.5 rounded-xl shadow-lg border text-xs font-semibold flex items-center gap-2 pointer-events-auto transition-all animate-fade-in ${
            type === 'success' ? 'bg-emerald-950 border-emerald-800 text-emerald-200' :
            type === 'error' ? 'bg-rose-950 border-rose-800 text-rose-200' :
            'bg-slate-900 border-slate-700 text-slate-200'
        }`;

        const iconName = type === 'success' ? 'check-circle' : type === 'error' ? 'alert-circle' : 'info';
        toast.innerHTML = `<i data-lucide="${iconName}" class="w-4 h-4 shrink-0"></i><span>${message}</span>`;
        toastContainer.appendChild(toast);
        if (window.lucide) lucide.createIcons();

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }
});
