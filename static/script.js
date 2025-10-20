(function(){
	const library = document.getElementById('library');
	const expandAllBtn = document.getElementById('expandAll');
	const collapseAllBtn = document.getElementById('collapseAll');
	const modal = document.getElementById('playerModal');
	const closeModal = document.getElementById('closeModal');
	const player = document.getElementById('player');
	const playerTitle = document.getElementById('playerTitle');
	const summarizeBtn = document.getElementById('summarizeBtn');
	const summarySection = document.getElementById('summarySection');
	const summaryStatus = document.getElementById('summaryStatus');
	const summaryContent = document.getElementById('summaryContent');
	const summaryVersionSelect = document.getElementById('summaryVersionSelect');
	const modelSelect = document.getElementById('modelSelect');
	const modalPlayBtn = document.getElementById('modalPlayBtn');
	const modalVideoRating = document.getElementById('modalVideoRating');
	const courseSidebar = document.getElementById('courseSidebar');
	const courseList = document.getElementById('courseList');
	const mobileMenuBtn = document.getElementById('mobileMenuBtn');
	const syncStatus = document.getElementById('syncStatus');
	const syncModal = document.getElementById('syncModal');
	const closeSyncModal = document.getElementById('closeSyncModal');
	const createSyncBtn = document.getElementById('createSyncBtn');
	const joinSyncBtn = document.getElementById('joinSyncBtn');
	const syncCodeInput = document.getElementById('syncCodeInput');
	const syncStatusDisplay = document.getElementById('syncStatusDisplay');
	const syncResult = document.getElementById('syncResult');
	

	let libraryData = [];
	let filtered = [];
	let selectedCourse = null; // Track currently selected/filtered course
	let currentModalPath = null; // Which video is open in modal
	let activeSummary = { path: null, taskId: null }; // Track in-progress summary
	let transcriptJPFallback = ''; // Fallback transcript containing [JUMP_POINTS] for current video
	
	// Debug: Check if elements are found
	console.log('Course sidebar element:', courseSidebar);
	console.log('Course list element:', courseList);
	console.log('Mobile menu button:', mobileMenuBtn);

	function getProgressKey(item){
		return `progress:${item.path}`;
	}

	function getPlayedKey(item){
		return `played:${item.path}`;
	}
	
function getRatingKey(courseName){
	return `rating:${courseName}`;
}

function getRating(courseName){
	const rating = window.storageManager.getItem(getRatingKey(courseName));
	return rating ? parseInt(rating) : 0;
}

async function setRating(courseName, rating){
	await window.storageManager.setItem(getRatingKey(courseName), rating.toString());
}

function getVideoRatingKey(videoPath){
	return `videoRating:${videoPath}`;
}

function getVideoRating(videoPath){
	const rating = window.storageManager.getItem(getVideoRatingKey(videoPath));
	return rating ? parseInt(rating) : 0;
}

async function setVideoRating(videoPath, rating){
	await window.storageManager.setItem(getVideoRatingKey(videoPath), rating.toString());
}

	async function saveProgress(item){
		await window.storageManager.setItem(getProgressKey(item), String(player.currentTime || 0));
	}

	function loadProgress(item){
		const v = Number(window.storageManager.getItem(getProgressKey(item)) || 0);
		if (!Number.isFinite(v)) return 0;
		return v;
	}

	async function markAsPlayed(item){
		await window.storageManager.setItem(getPlayedKey(item), 'true');
	}

	function isPlayed(item){
		return window.storageManager.getItem(getPlayedKey(item)) === 'true';
	}

	// Update sync status indicator
	async function updateSyncStatus() {
		if (!syncStatus) return;
		
		const status = window.storageManager.getSyncStatus();
		const icon = syncStatus.querySelector('.sync-icon');
		const text = syncStatus.querySelector('.sync-text');
		
		syncStatus.className = 'sync-status';
		
		// Check if user is in a sync group
		let syncGroupStatus = null;
		try {
			const response = await fetch('/api/sync/status');
			if (response.ok) {
				syncGroupStatus = await response.json();
			}
		} catch (error) {
			console.log('Could not fetch sync status:', error.message);
		}
		
		if (!status.online) {
			syncStatus.classList.add('offline');
			icon.textContent = '📴';
			text.textContent = 'Offline';
		} else if (syncGroupStatus && syncGroupStatus.synced) {
			icon.textContent = '🔗';
			text.textContent = `Synced (${syncGroupStatus.device_count})`;
		} else if (status.pendingChanges > 0) {
			syncStatus.classList.add('syncing');
			icon.textContent = '🔄';
			text.textContent = 'Syncing';
		} else {
			icon.textContent = '☁️';
			text.textContent = 'Local';
		}
		
		const tooltip = syncGroupStatus && syncGroupStatus.synced 
			? `Synced with ${syncGroupStatus.device_count} devices - Click to manage`
			: 'Click to sync with other devices';
		syncStatus.title = tooltip;
	}

	// Sync Group Management
	async function openSyncModal() {
		syncModal.classList.remove('hidden');
		await updateSyncStatusDisplay();
	}

	async function closeSyncModalFunc() {
		syncModal.classList.add('hidden');
		syncResult.classList.add('hidden');
		syncCodeInput.value = '';
	}

	async function updateSyncStatusDisplay() {
		if (!syncStatusDisplay) return;

		try {
			const response = await fetch('/api/sync/status');
			if (!response.ok) {
				syncStatusDisplay.innerHTML = '<p style="color: #f44336;">Sync service unavailable</p>';
				return;
			}

			const status = await response.json();
			
			if (status.synced) {
				const expiresAt = new Date(status.expires_at);
				const hoursLeft = Math.max(0, Math.ceil((expiresAt - new Date()) / (1000 * 60 * 60)));
				
				syncStatusDisplay.innerHTML = `
					<div class="sync-code-display">
						<div>Your sync code:</div>
						<div class="sync-code-large">${status.sync_code}</div>
						<div style="font-size: 12px; color: var(--muted);">Expires in ${hoursLeft} hours</div>
					</div>
					<div class="device-list">
						<div style="font-weight: 600; margin-bottom: 8px;">Connected Devices (${status.device_count}):</div>
						${status.devices.map(device => `
							<div class="device-item ${device.is_current ? 'current' : ''}">
								<span class="device-name">${device.name}${device.is_current ? ' (This device)' : ''}</span>
								<span class="device-time">${new Date(device.last_sync).toLocaleDateString()}</span>
							</div>
						`).join('')}
					</div>
					<div style="display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap;">
						<button onclick="leaveSyncGroup()" style="background: rgba(244, 67, 54, 0.1); color: #f44336; border: 1px solid rgba(244, 67, 54, 0.3); padding: 8px 16px; border-radius: 6px; cursor: pointer;">Leave Sync Group</button>
						<button onclick="resetAllData()" style="background: rgba(156, 39, 176, 0.1); color: #9c27b0; border: 1px solid rgba(156, 39, 176, 0.3); padding: 8px 16px; border-radius: 6px; cursor: pointer;">Reset All Data</button>
					</div>
				`;
			} else {
				syncStatusDisplay.innerHTML = `
					<p style="color: var(--muted); margin: 16px 0;">
						This device is not synced with any other devices. Create a sync code to share with your other devices, or enter a code from another device to join an existing sync group.
					</p>
					<div style="margin-top: 16px;">
						<button onclick="resetAllData()" style="background: rgba(156, 39, 176, 0.1); color: #9c27b0; border: 1px solid rgba(156, 39, 176, 0.3); padding: 8px 16px; border-radius: 6px; cursor: pointer;">Reset All Data</button>
					</div>
				`;
			}
		} catch (error) {
			syncStatusDisplay.innerHTML = '<p style="color: #f44336;">Failed to load sync status</p>';
		}
	}

	async function createSyncGroup() {
		showSyncResult('Creating sync code...', 'info');
		
		try {
			const response = await fetch('/api/sync/create', {
				method: 'POST',
				headers: {'Content-Type': 'application/json'},
				body: JSON.stringify({description: 'Device Sync'})
			});
			
			const result = await response.json();
			
			if (result.success) {
				showSyncResult(`✅ Sync code created: ${result.sync_code}`, 'success');
				await updateSyncStatusDisplay();
				await updateSyncStatus();
			} else {
				showSyncResult('❌ Failed to create sync code', 'error');
			}
		} catch (error) {
			showSyncResult('❌ Network error creating sync code', 'error');
		}
	}

	async function joinSyncGroup() {
		const code = syncCodeInput.value.trim().toUpperCase();
		
		if (!code || code.length !== 6) {
			showSyncResult('❌ Please enter a valid 6-character code', 'error');
			return;
		}
		
		showSyncResult('Joining sync group...', 'info');
		
		try {
			const response = await fetch('/api/sync/join', {
				method: 'POST',
				headers: {'Content-Type': 'application/json'},
				body: JSON.stringify({sync_code: code})
			});
			
			const result = await response.json();
			
			if (result.success) {
				showSyncResult(`✅ ${result.message}`, 'success');
				syncCodeInput.value = '';
				await updateSyncStatusDisplay();
				await updateSyncStatus();
				
				// Reload preferences to get synced data
				setTimeout(() => {
					window.location.reload();
				}, 2000);
			} else {
				showSyncResult(`❌ ${result.message}`, 'error');
			}
		} catch (error) {
			showSyncResult('❌ Network error joining sync group', 'error');
		}
	}

	async function leaveSyncGroup() {
		if (!confirm('Are you sure you want to leave this sync group? Your data will remain on this device but won\'t sync with other devices anymore.')) {
			return;
		}
		
		try {
			const response = await fetch('/api/sync/leave', {method: 'DELETE'});
			const result = await response.json();
			
			if (result.success) {
				showSyncResult('✅ Left sync group successfully', 'success');
				await updateSyncStatusDisplay();
				await updateSyncStatus();
			} else {
				showSyncResult('❌ Failed to leave sync group', 'error');
			}
		} catch (error) {
			showSyncResult('❌ Network error leaving sync group', 'error');
		}
	}
	
	async function resetAllData() {
		if (!confirm('⚠️ Are you sure you want to reset ALL data?\n\nThis will permanently clear:\n• All ratings and reviews\n• All played/watched status\n• All video progress\n• Sync group membership\n\nThis action cannot be undone!')) {
			return;
		}
		
		try {
			showSyncResult('Resetting all data...', 'info');
			
			// Clear all localStorage data
			const keys = [];
			for (let i = 0; i < localStorage.length; i++) {
				keys.push(localStorage.key(i));
			}
			
			// Remove all video site related data
			keys.forEach(key => {
				if (key.startsWith('progress:') || 
					key.startsWith('played:') || 
					key.startsWith('rating:') || 
					key.startsWith('videoRating:')) {
					localStorage.removeItem(key);
				}
			});
			
			// Reset server-side data if available
			try {
				const response = await fetch('/api/reset', { method: 'POST' });
				if (response.ok) {
					showSyncResult('✅ All data reset successfully', 'success');
				} else {
					showSyncResult('✅ Local data reset (server sync unavailable)', 'success');
				}
			} catch (error) {
				showSyncResult('✅ Local data reset (server sync unavailable)', 'success');
			}
			
			// Reload to refresh the interface
			setTimeout(() => {
				window.location.reload();
			}, 2000);
			
		} catch (error) {
			showSyncResult('❌ Failed to reset data', 'error');
		}
	}
	
	// Make functions available globally for the onclick handlers
	window.leaveSyncGroup = leaveSyncGroup;
	window.resetAllData = resetAllData;

	function showSyncResult(message, type) {
		syncResult.textContent = message;
		syncResult.className = `sync-result ${type}`;
		syncResult.classList.remove('hidden');
		
		// Hide after 5 seconds for success messages
		if (type === 'success') {
			setTimeout(() => {
				syncResult.classList.add('hidden');
			}, 5000);
		}
	}

	function getResourceIcon(fileType) {
		const icons = {
			'.html': '🌐',
			'.htm': '🌐',
			'.pdf': '📄',
			'.txt': '📝',
			'.md': '📝',
			'.doc': '📄',
			'.docx': '📄'
		};
		return icons[fileType] || '📎';
	}

	function renderSidebar(courseGroups) {
		console.log('renderSidebar called with courseGroups:', courseGroups);
		console.log('courseList element:', courseList);
		
		if (!courseList) {
			console.error('courseList element not found!');
			return;
		}
		
		// Clear the test content and add actual course list
		courseList.innerHTML = '';
		
		// Check if we have any courses
		if (!courseGroups || Object.keys(courseGroups).length === 0) {
			courseList.innerHTML = '<div style="padding: 10px; color: white;">No courses found</div>';
			return;
		}
		
		Object.keys(courseGroups).sort().forEach(courseName => {
			// Calculate progress for this course
			const totalVideos = Object.values(courseGroups[courseName])
				.reduce((sum, section) => sum + section.videos.length, 0);
			const playedVideos = Object.values(courseGroups[courseName])
				.reduce((sum, section) => sum + section.videos.filter(video => isPlayed(video)).length, 0);
			
			const courseItem = document.createElement('a');
			courseItem.className = 'course-nav-item';
			courseItem.href = '#';
			courseItem.dataset.courseName = courseName;
			
			const progressPercent = totalVideos > 0 ? (playedVideos / totalVideos) * 100 : 0;
			
			courseItem.innerHTML = `
				<div class="course-nav-title">${courseName}</div>
				<div class="course-nav-stats">
					<span>${playedVideos}/${totalVideos} videos</span>
					<span>${Math.round(progressPercent)}%</span>
				</div>
				<div class="course-nav-rating" data-course-name="${courseName}">
					${Array.from({length: 5}, (_, i) => 
						`<span class="star ${i < getRating(courseName) ? 'filled' : ''}" data-rating="${i + 1}">🔥</span>`
					).join('')}
				</div>
				<div class="course-nav-progress">
					<div class="course-nav-progress-fill" style="width: ${progressPercent}%"></div>
				</div>
			`;
			
			courseItem.addEventListener('click', (e) => {
				e.preventDefault();
				scrollToCourseEnhanced(courseName);
			});
			
			// Add star rating event listeners
			courseItem.querySelectorAll('.star').forEach(star => {
				star.addEventListener('click', async (e) => {
					e.stopPropagation();
					const rating = parseInt(star.dataset.rating);
					const currentRating = getRating(courseName);
					
					// If clicking the same rating as current, clear it
					if (rating === currentRating) {
						await setRating(courseName, 0);
					} else {
						await setRating(courseName, rating);
					}
					render(); // Refresh to update all ratings
				});
			});
			
			courseList.appendChild(courseItem);
		});
		
		// Update sidebar selection after rendering
		updateSidebarSelection();
	}

	function scrollToCourse(courseName) {
		const courseElement = document.querySelector(`[data-course-name="${courseName}"]`);
		if (courseElement) {
			// Scroll to the course in the main content area
			courseElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
			
			// Highlight the course briefly
			courseElement.style.background = 'rgba(100, 181, 246, 0.3)';
			setTimeout(() => {
				courseElement.style.background = '';
			}, 2000);
			
			// Expand the course if it's collapsed
			const courseHeader = courseElement.querySelector('.course-header');
			const courseContent = courseElement.querySelector('.course-content');
			if (courseHeader && courseContent) {
				courseHeader.classList.remove('collapsed');
				courseContent.classList.remove('collapsed');
			}
		}
	}

	// Filter courses to show only selected course
	function filterCourseData(courseName) {
		if (!courseName || !libraryData) return libraryData;
		return libraryData.filter(item => {
			const pathParts = (item.dir_path || '').split('/');
			const itemCourseName = pathParts[0] || 'Other';
			return itemCourseName === courseName;
		});
	}
	
	// Show only one course
	function showOnlyCourse(courseName) {
		selectedCourse = courseName;
		filtered = filterCourseData(courseName);
		render();
		updateSidebarSelection();
	}
	
	// Show all courses (reset filter)
	function showAllCourses() {
		selectedCourse = null;
		filtered = libraryData;
		render();
		updateSidebarSelection();
	}
	
	// Update sidebar to show which course is selected
	function updateSidebarSelection() {
		// Remove active class from all course nav items
		document.querySelectorAll('.course-nav-item').forEach(item => {
			item.classList.remove('active');
		});
		
		// Add active class to selected course
		if (selectedCourse) {
			const activeItem = document.querySelector(`[data-course-name="${selectedCourse}"]`);
			if (activeItem) {
				activeItem.classList.add('active');
			}
		}
	}

	function render(){
		library.innerHTML = '';
		
		// Group videos by course and then by section
		const courseGroups = {};
		filtered.forEach(item => {
			const pathParts = (item.dir_path || '').split('/');
			const courseName = pathParts[0] || 'Other';
			const sectionName = pathParts[pathParts.length - 1] || 'Root';
			const sectionPath = item.dir_path || 'Root';
			
			if (!courseGroups[courseName]) {
				courseGroups[courseName] = {};
			}
			if (!courseGroups[courseName][sectionPath]) {
				courseGroups[courseName][sectionPath] = {
					sectionName: sectionName,
					videos: []
				};
			}
			courseGroups[courseName][sectionPath].videos.push(item);
		});

		// Render sidebar first
		console.log('About to render sidebar with courseGroups:', courseGroups);
		renderSidebar(courseGroups);
		
		// Fallback: If sidebar is still empty after a delay, add some content
		setTimeout(() => {
			if (courseList && courseList.innerHTML.trim() === '') {
				console.log('Sidebar is empty, adding fallback content');
				courseList.innerHTML = '<div style="padding: 10px; color: white;">Loading courses...</div>';
			}
		}, 1000);

		// Create course sections
		Object.keys(courseGroups).sort().forEach(courseName => {
			const courseSection = document.createElement('div');
			courseSection.className = 'course-section';
			courseSection.dataset.courseName = courseName;
			
			// Calculate total videos and played videos for this course
			const totalVideos = Object.values(courseGroups[courseName])
				.reduce((sum, section) => sum + section.videos.length, 0);
			const playedVideos = Object.values(courseGroups[courseName])
				.reduce((sum, section) => sum + section.videos.filter(video => isPlayed(video)).length, 0);
			
			// Create course header
			const courseHeader = document.createElement('div');
			courseHeader.className = `course-header collapsed ${playedVideos === totalVideos ? 'completed' : playedVideos > 0 ? 'in-progress' : ''}`;
			courseHeader.innerHTML = `
				<div class="course-header-main">
					<div class="course-title">${courseName}</div>
					<div class="course-stats">
						<span class="progress-indicator">${playedVideos}/${totalVideos} videos</span>
						<div class="course-rating" data-course-name="${courseName}">
							${Array.from({length: 5}, (_, i) => 
								`<span class="star ${i < getRating(courseName) ? 'filled' : ''}" data-rating="${i + 1}">🔥</span>`
							).join('')}
						</div>
						<span class="progress-bar">
							<span class="progress-fill" style="width: ${totalVideos > 0 ? (playedVideos / totalVideos) * 100 : 0}%"></span>
						</span>
					</div>
				</div>
				<div class="course-header-info">
					<span class="course-toggle">▼</span>
				</div>
			`;
			
			// Create course content
			const courseContent = document.createElement('div');
			courseContent.className = 'course-content collapsed';
			
			// Add section headers and videos
			Object.keys(courseGroups[courseName]).sort().forEach(sectionPath => {
				const sectionData = courseGroups[courseName][sectionPath];
				
				const sectionDiv = document.createElement('div');
				sectionDiv.className = 'section-item';
				
				// Calculate played videos for this section
				const sectionPlayedVideos = sectionData.videos.filter(video => isPlayed(video)).length;
				
				// Collect all resources from videos in this section
				const allResources = [];
				sectionData.videos.forEach(video => {
					if (video.resources && video.resources.length > 0) {
						allResources.push(...video.resources);
					}
				});
				
				// Remove duplicates based on path
				const uniqueResources = allResources.filter((resource, index, self) => 
					index === self.findIndex(r => r.path === resource.path)
				);
				
				const sectionHeader = document.createElement('div');
				sectionHeader.className = `section-header collapsed ${sectionPlayedVideos === sectionData.videos.length ? 'completed' : sectionPlayedVideos > 0 ? 'in-progress' : ''}`;
				sectionHeader.innerHTML = `
					<div class="section-header-main">
						<div class="section-title">${sectionData.sectionName}</div>
						<div class="section-stats">
							<span class="progress-indicator">${sectionPlayedVideos}/${sectionData.videos.length} videos</span>
							<span class="progress-bar">
								<span class="progress-fill" style="width: ${sectionData.videos.length > 0 ? (sectionPlayedVideos / sectionData.videos.length) * 100 : 0}%"></span>
							</span>
							${uniqueResources.length > 0 ? `
								<div class="section-resources">
									<span class="resources-label">Resources:</span>
									<div class="resource-links">
										${uniqueResources.map(resource => `
											<a href="/resources/${encodeURIComponent(resource.path)}" target="_blank" class="resource-link" data-type="${resource.type}">
												<span class="resource-icon">${getResourceIcon(resource.type)}</span>
												<span class="resource-name">${resource.name}</span>
											</a>
										`).join('')}
									</div>
								</div>
							` : ''}
						</div>
					</div>
					<div class="section-header-info">
						<span class="section-toggle">▼</span>
					</div>
				`;
				
				const sectionContent = document.createElement('div');
				sectionContent.className = 'section-content collapsed';
				
				// Add videos grid
				const videoGrid = document.createElement('div');
				videoGrid.className = 'video-grid';
				
				// Sort videos numerically by leading number
				sectionData.videos.sort((a, b) => {
					const getLeadingNumber = (title) => {
						const match = title.match(/^(\d+)/);
						return match ? parseInt(match[1], 10) : 0;
					};
					return getLeadingNumber(a.title) - getLeadingNumber(b.title);
				});
				
				sectionData.videos.forEach(item => {
					const card = document.createElement('div');
					card.className = `card ${isPlayed(item) ? 'played' : ''}`;
					
					// Create card content wrapper
					const cardContent = document.createElement('div');
					cardContent.className = 'card-content';
					
					const h3 = document.createElement('h3');
					h3.textContent = item.title;
					
					// Create card actions wrapper (stars + button)
					const cardActions = document.createElement('div');
					cardActions.className = 'card-actions';
					
					// Create compact video rating
					const videoRating = document.createElement('div');
					videoRating.className = 'video-rating';
					videoRating.dataset.videoPath = item.path;
					videoRating.innerHTML = Array.from({length: 5}, (_, i) => 
						`<span class="star ${i < getVideoRating(item.path) ? 'filled' : ''}" data-rating="${i + 1}">🔥</span>`
					).join('');
					
					// Add star rating event listeners
					videoRating.querySelectorAll('.star').forEach(star => {
						star.addEventListener('click', async (e) => {
							e.stopPropagation();
							const rating = parseInt(star.dataset.rating);
							const currentRating = getVideoRating(item.path);
							
							// If clicking the same rating as current, clear it
							if (rating === currentRating) {
								await setVideoRating(item.path, 0);
							} else {
								await setVideoRating(item.path, rating);
							}
							render(); // Refresh to update all ratings
						});
					});
					
					const btn = document.createElement('button');
					btn.textContent = isPlayed(item) ? '✓ Played' : '▶ Play';
					btn.className = isPlayed(item) ? 'played-btn' : '';
					btn.addEventListener('click', () => openPlayer(item));
					
					// Assemble the card
					cardContent.appendChild(h3);
					cardActions.appendChild(btn);
					cardActions.appendChild(videoRating);
					card.appendChild(cardContent);
					card.appendChild(cardActions);
					videoGrid.appendChild(card);
				});
				
				sectionContent.appendChild(videoGrid);
				
				// Section toggle functionality
				sectionHeader.addEventListener('click', () => {
					sectionHeader.classList.toggle('collapsed');
					sectionContent.classList.toggle('collapsed');
					
				});
				
				sectionDiv.appendChild(sectionHeader);
				sectionDiv.appendChild(sectionContent);
				courseContent.appendChild(sectionDiv);
			});
			
			// Course toggle functionality
			courseHeader.addEventListener('click', (e) => {
				// Don't toggle if clicking on stars
				if (e.target.classList.contains('star')) {
					return;
				}
				courseHeader.classList.toggle('collapsed');
				courseContent.classList.toggle('collapsed');
				
			});
			
			// Add star rating event listeners for main content
			courseHeader.querySelectorAll('.star').forEach(star => {
				star.addEventListener('click', async (e) => {
					e.stopPropagation();
					const rating = parseInt(star.dataset.rating);
					const currentRating = getRating(courseName);
					
					// If clicking the same rating as current, clear it
					if (rating === currentRating) {
						await setRating(courseName, 0);
					} else {
						await setRating(courseName, rating);
					}
					render(); // Refresh to update all ratings
				});
			});
			
			courseSection.appendChild(courseHeader);
			courseSection.appendChild(courseContent);
			library.appendChild(courseSection);
		});
	}


	async function fetchLibrary(){
		const res = await fetch('/api/library');
		const data = await res.json();
		libraryData = data.items || [];
		filtered = libraryData;
		render();
		
		// Re-render sidebar after library data is loaded to ensure proper course groups
		setTimeout(() => {
			const courseGroups = {};
			libraryData.forEach(item => {
				const pathParts = (item.dir_path || '').split('/');
				const courseName = pathParts[0] || 'Other';
				if (!courseGroups[courseName]) {
					courseGroups[courseName] = {};
				}
			});
			renderSidebar(courseGroups);
			updateSidebarSelection(); // Make sure sidebar selection state is correct
		}, 100);
	}

	function openPlayer(item){
		player.pause();
		player.innerHTML = '';
		player.src = `/video/${encodeURIComponent(item.path)}`;
		playerTitle.textContent = `${item.class} — ${item.title}`;
		currentModalPath = item.path;
		activeSummary = { path: null, taskId: null };
		// subtitles
		(item.subtitles || []).forEach(sub => {
			const track = document.createElement('track');
			track.kind = 'subtitles';
			track.label = sub.endsWith('.vtt') ? 'Subtitles' : 'Subtitles';
			track.srclang = 'en';
			track.src = `/subs/${encodeURIComponent(sub)}`;
			player.appendChild(track);
		});
		const resumeAt = loadProgress(item);
		modal.classList.remove('hidden');
		
		// Reset summary UI
		summarySection.classList.add('hidden');
		summaryStatus.textContent = '';
		summaryContent.innerHTML = '';
		if (summaryVersionSelect) { summaryVersionSelect.style.display = 'none'; summaryVersionSelect.innerHTML = ''; }
		transcriptJPFallback = '';

		// Wire modal play button
		if (modalPlayBtn) {
			modalPlayBtn.textContent = '▶ Play';
			modalPlayBtn.classList.remove('pause');
			modalPlayBtn.onclick = () => {
				if (player.paused) { player.play().catch(()=>{}); }
				else { player.pause(); }
			};
			player.addEventListener('play', () => { modalPlayBtn.textContent = '⏸ Pause'; modalPlayBtn.classList.add('pause'); });
			player.addEventListener('pause', () => { modalPlayBtn.textContent = '▶ Play'; modalPlayBtn.classList.remove('pause'); });
		}

		// Set modal rating for this video
		if (modalVideoRating) {
			modalVideoRating.dataset.videoPath = item.path;
			modalVideoRating.innerHTML = Array.from({length: 5}, (_, i) => 
				`<span class="star ${i < getVideoRating(item.path) ? 'filled' : ''}" data-rating="${i + 1}">🔥</span>`
			).join('');
			modalVideoRating.querySelectorAll('.star').forEach(star => {
				star.addEventListener('click', async (e) => {
					const rating = parseInt(star.dataset.rating);
					const currentRating = getVideoRating(item.path);
					if (rating === currentRating) { await setVideoRating(item.path, 0); }
					else { await setVideoRating(item.path, rating); }
					modalVideoRating.innerHTML = Array.from({length: 5}, (_, i) => 
						`<span class="star ${i < getVideoRating(item.path) ? 'filled' : ''}" data-rating="${i + 1}">🔥</span>`
					).join('');
				});
			});
		}

		// Populate model select
		setupModelSelect();

		// Wire summarize button
		if (summarizeBtn) {
			summarizeBtn.classList.remove('processing');
			summarizeBtn.textContent = '✨ Generate Summary';
			summarizeBtn.onclick = () => startSummaryFlow(item);
		}

		// Auto-load existing summary if present
		(async () => {
			try {
				// Populate versions immediately if any exist, regardless of summary status
				try {
					const vs0 = await fetch(`/api/summary/versions?video_path=${encodeURIComponent(item.path)}`);
					if (vs0.ok) {
						const v0 = await vs0.json();
					if (v0.found && Array.isArray(v0.versions) && v0.versions.length) {
						populateVersionSelector(item.path, v0.versions, true);
						}
					}
				} catch(_) {}
				// If an active task exists for this video, resume polling immediately
				const active = await fetch(`/api/summary/active?video_path=${encodeURIComponent(item.path)}`);
				if (active.ok) {
					const a = await active.json();
					if (a.active && a.task_id) {
						summarySection.classList.remove('hidden');
						summarizeBtn.classList.add('processing');
						summarizeBtn.textContent = '⏳ Summarizing...';
						summaryStatus.textContent = 'Resuming...';
						activeSummary = { path: item.path, taskId: a.task_id };
						pollSummaryStatus(a.task_id, item.path);
					}
				}
				const existing = await fetch(`/api/summary/get?video_path=${encodeURIComponent(item.path)}`);
                if (existing.ok) {
                    const data = await existing.json();
                    if (data.found && data.status === 'completed' && data.summary) {
                        summarySection.classList.remove('hidden');
						if (data.transcript && data.transcript.includes('[JUMP_POINTS]')) {
							transcriptJPFallback = data.transcript;
						}
						renderSummary(data.summary, data.transcript || transcriptJPFallback || '');
                        summaryStatus.textContent = 'Summary ready';
						if (summarizeBtn) summarizeBtn.textContent = '🔄 Re-summarize';
						// If backend included versions, populate (may already be populated, idempotent)
						if (Array.isArray(data.versions) && data.versions.length) {
							populateVersionSelector(item.path, data.versions);
						}
					}
				}
			} catch (_) {}
		})();

		player.addEventListener('loadedmetadata', function onMeta(){
			player.removeEventListener('loadedmetadata', onMeta);
			if (resumeAt > 0 && resumeAt < (player.duration || Infinity)) {
				player.currentTime = resumeAt;
			}
			// Do not autoplay
		});

		// save progress periodically
		const onTime = async () => {
			await saveProgress(item);
			// Mark as played when 90% of video is watched
			if (player.duration && player.currentTime / player.duration >= 0.9) {
				await markAsPlayed(item);
			}
		};
		player.addEventListener('timeupdate', onTime);
		const onEnded = async () => {
			await saveProgress(item);
			await markAsPlayed(item);
			// Re-render to update visual indicators
			render();
		};
		player.addEventListener('ended', onEnded);

		// cleanup when closing
		const cleanup = () => {
			player.removeEventListener('timeupdate', onTime);
			player.removeEventListener('ended', onEnded);
			player.pause();
			player.src = '';
			currentModalPath = null;
			activeSummary = { path: null, taskId: null };
			if (summarizeBtn) {
				summarizeBtn.classList.remove('processing');
				summarizeBtn.textContent = '✨ Generate Summary';
			}
		};
		closeModal.onclick = () => { cleanup(); modal.classList.add('hidden'); };
		modal.onclick = (e) => { if (e.target === modal) { cleanup(); modal.classList.add('hidden'); } };
	}

	async function startSummaryFlow(item){
		try {
			summarySection.classList.remove('hidden');
			summaryStatus.textContent = 'Checking for existing summary...';
			summaryContent.innerHTML = '';

			// Try to load existing
			const existing = await fetch(`/api/summary/get?video_path=${encodeURIComponent(item.path)}`);
			if (existing.ok) {
				const data = await existing.json();
				if (data.found && data.status === 'completed' && data.summary) {
					renderSummary(data.summary);
					summaryStatus.textContent = 'Summary loaded';
					summarizeBtn.textContent = '🔄 Regenerate Summary';
				}
			}

			// Start new summary
			summarizeBtn.classList.add('processing');
			summarizeBtn.textContent = '⏳ Summarizing 0%';
			summaryStatus.textContent = 'Starting...';
			const res = await fetch('/api/summary/start', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ video_path: item.path, force: true, model_name: getSelectedModel() })
			});
			if (!res.ok) {
				const err = await res.text();
				throw new Error(err || 'Failed to start summary');
			}
			const { task_id } = await res.json();
			activeSummary = { path: item.path, taskId: task_id };
			summaryStatus.textContent = 'Queued...';
			await pollSummaryStatus(task_id, item.path);
		} catch (e) {
			summaryStatus.textContent = 'Error: ' + (e.message || 'Failed');
			summarizeBtn.classList.remove('processing');
			summarizeBtn.textContent = '✨ AI Summary';
		}
	}

	async function pollSummaryStatus(taskId, itemPath){
		let done = false;
		while (!done) {
			await new Promise(r => setTimeout(r, 1500));
			// Stop if modal closed or another summary superseded this one
			if (modal.classList.contains('hidden')) break;
			if (activeSummary.taskId !== taskId || activeSummary.path !== itemPath) break;
			const r = await fetch(`/api/summary/status/${encodeURIComponent(taskId)}`);
			if (!r.ok) break;
			const s = await r.json();
			summaryStatus.textContent = `${s.progress || s.status} ${s.progress_percent ? '('+s.progress_percent+'%)' : ''}`;
			if (typeof s.progress_percent === 'number') {
				summarizeBtn.textContent = `⏳ Summarizing ${s.progress_percent}%`;
			}
			if (s.status === 'completed') {
				done = true;
				// Fetch the completed summary (with transcript) to render jump points reliably
				try {
					const gr = await fetch(`/api/summary/get?video_path=${encodeURIComponent(itemPath)}`);
					if (gr.ok) {
						const gd = await gr.json();
						if (gd.found && gd.summary) {
							if (gd.transcript && gd.transcript.includes('[JUMP_POINTS]')) {
								transcriptJPFallback = gd.transcript;
							}
							renderSummary(gd.summary, gd.transcript || transcriptJPFallback || '');
						}
					}
					// refresh versions list after new completion
					try {
						const vs = await fetch(`/api/summary/versions?video_path=${encodeURIComponent(itemPath)}`);
						if (vs.ok) {
							const data = await vs.json();
							if (data.found) populateVersionSelector(itemPath, data.versions);
						}
					} catch(_) {}
				} catch(_) {}
				summarizeBtn.classList.remove('processing');
				summarizeBtn.textContent = '🔄 Re-summarize';
				activeSummary = { path: itemPath, taskId: null };
			}
			if (s.status === 'failed') {
				done = true;
				summaryStatus.textContent = 'Failed: ' + (s.error || 'Unknown error');
				summarizeBtn.classList.remove('processing');
				summarizeBtn.textContent = '✨ AI Summary';
				activeSummary = { path: itemPath, taskId: null };
			}
		}
	}

