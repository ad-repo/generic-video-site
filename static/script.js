(function(){
	const library = document.getElementById('library');
	const expandAllBtn = document.getElementById('expandAll');
	const collapseAllBtn = document.getElementById('collapseAll');
	const modal = document.getElementById('playerModal');
	const closeModal = document.getElementById('closeModal');
	const player = document.getElementById('player');
	const playerTitle = document.getElementById('playerTitle');
	const courseSidebar = document.getElementById('courseSidebar');
	const courseList = document.getElementById('courseList');
	const toggleSidebar = document.getElementById('toggleSidebar');
	const floatingToggle = document.getElementById('floatingToggle');
	

	let libraryData = [];
	let filtered = [];
	
	// Debug: Check if elements are found
	console.log('Course sidebar element:', courseSidebar);
	console.log('Course list element:', courseList);
	console.log('Toggle sidebar element:', toggleSidebar);

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
	const rating = localStorage.getItem(getRatingKey(courseName));
	return rating ? parseInt(rating) : 0;
}

function setRating(courseName, rating){
	localStorage.setItem(getRatingKey(courseName), rating.toString());
}

function getVideoRatingKey(videoPath){
	return `videoRating:${videoPath}`;
}

function getVideoRating(videoPath){
	const rating = localStorage.getItem(getVideoRatingKey(videoPath));
	return rating ? parseInt(rating) : 0;
}

function setVideoRating(videoPath, rating){
	localStorage.setItem(getVideoRatingKey(videoPath), rating.toString());
}

	function saveProgress(item){
		localStorage.setItem(getProgressKey(item), String(player.currentTime || 0));
	}

	function loadProgress(item){
		const v = Number(localStorage.getItem(getProgressKey(item)) || 0);
		if (!Number.isFinite(v)) return 0;
		return v;
	}

	function markAsPlayed(item){
		localStorage.setItem(getPlayedKey(item), 'true');
	}

	function isPlayed(item){
		return localStorage.getItem(getPlayedKey(item)) === 'true';
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
						`<span class="star ${i < getRating(courseName) ? 'filled' : ''}" data-rating="${i + 1}">★</span>`
					).join('')}
				</div>
				<div class="course-nav-progress">
					<div class="course-nav-progress-fill" style="width: ${progressPercent}%"></div>
				</div>
			`;
			
			courseItem.addEventListener('click', (e) => {
				e.preventDefault();
				scrollToCourse(courseName);
			});
			
			// Add star rating event listeners
			courseItem.querySelectorAll('.star').forEach(star => {
				star.addEventListener('click', (e) => {
					e.stopPropagation();
					const rating = parseInt(star.dataset.rating);
					const currentRating = getRating(courseName);
					
					// If clicking the same rating as current, clear it
					if (rating === currentRating) {
						setRating(courseName, 0);
					} else {
						setRating(courseName, rating);
					}
					render(); // Refresh to update all ratings
				});
			});
			
			courseList.appendChild(courseItem);
		});
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
								`<span class="star ${i < getRating(courseName) ? 'filled' : ''}" data-rating="${i + 1}">★</span>`
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
						`<span class="star ${i < getVideoRating(item.path) ? 'filled' : ''}" data-rating="${i + 1}">★</span>`
					).join('');
					
					// Add star rating event listeners
					videoRating.querySelectorAll('.star').forEach(star => {
						star.addEventListener('click', (e) => {
							e.stopPropagation();
							const rating = parseInt(star.dataset.rating);
							const currentRating = getVideoRating(item.path);
							
							// If clicking the same rating as current, clear it
							if (rating === currentRating) {
								setVideoRating(item.path, 0);
							} else {
								setVideoRating(item.path, rating);
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
				star.addEventListener('click', (e) => {
					e.stopPropagation();
					const rating = parseInt(star.dataset.rating);
					const currentRating = getRating(courseName);
					
					// If clicking the same rating as current, clear it
					if (rating === currentRating) {
						setRating(courseName, 0);
					} else {
						setRating(courseName, rating);
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
	}

	function openPlayer(item){
		player.pause();
		player.innerHTML = '';
		player.src = `/video/${encodeURIComponent(item.path)}`;
		playerTitle.textContent = `${item.class} — ${item.title}`;
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
		
		player.addEventListener('loadedmetadata', function onMeta(){
			player.removeEventListener('loadedmetadata', onMeta);
			if (resumeAt > 0 && resumeAt < (player.duration || Infinity)) {
				player.currentTime = resumeAt;
			}
			player.play().catch(()=>{});
		});

		// save progress periodically
		const onTime = () => {
			saveProgress(item);
			// Mark as played when 90% of video is watched
			if (player.duration && player.currentTime / player.duration >= 0.9) {
				markAsPlayed(item);
			}
		};
		player.addEventListener('timeupdate', onTime);
		const onEnded = () => {
			saveProgress(item);
			markAsPlayed(item);
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
		};
		closeModal.onclick = () => { cleanup(); modal.classList.add('hidden'); };
		modal.onclick = (e) => { if (e.target === modal) { cleanup(); modal.classList.add('hidden'); } };
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

	// Sidebar toggle functionality
	function toggleSidebarFunction() {
		courseSidebar.classList.toggle('collapsed');
		
		// Show/hide floating toggle based on sidebar state
		if (courseSidebar.classList.contains('collapsed')) {
			floatingToggle.classList.remove('hidden');
		} else {
			floatingToggle.classList.add('hidden');
		}
	}
	
	toggleSidebar.addEventListener('click', toggleSidebarFunction);
	floatingToggle.addEventListener('click', toggleSidebarFunction);


	fetchLibrary();
})();