function renderSummary(raw, transcript){
    // Parse optional jump points from transcript
    const jp = transcript ? parseJumpPointsFromTranscript(transcript) : [];
    const html = formatSummaryContent(raw, jp);
    summaryContent.innerHTML = html;
    attachJumpDelegation();
}

// Extract jump points appended as a JSON block after a [JUMP_POINTS] marker
function parseJumpPointsFromTranscript(transcript){
    try {
        if (!transcript || typeof transcript !== 'string') return [];
        const marker = transcript.indexOf('[JUMP_POINTS]');
        if (marker === -1) return [];
        // Take substring after marker and trim leading whitespace
        let tail = transcript.slice(marker + '[JUMP_POINTS]'.length).trim();
        // Heuristic: JSON array should start at first '[' and end at last ']'
        const startIdx = tail.indexOf('[');
        const endIdx = tail.lastIndexOf(']');
        if (startIdx === -1 || endIdx === -1 || endIdx <= startIdx) return [];
        const jsonStr = tail.slice(startIdx, endIdx + 1);
        let arr = [];
        try { arr = JSON.parse(jsonStr); } catch { return [];
        }
        if (!Array.isArray(arr)) return [];
        // Normalize to expected fields
        const norm = [];
        for (const item of arr) {
            if (!item) continue;
            const seconds = Number(item.seconds ?? item.t ?? item.time ?? NaN);
            const title = String(item.title ?? item.label ?? '').trim();
            if (!Number.isFinite(seconds)) continue;
            const mm = Math.floor(seconds / 60);
            const ss = Math.floor(seconds % 60);
            const ts = `${mm}:${String(ss).padStart(2,'0')}`;
            norm.push({ seconds, ts, title });
        }
        return norm;
    } catch { return []; }
}

function formatSummaryContent(raw, extraChapters){
		const normalized = normalizeSummaryText(raw);
		// Split lines and merge orphan numeric step lines like "1" followed by content
		const rawLines = normalized.split('\n').map(l => l.trim()).filter(Boolean);
		const lines = [];
		for (let i = 0; i < rawLines.length; i++) {
			const ln = rawLines[i];
			if (/^\d+$/.test(ln) && i + 1 < rawLines.length) {
				lines.push(`${ln}) ${rawLines[i+1]}`);
				i++; // skip the next line (already merged)
			} else {
				lines.push(ln);
			}
		}
		let html = '';
		let inKeys = false, inDetails = false;
		const keyPoints = [];
		const detailSections = [];
		let currentSection = null;
    const chapters = [];
		const seenChapterSeconds = new Set();

		const canonize = (s) => s.replace(/\*/g, '').replace(/\s*:+\s*$/, '').trim().toUpperCase();
		const isMainKeyHeader = (s) => canonize(s) === 'KEY POINTS';
		const isMainDetailHeader = (s) => canonize(s) === 'DETAILED SUMMARY';
		const knownHeadsRe = /^(key concepts|tools|prerequisites|practical applications|real[- ]world use cases|step[- ]by[- ]step|introduction|overview|key features|features)$/i;
		const isSubHeader = (s) => {
			const plain = s.replace(/^\*+|\*+$/g, '').trim();
			const endsColon = /:$/.test(plain);
			const words = plain.replace(/:$/, '').trim();
			if (endsColon) return words.length > 0 && words.length <= 200;
			return knownHeadsRe.test(words);
		};

		for (let rawLine of lines) {
			let line = rawLine.replace(/^(?:[•\-–—]|➜)\s*/, '').replace(/^["“”]+/, '').trim();
			if (!line) continue;
			// Detect chapter lines like: 01:23 - Title or [1:02:03] Title
			const chap = line.match(/^\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*[-–—:]?\s*(.+)$/);
			if (chap) {
				const seconds = timestampToSeconds(chap[1]);
				if (!isNaN(seconds) && !seenChapterSeconds.has(seconds)) {
					chapters.push({ ts: chap[1], seconds, title: chap[2] });
					seenChapterSeconds.add(seconds);
					continue;
				}
			}
			// Also collect inline timestamps anywhere in the line (multiple per line)
			let m;
			const re = /\b(\d{1,2}:\d{2}(?::\d{2})?)\b/g;
			while ((m = re.exec(line))) {
				const ts = m[1];
				const seconds = timestampToSeconds(ts);
				if (!isNaN(seconds) && !seenChapterSeconds.has(seconds)) {
					const after = line.slice(m.index + m[0].length).replace(/^\s*[-–—:]?\s*/, '').trim();
					const before = line.slice(0, m.index).trim();
					const title = (after || before || 'Jump').trim();
					chapters.push({ ts, seconds, title });
					seenChapterSeconds.add(seconds);
				}
			}
			// Flexible formats like 1m23s, 1m 23s, 90s, 4m
			let m2;
			const reMs = /\b(?:(\d+)m\s*(\d+)s|(?:(\d+)m)|(\d+)s)\b/gi;
			while ((m2 = reMs.exec(line))) {
				const secs = parseFlexibleTimestamp(m2);
				if (!isNaN(secs) && !seenChapterSeconds.has(secs)) {
					const after = line.slice(m2.index + m2[0].length).replace(/^\s*[-–—:]?\s*/, '').trim();
					const before = line.slice(0, m2.index).trim();
					const label = m2[0].replace(/\s+/g,'');
					const title = (after || before || 'Jump').trim();
					chapters.push({ ts: label, seconds: secs, title });
					seenChapterSeconds.add(secs);
				}
			}
			if (isMainKeyHeader(line)) { inKeys = true; inDetails = false; continue; }
			if (isMainDetailHeader(line)) { inKeys = false; inDetails = true; if (!currentSection) currentSection = { title: 'Overview', points: [], steps: [] }; continue; }
			// Normalize known headers without colon
			if (!/:$/.test(line) && isSubHeader(line) && !knownHeadsRe.test('')) {
				line = line + ':';
			}
			// Handle header + inline content on same line, including stray ** around colon
			let split = line.match(/^\*{0,2}([^*].*?)\*{0,2}:\*{0,2}\s+(.+)$/);
			if (!split) {
				const h2 = line.match(/^(.+?):\s+(.+)$/);
				if (h2 && isSubHeader(h2[1] + ':')) {
					split = ['', h2[1], h2[2]];
				}
			}
			if (split) {
				if (!inDetails) inDetails = true;
				if (currentSection && (currentSection.points.length || currentSection.steps.length)) detailSections.push(currentSection);
				const title = split[1].replace(/^\*+|\*+$/g, '').trim();
				currentSection = { title, points: [], steps: [] };
				const rest = split[2].trim();
				if (rest) currentSection.points.push(rest.replace(/\*\*:/g, ':').replace(/:\*\*/g, ':').replace(/\*\*$/,''));
				continue;
			}
			if (isSubHeader(line)) {
				if (!inDetails) { inDetails = true; }
				if (currentSection && (currentSection.points.length || currentSection.steps.length)) detailSections.push(currentSection);
				const title = line.replace(/^\*+|\*+$/g, '').replace(/:$/, '').replace(/:?\*+\s*$/,'').trim();
				currentSection = { title, points: [], steps: [] };
				continue;
			}
			if (inKeys) {
				if (line) keyPoints.push(line.replace(/\*\*:/g, ':').replace(/:\*\*/g, ':').replace(/\*\*$/,''));
				continue;
			}
			if (inDetails) {
				if (!currentSection) currentSection = { title: 'Overview', points: [], steps: [] };
				const m = line.match(/^(\d+)[\)\.]+\s*(.*)$/);
				if (m) currentSection.steps.push({ n: parseInt(m[1],10), text: m[2] || '' });
				else if (line) {
					const cleaned = line.replace(/\*\*:/g, ':').replace(/:\*\*/g, ':').replace(/\*\*$/,'');
					if (cleaned) currentSection.points.push(cleaned);
				}
			}
		}
		if (currentSection && (currentSection.points.length || currentSection.steps.length)) detailSections.push(currentSection);

		if (keyPoints.length) {
			html += '<div class="summary-section-title">✨ KEY POINTS</div>';
			html += '<ul class="key-points-list">' + keyPoints.map(p => `<li class="key-point">✨ ${renderInline(p)}</li>`).join('') + '</ul>';
		}
    // Merge chapters from transcript if provided
    if (Array.isArray(extraChapters)) {
        extraChapters.forEach(c => {
            if (!c) return;
            const seconds = Number(c.seconds ?? c.t ?? c.time ?? NaN);
            const ts = c.ts || (Number.isFinite(seconds) ? `${Math.floor(seconds/60)}:${String(Math.floor(seconds%60)).padStart(2,'0')}` : '');
            const title = c.title || c.label || '';
            if (Number.isFinite(seconds) && !seenChapterSeconds.has(seconds)) {
                chapters.push({ seconds, ts, title });
                seenChapterSeconds.add(seconds);
            }
        });
    }

		if (detailSections.length) {
			html += '<div class="summary-section-title">🧩 DETAILED SUMMARY</div>';
			detailSections.forEach(sec => {
				html += `<div class="subsection-title">${formatSubsectionTitle(sec.title)}</div>`;
				if (sec.points.length) {
					html += '<ul class="detailed-summary-list">' + sec.points.map(p => `<li class="detailed-point">🔹 ${renderInline(p)}</li>`).join('') + '</ul>';
				}
				if (sec.steps.length) {
					const sorted = sec.steps.sort((a,b)=>a.n-b.n);
					html += '<ol class="steps-list">' + sorted.map(s => `<li><span class="step-num">${s.n}</span><span>${renderInline(s.text)}</span></li>`).join('') + '</ol>';
				}
			});
		}
		if (!html) {
			const bullets = normalized.split(/(?:^|\n)\s*[•\-–—\*]\s+/).map(s => s.trim()).filter(Boolean);
			if (bullets.length > 1) {
				html = '<div class="summary-section-title">SUMMARY</div>' + '<ul class="detailed-summary-list">' + bullets.map(p => `<li class="detailed-point">${renderInline(p)}</li>`).join('') + '</ul>';
			} else {
				html = `<div class="summary-section-title">SUMMARY</div><div>${renderInline(raw)}</div>`;
			}
		}
		// Append Jump Points at the end (below the summary), if available
		if (chapters.length) {
			html += '<div class="summary-section-title">⏱️ Jump Points</div>';
			html += '<ul class="chapters-list">' + chapters.map(c => `<li class="chapter-item"><a href="#" class="jump-link" data-seconds="${c.seconds}">⏩ ${escapeHtml(c.ts)} — ${renderInline(c.title)}</a></li>`).join('') + '</ul>';
		}
		return html;
	}

	function normalizeSummaryText(raw){
		if (!raw) return '';
		let text = String(raw).replace(/\r/g, '');
		// Remove a leading SUMMARY label if present
		text = text.replace(/^\s*\**\s*SUMMARY\s*\**:?-?\s*/i, '');
		// Convert inline bullets to real line breaks first (handles headings prefixed by bullets)
		text = text.replace(/\s*[•\-–—]\s+/g, '\n• ');
		// Normalize section markers to their own lines (allow optional leading bullet)
		text = text.replace(/(?:^|\n)\s*(?:[•\-–—]\s*)?\*{0,2}\s*KEY\s+POINTS\s*\*{0,2}:?\s*(?:\*{0,2}\s*)?/gi, '\n**KEY POINTS:**\n');
		text = text.replace(/(?:^|\n)\s*(?:[•\-–—]\s*)?\*{0,2}\s*DETAILED\s+SUMMARY\s*\*{0,2}:?\s*(?:\*{0,2}\s*)?/gi, '\n**DETAILED SUMMARY:**\n');
		// Also fix inline occurrences mid-line
		text = text.replace(/\s+\*{0,2}\s*KEY\s+POINTS\s*\*{0,2}:?\s*(?:\*{0,2}\s*)?/gi, '\n**KEY POINTS:**\n');
		text = text.replace(/\s+\*{0,2}\s*DETAILED\s+SUMMARY\s*\*{0,2}:?\s*(?:\*{0,2}\s*)?/gi, '\n**DETAILED SUMMARY:**\n');
		// Common subheaders – put on their own lines
		const subs = [
			'KEY CONCEPTS, METHODOLOGIES, AND TECHNICAL DETAILS',
			'TOOLS, FRAMEWORKS, OR TECHNOLOGIES REFERENCED',
			'PREREQUISITES OR BACKGROUND KNOWLEDGE DISCUSSED',
			'PRACTICAL APPLICATIONS AND REAL-WORLD USE CASES',
			'STEP-BY-STEP PROCESSES OR WORKFLOWS MENTIONED',
			'INTRODUCTION', 'OVERVIEW', 'KEY FEATURES', 'FEATURES'
		];
		subs.forEach(s => {
			const re = new RegExp(`(?:^|\\n)\\s*(?:[•\\-–—]\\s*)?\\*{0,2}\\s*${s.replace(/[-/\\^$*+?.()|[\\]{}]/g, '\\$&')}\\s*\\*{0,2}:?\\s*(?:\\*{0,2}\\s*)?`, 'gi');
			text = text.replace(re, `\n*${s}:**\n`);
			// Also handle inline mid-line occurrences
			const mid = new RegExp(`\\s+\\*{0,2}\\s*${s.replace(/[-/\\^$*+?.()|[\\]{}]/g, '\\$&')}\\s*\\*{0,2}:?\\s*(?:\\*{0,2}\\s*)?`, 'gi');
			text = text.replace(mid, `\n*${s}:**\n`);
		});
		// Collapse multiple newlines
		text = text.replace(/\n{2,}/g, '\n');
		return text.trim();
	}

	function escapeHtml(str){
		return str.replace(/[&<>"]|'/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
	}

	function renderInline(text){
		// Escape HTML, then convert **bold** to <strong>
		const escaped = escapeHtml(text);
		const withBold = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
		// Linkify timestamps like 0:42, 01:23, 1:02:03
		let out = withBold.replace(/\b(\d{1,2}:\d{2}(?::\d{2})?)\b/g, (m, ts) => {
			const secs = timestampToSeconds(ts);
			if (isNaN(secs)) return m;
			return `<a href="#" class="jump-link" data-seconds="${secs}">⏩ ${ts}</a>`;
		});
		// Also linkify 1m23s, 1m 23s, 90s, 4m
		out = out.replace(/\b(?:(\d+)m\s*(\d+)s|(?:(\d+)m)|(\d+)s)\b/gi, (m, a, b, c, d) => {
			const secs = parseFlexibleTimestamp([m, a, b, c, d]);
			if (isNaN(secs)) return m;
			return `<a href="#" class="jump-link" data-seconds="${secs}">⏩ ${m.replace(/\s+/g,'')}</a>`;
		});
		return out;
	}

	function formatSubsectionTitle(title){
		const t = title.toUpperCase();
		if (t.startsWith('KEY CONCEPTS')) return `📚 ${escapeHtml(title)}`;
		if (t.startsWith('TOOLS')) return `🛠️ ${escapeHtml(title)}`;
		if (t.startsWith('PREREQUISITES')) return `🧠 ${escapeHtml(title)}`;
		if (t.startsWith('PRACTICAL APPLICATIONS')) return `🚀 ${escapeHtml(title)}`;
		if (t.startsWith('STEP-BY-STEP')) return `🧭 ${escapeHtml(title)}`;
		return `📌 ${escapeHtml(title)}`;
	}

	function timestampToSeconds(ts){
		const parts = ts.split(':').map(Number);
		if (parts.length === 2) return parts[0]*60 + parts[1];
		if (parts.length === 3) return parts[0]*3600 + parts[1]*60 + parts[2];
		return NaN;
	}

	function parseFlexibleTimestamp(match){
		// match can be RegExp match array or composed array [full,a,b,c,d]
		const a = match[1], b = match[2], c = match[3], d = match[4];
		if (a && b) return Number(a)*60 + Number(b);
		if (c) return Number(c)*60;
		if (d) return Number(d);
		return NaN;
	}

	function attachJumpDelegation(){
		if (!summaryContent || summaryContent._jumpHandlerAttached) return;
		summaryContent.addEventListener('click', (e) => {
			const a = e.target.closest && e.target.closest('.jump-link');
			if (!a) return;
			e.preventDefault();
			const seconds = Number(a.dataset.seconds || 'NaN');
			if (!Number.isNaN(seconds)) {
				try {
					player.currentTime = Math.max(0, Math.min(seconds, player.duration || seconds));
					player.play().catch(()=>{});
				} catch(_) {}
			}
		});
		summaryContent._jumpHandlerAttached = true;
	}

function populateVersionSelector(videoPath, versions, autoLoad){
		if (!summaryVersionSelect) return;
		const vs = Array.isArray(versions) ? versions.slice() : [];
		if (vs.length === 0) { summaryVersionSelect.style.display = 'none'; return; }
		summaryVersionSelect.innerHTML = '';
		vs.forEach(v => {
			const opt = document.createElement('option');
			opt.value = String(v.version);
			const when = v.generated_at ? formatDateOnly(v.generated_at) : '';
			const dur = typeof v.processing_time_seconds === 'number' ? ` • ${formatMinutes(v.processing_time_seconds)}` : '';
			// Short label: vN • model • mm/dd/yy • Xm
			let modelShort = '';
			try {
				const raw = (v.model_used || v.display_model || '').toString();
				const mm = raw.match(/[^+]+$/); // take text after last '+'
				modelShort = (mm ? mm[0] : raw).replace(/-instruct\b/i, '');
			} catch(_) { modelShort = ''; }
			opt.textContent = `v${v.version} • ${modelShort || 'model'}${when ? ` • ${when}` : ''}${dur}`.trim();
			// Mobile label (CSS hides full text and shows data-mobile)
			opt.setAttribute('data-mobile', `v${v.version}`);
			summaryVersionSelect.appendChild(opt);
		});
		summaryVersionSelect.style.display = '';
		// Load latest (first in list) by default
		summaryVersionSelect.selectedIndex = 0;
		if (!summaryVersionSelect._bound) {
			summaryVersionSelect.addEventListener('change', async () => {
				const ver = parseInt(summaryVersionSelect.value, 10);
				if (!Number.isFinite(ver)) return;
				try {
					summaryStatus.textContent = `Loading v${ver}...`;
					let r = await fetch(`/api/summary/version?video_path=${encodeURIComponent(videoPath)}&version=${ver}`);
					if (!r.ok) {
						// Fallback: try filename-only in case of path mismatch
						const base = (videoPath || '').split('/').pop();
						if (base) {
							r = await fetch(`/api/summary/version?video_path=${encodeURIComponent(base)}&version=${ver}`);
						}
					}
					if (r.ok) {
						const data = await r.json();
						summarySection.classList.remove('hidden');
						if (data.summary && data.summary.trim()) {
							const tx = (data.transcript && data.transcript.includes('[JUMP_POINTS]')) ? data.transcript : (transcriptJPFallback || '');
							renderSummary(data.summary, tx);
							summaryStatus.textContent = `Showing v${ver}`;
						} else {
							// Fallback to completed summary
							const g = await fetch(`/api/summary/get?video_path=${encodeURIComponent(videoPath)}`);
							if (g.ok) {
								const gd = await g.json();
								if (gd.found && gd.summary) {
									if (gd.transcript && gd.transcript.includes('[JUMP_POINTS]')) {
										transcriptJPFallback = gd.transcript;
									}
									renderSummary(gd.summary, gd.transcript || transcriptJPFallback || '');
									summaryStatus.textContent = `Showing v${ver}`;
									return;
								}
							}
							summaryStatus.textContent = `No content for v${ver}`;
						}
					} else {
						summaryStatus.textContent = `Failed to load v${ver}`;
					}
				} catch(_) {
					summaryStatus.textContent = `Failed to load v${ver}`;
				}
			});
			summaryVersionSelect._bound = true;
		}

		// Auto-load currently selected version if requested or if nothing is rendered yet
		if (autoLoad || !summaryContent || summaryContent.innerHTML.trim() === '') {
			const sel = parseInt(summaryVersionSelect.value, 10);
			if (Number.isFinite(sel)) {
				(void (async () => {
					try {
						summaryStatus.textContent = `Loading v${sel}...`;
					let r = await fetch(`/api/summary/version?video_path=${encodeURIComponent(videoPath)}&version=${sel}`);
						if (!r.ok) {
							const base = (videoPath || '').split('/').pop();
							if (base) {
								r = await fetch(`/api/summary/version?video_path=${encodeURIComponent(base)}&version=${sel}`);
							}
						}
						if (r.ok) {
							const data = await r.json();
							summarySection.classList.remove('hidden');
							if (data.summary && data.summary.trim()) {
								const tx = (data.transcript && data.transcript.includes('[JUMP_POINTS]')) ? data.transcript : (transcriptJPFallback || '');
								renderSummary(data.summary, tx);
								summaryStatus.textContent = `Showing v${sel}`;
							} else {
								const g = await fetch(`/api/summary/get?video_path=${encodeURIComponent(videoPath)}`);
								if (g.ok) {
									const gd = await g.json();
									if (gd.found && gd.summary) {
										if (gd.transcript && gd.transcript.includes('[JUMP_POINTS]')) {
											transcriptJPFallback = gd.transcript;
										}
										renderSummary(gd.summary, gd.transcript || transcriptJPFallback || '');
										summaryStatus.textContent = `Showing v${sel}`;
									}
								}
							}
						}
					} catch(_) {}
				})());
			}
		}
	}

	function formatMinutes(seconds){
		const m = (Number(seconds) || 0) / 60;
		const str = m.toFixed(1);
		return `${str}m`;
	}

	function compactModel(model){
		try{
			let m = model;
			const plus = m.lastIndexOf('+');
			if (plus !== -1) m = m.slice(plus + 1);
			m = m.replace(/-instruct\b/i, '');
			return m;
		}catch{ return model; }
	}

	function formatDateOnly(iso){
		try{
			const d = new Date(iso);
			return new Intl.DateTimeFormat('en-US', {
				month: '2-digit', day: '2-digit', year: '2-digit', timeZone: 'America/New_York'
			}).format(d);
		}catch{ return ''; }
	}

function setupModelSelect(preselectName){
		if (!modelSelect) return;
		modelSelect.style.display = 'none';
		modelSelect.innerHTML = '';
		fetch('/api/ai-health').then(r => r.json()).then(data => {
			const models = Array.isArray(data.models_available) ? data.models_available : [];
			const current = data.current_model || '';
			if (models.length === 0) return;
        const desired = preselectName || window.storageManager.getItem('preferredModel') || current;
			models.forEach(name => {
				const opt = document.createElement('option');
				opt.value = name;
				opt.textContent = name;
				if (name === desired) opt.selected = true;
				modelSelect.appendChild(opt);
			});
			// Add "Pull more" option group
			const smallGood = [
				'llama3.2:1b', 'llama3.2:3b', 'llama3.1:8b-instruct', 'qwen2.5:3b-instruct', 'phi3:mini', 'gemma2:2b',
				'mistral:7b-instruct', 'qwen2.5:7b-instruct', 'qwen2.5:14b-instruct', 'mistral-nemo:12b-instruct'
			];
			const group = document.createElement('optgroup');
			group.label = 'Try pulling:';
			smallGood.forEach(name => {
				if (models.includes(name)) return;
				const opt = document.createElement('option');
				opt.value = `__pull__:${name}`;
				opt.textContent = `Pull ${name}`;
				group.appendChild(opt);
			});
			if (group.children.length) modelSelect.appendChild(group);
			modelSelect.style.display = '';
			if (!modelSelect._bound) {
            modelSelect.addEventListener('change', async () => {
					const sel = modelSelect.value;
					if (sel && sel.startsWith('__pull__:')) {
						const name = sel.replace('__pull__:', '');
						summaryStatus.textContent = `Pulling ${name}...`;
                    try {
                        const pr = await fetch('/api/ai-model/pull', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) });
                        if (!pr.ok) {
                            const t = await pr.text();
                            summaryStatus.textContent = `Failed to pull ${name}: ${t}`;
                            return;
                        }
                        const resp = await pr.json();
                        summaryStatus.textContent = `${resp.cached ? 'Found cached' : 'Pulled'} ${name}. Refreshing models...`;
                        modelSelect._retryName = name;
                        modelSelect._retryCount = 0;
                        setupModelSelect(name);
                        window.storageManager.setItem('preferredModel', name);
                    } catch (e) {
                        summaryStatus.textContent = `Failed to pull ${name}`;
                    }
						return;
					}
					if (sel) window.storageManager.setItem('preferredModel', sel);
				});
				modelSelect._bound = true;
			}
			// If a preselect was requested and exists, persist it now
			if (desired) {
				const hasDesired = models.includes(desired);
				if (hasDesired) {
					modelSelect.value = desired;
					window.storageManager.setItem('preferredModel', desired);
				}
			}

        // If we just pulled a model and it hasn't registered yet, poll a few times
        if (preselectName && !models.includes(preselectName)) {
            modelSelect._retryName = preselectName;
            modelSelect._retryCount = (modelSelect._retryCount || 0) + 1;
            if (modelSelect._retryCount <= 60) { // up to ~60s
                summaryStatus.textContent = `Waiting for ${preselectName} to register... (${modelSelect._retryCount}/10)`;
                setTimeout(() => setupModelSelect(preselectName), 1000);
            } else {
                summaryStatus.textContent = `Model ${preselectName} not listed yet; try again or refresh.`;
            }
            return;
        } else {
            modelSelect._retryName = null;
            modelSelect._retryCount = 0;
        }
		}).catch(()=>{});
	}

	function getSelectedModel(){
		const stored = window.storageManager.getItem('preferredModel');
		if (stored) return stored;
		return modelSelect && modelSelect.value ? modelSelect.value : undefined;
	}

	function formatDateEST(iso){
		try{
			const d = new Date(iso);
			return new Intl.DateTimeFormat('en-US', {
				timeZone: 'America/New_York',
				year: 'numeric', month: 'short', day: '2-digit',
				hour: '2-digit', minute: '2-digit', hour12: true,
				timeZoneName: 'short'
			}).format(d);
		}catch{ return iso; }
	}

	// keyboard shortcuts
	document.addEventListener('keydown', (e) => {
		if (modal.classList.contains('hidden')) return;
		if (['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)) return;
		switch (e.key) {
			case ' ': e.preventDefault(); if (player.paused) player.play(); else player.pause(); break;
			case 'ArrowRight': player.currentTime = Math.min((player.currentTime||0)+5, (player.duration||0)); break;
			case 'ArrowLeft': player.currentTime = Math.max((player.currentTime||0)-5, 0); break;
			case '+': player.playbackRate = Math.min((player.playbackRate||1)+0.25, 3); break;
			case '-': player.playbackRate = Math.max((player.playbackRate||1)-0.25, 0.25); break;
			case 'Escape': closeModal.click(); break;
		}
	});

	// Expand all functionality
	expandAllBtn.addEventListener('click', () => {
		document.querySelectorAll('.course-header, .section-header').forEach(header => {
			header.classList.remove('collapsed');
			header.nextElementSibling.classList.remove('collapsed');
		});
	});

	// Collapse all functionality
	collapseAllBtn.addEventListener('click', () => {
		document.querySelectorAll('.course-header, .section-header').forEach(header => {
			header.classList.add('collapsed');
			header.nextElementSibling.classList.add('collapsed');
		});
	});

	// Mobile detection
	function isMobile() {
		return window.innerWidth <= 768;
	}

	// Sidebar toggle functionality with mobile and desktop support
	function toggleSidebarFunction() {
		// Reset course filter to show all courses when hamburger menu is clicked
		if (selectedCourse) {
			showAllCourses();
		}
		
		courseSidebar.classList.toggle('collapsed');
		
		if (isMobile()) {
			// On mobile, manage body scroll and overlay behavior
			if (courseSidebar.classList.contains('collapsed')) {
				document.body.style.overflow = '';
			} else {
				document.body.style.overflow = 'hidden';
			}
		} else {
			// Desktop behavior - manage floating toggle visibility
			const floatingToggle = document.getElementById('floatingToggle');
			if (floatingToggle) {
				if (courseSidebar.classList.contains('collapsed')) {
					floatingToggle.classList.remove('hidden');
				} else {
					floatingToggle.classList.add('hidden');
				}
			}
		}
	}

	// Close sidebar function
	function closeSidebar() {
		courseSidebar.classList.add('collapsed');
		document.body.style.overflow = '';
		
		// Desktop behavior - show floating toggle if on desktop
		if (!isMobile()) {
			const floatingToggle = document.getElementById('floatingToggle');
			if (floatingToggle) {
				floatingToggle.classList.remove('hidden');
			}
		}
	}

	// Mobile: Close sidebar when clicking outside
	function handleOutsideClick(event) {
		if (isMobile() && !courseSidebar.classList.contains('collapsed')) {
			// Check if click is outside sidebar and not on the mobile menu button
			if (!courseSidebar.contains(event.target) && !mobileMenuBtn.contains(event.target)) {
				closeSidebar();
			}
		}
	}

	// Mobile: Handle escape key
	function handleEscapeKey(event) {
		if (event.key === 'Escape' && isMobile() && !courseSidebar.classList.contains('collapsed')) {
			closeSidebar();
		}
	}

	// Touch gesture support for mobile sidebar
	let startX = 0;
	let currentX = 0;
	let isDragging = false;

	function handleTouchStart(event) {
		if (isMobile()) {
			startX = event.touches[0].clientX;
			isDragging = true;
		}
	}

	function handleTouchMove(event) {
		if (!isDragging || !isMobile()) return;
		
		currentX = event.touches[0].clientX;
		const diffX = currentX - startX;

		// If sidebar is open and swiping left, allow closing gesture
		if (!courseSidebar.classList.contains('collapsed') && diffX < -50) {
			event.preventDefault();
		}
	}

	function handleTouchEnd(event) {
		if (!isDragging || !isMobile()) {
			isDragging = false;
			return;
		}

		const diffX = currentX - startX;
		
		// Close sidebar if swiped left more than 100px
		if (!courseSidebar.classList.contains('collapsed') && diffX < -100) {
			closeSidebar();
		}
		
		isDragging = false;
	}

	// Enhanced course selection - now filters to show only selected course
	function scrollToCourseEnhanced(courseName) {
		// Show only the selected course
		showOnlyCourse(courseName);
		
		// Close sidebar on mobile after selecting course
		if (isMobile()) {
			setTimeout(() => {
				closeSidebar();
			}, 300);
		}
	}

	// Window resize handler
	function handleResize() {
		const floatingToggle = document.getElementById('floatingToggle');
		
		if (isMobile()) {
			// Switching to mobile view
			if (!courseSidebar.classList.contains('collapsed')) {
				document.body.style.overflow = 'hidden';
			}
			// Hide desktop floating toggle on mobile
			if (floatingToggle) {
				floatingToggle.classList.add('hidden');
			}
		} else {
			// Switching to desktop view - reset mobile styles
			document.body.style.overflow = '';
			// Manage desktop floating toggle visibility
			if (floatingToggle) {
				if (courseSidebar.classList.contains('collapsed')) {
					floatingToggle.classList.remove('hidden');
				} else {
					floatingToggle.classList.add('hidden');
				}
			}
		}
	}

	// Event listeners
	// Note: toggleSidebar button in sidebar is now hidden - only hamburger menu is used
	if (mobileMenuBtn) {
		mobileMenuBtn.addEventListener('click', toggleSidebarFunction);
	}
	
	// Desktop floating toggle (if it exists)
	const floatingToggle = document.getElementById('floatingToggle');
	if (floatingToggle) {
		floatingToggle.addEventListener('click', toggleSidebarFunction);
	}
	
	// Sync modal event listeners
	if (syncStatus) {
		syncStatus.addEventListener('click', openSyncModal);
	}
	
	if (closeSyncModal) {
		closeSyncModal.addEventListener('click', closeSyncModalFunc);
	}
	
	if (createSyncBtn) {
		createSyncBtn.addEventListener('click', createSyncGroup);
	}
	
	if (joinSyncBtn) {
		joinSyncBtn.addEventListener('click', joinSyncGroup);
	}
	
	if (syncCodeInput) {
		syncCodeInput.addEventListener('keypress', (e) => {
			if (e.key === 'Enter') {
				joinSyncGroup();
			}
		});
		
		// Auto-uppercase input
		syncCodeInput.addEventListener('input', (e) => {
			e.target.value = e.target.value.toUpperCase();
		});
	}
	
	// Close sync modal when clicking outside
	if (syncModal) {
		syncModal.addEventListener('click', (e) => {
			if (e.target === syncModal) {
				closeSyncModalFunc();
			}
		});
	}
	
	document.addEventListener('click', handleOutsideClick);
	document.addEventListener('keydown', handleEscapeKey);
	document.addEventListener('touchstart', handleTouchStart, { passive: false });
	document.addEventListener('touchmove', handleTouchMove, { passive: false });
	document.addEventListener('touchend', handleTouchEnd);
	window.addEventListener('resize', handleResize);

	// Initialize state based on device type
	if (isMobile()) {
		courseSidebar.classList.add('collapsed');
		document.body.style.overflow = '';
		// Hide desktop floating toggle on mobile
		const floatingToggle = document.getElementById('floatingToggle');
		if (floatingToggle) {
			floatingToggle.classList.add('hidden');
		}
	} else {
		// Desktop initialization - manage floating toggle visibility
		const floatingToggle = document.getElementById('floatingToggle');
		if (floatingToggle) {
			if (courseSidebar.classList.contains('collapsed')) {
				floatingToggle.classList.remove('hidden');
			} else {
				floatingToggle.classList.add('hidden');
			}
		}
	}


	// Initialize storage manager and then fetch library
	window.storageManager.initialize().then(() => {
		fetchLibrary();
		updateSyncStatus();
		
		// Update sync status periodically (less frequent to reduce DB load)
		setInterval(updateSyncStatus, 5000);
		
		// Update sync status when online/offline
		window.addEventListener('online', updateSyncStatus);
		window.addEventListener('offline', updateSyncStatus);
	}).catch(() => {
		console.warn('Storage manager initialization failed, using localStorage fallback');
		fetchLibrary();
		updateSyncStatus();
	});
})();
