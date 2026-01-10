// EITBHub Homepage JavaScript
let allContent = [];
let currentDetailItem = null;
let currentCategoryItems = [];
let currentItemIndex = -1;

// Scroll position lock for modal (iOS Safari fix)
let scrollPosition = 0;

// Touch handling for mobile navigation
let touchStartX = 0;
let touchEndX = 0;

// Featured carousel state
let featuredItems = [];
let currentFeaturedIndex = 0;
let featuredCarouselInterval = null;
const CAROUSEL_INTERVAL = 5000; // 5 seconds

// Load content from JSON
async function loadContent() {
    try {
        const response = await fetch('data/content.json');
        const data = await response.json();
        return data.content || [];
    } catch (error) {
        console.error('Error loading content:', error);
        return [];
    }
}

// Category filter functions
function getRecentlyAdded(items, limit = 20) {
    const seenSeries = new Set();
    const results = [];
    
    // Sort all items by publication date first
    const sortedItems = items
        .filter(item => item.publication_date && item.thumbnail)
        .sort((a, b) => {
            const dateA = new Date(a.publication_date);
            const dateB = new Date(b.publication_date);
            return dateB - dateA;
        });
    
    // Filter out duplicate series episodes
    for (const item of sortedItems) {
        if (results.length >= limit) break;
        
        // If it's an episode, check if we've already added an episode from this series
        if (item.series_slug) {
            if (seenSeries.has(item.series_slug)) {
                continue; // Skip this episode, we already have one from this series
            }
            seenSeries.add(item.series_slug);
        }
        
        results.push(item);
    }
    
    return results;
}

function getSoonUnavailable(items, limit = 20) {
    const today = new Date();
    const sixtyDaysFromNow = new Date(today.getTime() + 60 * 24 * 60 * 60 * 1000);
    
    return items
        .filter(item => {
            if (!item.available_until || !item.thumbnail) return false;
            const expiryDate = new Date(item.available_until);
            const isExpiringSoon = expiryDate >= today && expiryDate <= sixtyDaysFromNow;
            // Only include VOD/movie content, not episodes or series
            const isVod = item.type === 'vod' || item.type === 'movie';
            const notEpisode = !item.series_slug;
            return isExpiringSoon && isVod && notEpisode;
        })
        .sort((a, b) => {
            return new Date(a.available_until) - new Date(b.available_until);
        })
        .slice(0, limit);
}

function getMovies(items, limit = 20) {
    return items
        .filter(item => {
            const isMovie = item.type === 'vod' || item.type === 'movie';
            const hasImage = item.thumbnail;
            const notEpisode = !item.series_slug;
            return isMovie && hasImage && notEpisode;
        })
        .sort((a, b) => {
            // Sort by publication_date DESC, or year DESC if no pub date
            if (a.publication_date && b.publication_date) {
                return new Date(b.publication_date) - new Date(a.publication_date);
            }
            if (a.year && b.year) {
                return b.year - a.year;
            }
            return 0;
        })
        .slice(0, limit);
}

function getSeries(items, limit = 20) {
    // Group episodes by series_slug
    const seriesMap = new Map();
    
    items.forEach(item => {
        if (item.series_slug && item.type === 'episode') {
            if (!seriesMap.has(item.series_slug)) {
                seriesMap.set(item.series_slug, {
                    series_slug: item.series_slug,
                    series_title: item.series_title || item.series_slug,
                    episodes: [],
                    latest_date: null,
                    thumbnail: null
                });
            }
            
            const series = seriesMap.get(item.series_slug);
            series.episodes.push(item);
            
            // Track latest publication date
            if (item.publication_date) {
                const itemDate = new Date(item.publication_date);
                if (!series.latest_date || itemDate > series.latest_date) {
                    series.latest_date = itemDate;
                }
            }
            
            // Use first episode's thumbnail
            if (!series.thumbnail && item.thumbnail) {
                series.thumbnail = item.thumbnail;
            }
        }
    });
    
    // Convert to array and sort by latest episode date
    return Array.from(seriesMap.values())
        .filter(series => series.thumbnail) // Only include series with thumbnails
        .sort((a, b) => {
            if (a.latest_date && b.latest_date) {
                return b.latest_date - a.latest_date;
            }
            return 0;
        })
        .slice(0, limit);
}

function getChildrenContent(items, limit = 20) {
    const kidsRatings = ['TP', '0-4', '5-7', '+7', '7'];
    
    return items
        .filter(item => {
            const isKidsRating = kidsRatings.includes(item.age_rating);
            const isStandalone = item.type === 'vod' || item.type === 'movie';
            const notEpisode = !item.series_slug;
            const hasImage = item.thumbnail;
            return isKidsRating && isStandalone && notEpisode && hasImage;
        })
        .sort((a, b) => {
            if (a.publication_date && b.publication_date) {
                return new Date(b.publication_date) - new Date(a.publication_date);
            }
            return 0;
        })
        .slice(0, limit);
}

// Render functions
function renderThumbnailCard(item, isSeries = false) {
    const title = isSeries ? item.series_title : (item.title || item.slug || 'Izenbururik gabe');
    const thumbnail = item.thumbnail || '';
    
    // Prepare badges
    let badgesHtml = '';
    if (!isSeries && item.is_geo_restricted === true) {
        badgesHtml += '<span class="card-badge geo-badge"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 1em; height: 1em; display: inline-block; vertical-align: middle;"><path stroke-linecap="round" stroke-linejoin="round" d="m20.893 13.393-1.135-1.135a2.252 2.252 0 0 1-.421-.585l-1.08-2.16a.414.414 0 0 0-.663-.107.827.827 0 0 1-.812.21l-1.273-.363a.89.89 0 0 0-.738 1.595l.587.39c.59.395.674 1.23.172 1.732l-.2.2c-.212.212-.33.498-.33.796v.41c0 .409-.11.809-.32 1.158l-1.315 2.191a2.11 2.11 0 0 1-1.81 1.025 1.055 1.055 0 0 1-1.055-1.055v-1.172c0-.92-.56-1.747-1.414-2.089l-.655-.261a2.25 2.25 0 0 1-1.383-2.46l.007-.042a2.25 2.25 0 0 1 .29-.787l.09-.15a2.25 2.25 0 0 1 2.37-1.048l1.178.236a1.125 1.125 0 0 0 1.302-.795l.208-.73a1.125 1.125 0 0 0-.578-1.315l-.665-.332-.091.091a2.25 2.25 0 0 1-1.591.659h-.18c-.249 0-.487.1-.662.274a.931.931 0 0 1-1.458-1.137l1.411-2.353a2.25 2.25 0 0 0 .286-.76m11.928 9.869A9 9 0 0 0 8.965 3.525m11.928 9.868A9 9 0 1 1 8.965 3.525" /></svg></span>';
    }
    if (!isSeries && item.age_rating) {
        badgesHtml += `<span class="card-badge age-badge">${escapeHtml(item.age_rating)}</span>`;
    }
    if (isSeries && item.episodes) {
        badgesHtml += `<span class="card-badge episode-count-badge">${item.episodes.length} atal</span>`;
    }
    
    return `
        <div class="thumbnail-card" data-slug="${escapeHtml(isSeries ? item.series_slug : item.slug)}" data-is-series="${isSeries}">
            <div class="card-image-wrapper">
                <img src="${escapeHtml(thumbnail)}" 
                     alt="${escapeHtml(title)}" 
                     loading="lazy"
                     onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22300%22%3E%3Crect fill=%22%23333%22 width=%22200%22 height=%22300%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 fill=%22%23666%22 font-size=%2220%22%3ENo Image%3C/text%3E%3C/svg%3E'">
                <div class="card-overlay">
                    <div class="card-title">${escapeHtml(title)}</div>
                    ${badgesHtml ? `<div class="card-badges">${badgesHtml}</div>` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderCategory(category, items, container) {
    if (!items || items.length === 0) return;
    
    const categoryId = category.id;
    const categoryTitle = category.title;
    const isSeries = category.id === 'series';
    
    const categoryHtml = `
        <div class="category-row" id="category-${categoryId}">
            <h2 class="category-title">${escapeHtml(categoryTitle)}</h2>
            <div class="cards-container" data-category="${categoryId}">
                ${items.map(item => renderThumbnailCard(item, isSeries)).join('')}
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', categoryHtml);
    
    // Attach click handlers
    const cards = container.querySelectorAll(`[data-category="${categoryId}"] .thumbnail-card`);
    cards.forEach((card, index) => {
        card.addEventListener('click', () => {
            const slug = card.getAttribute('data-slug');
            const isSeriesCard = card.getAttribute('data-is-series') === 'true';
            
            if (isSeriesCard) {
                openSeriesModal(items[index]);
            } else {
                currentCategoryItems = items;
                currentItemIndex = index;
                openDetailModal(items[index]);
            }
        });
    });
}

function renderHeroBanner(item) {
    if (!item || !item.thumbnail) return;
    
    const heroBanner = document.getElementById('hero-banner');
    const heroTitle = document.getElementById('hero-title');
    const heroDescription = document.getElementById('hero-description');
    const heroMeta = document.getElementById('hero-meta');
    const heroBtn = document.getElementById('hero-view-btn');
    
    // Set background with fade transition
    heroBanner.style.backgroundImage = `url('${item.thumbnail}')`;
    heroBanner.style.display = 'block';
    
    // Set content
    heroTitle.textContent = item.title || item.slug || 'Izenbururik gabe';
    heroDescription.textContent = item.description || '';
    
    // Meta info
    let metaHtml = '';
    if (item.year) metaHtml += `<span>${item.year}</span>`;
    if (item.duration) metaHtml += `<span>${formatDuration(item.duration)}</span>`;
    if (item.age_rating) metaHtml += `<span class="age-rating-badge">${escapeHtml(item.age_rating)}</span>`;
    heroMeta.innerHTML = metaHtml;
    
    // Button handler
    heroBtn.onclick = () => {
        currentCategoryItems = [item];
        currentItemIndex = 0;
        openDetailModal(item);
    };
}

function initFeaturedCarousel(items) {
    if (!items || items.length === 0) return;
    
    featuredItems = items;
    currentFeaturedIndex = 0;
    
    // Create carousel indicators
    const heroBanner = document.getElementById('hero-banner');
    let indicatorsContainer = document.getElementById('carousel-indicators');
    
    if (!indicatorsContainer) {
        indicatorsContainer = document.createElement('div');
        indicatorsContainer.id = 'carousel-indicators';
        indicatorsContainer.className = 'carousel-indicators';
        heroBanner.appendChild(indicatorsContainer);
    }
    
    indicatorsContainer.innerHTML = '';
    items.forEach((_, index) => {
        const dot = document.createElement('button');
        dot.className = 'carousel-dot';
        dot.setAttribute('aria-label', `Go to slide ${index + 1}`);
        if (index === 0) dot.classList.add('active');
        dot.onclick = () => goToFeaturedSlide(index);
        indicatorsContainer.appendChild(dot);
    });
    
    // Render first item
    renderHeroBanner(items[0]);
    
    // Start auto-rotation
    startFeaturedCarousel();
}

function goToFeaturedSlide(index) {
    if (index < 0 || index >= featuredItems.length) return;
    
    currentFeaturedIndex = index;
    renderHeroBanner(featuredItems[index]);
    updateCarouselIndicators();
    
    // Reset auto-rotation timer
    stopFeaturedCarousel();
    startFeaturedCarousel();
}

function nextFeaturedSlide() {
    currentFeaturedIndex = (currentFeaturedIndex + 1) % featuredItems.length;
    renderHeroBanner(featuredItems[currentFeaturedIndex]);
    updateCarouselIndicators();
}

function updateCarouselIndicators() {
    const dots = document.querySelectorAll('.carousel-dot');
    dots.forEach((dot, index) => {
        if (index === currentFeaturedIndex) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
}

function startFeaturedCarousel() {
    stopFeaturedCarousel(); // Clear any existing interval
    featuredCarouselInterval = setInterval(nextFeaturedSlide, CAROUSEL_INTERVAL);
}

function stopFeaturedCarousel() {
    if (featuredCarouselInterval) {
        clearInterval(featuredCarouselInterval);
        featuredCarouselInterval = null;
    }
}

// Modal functions
function openDetailModal(item) {
    if (!item) return;
    
    currentDetailItem = item;
    const modal = document.getElementById('mobile-detail-modal');
    
    // Populate modal
    const poster = document.getElementById('mobile-detail-poster');
    poster.src = item.thumbnail || '';
    poster.style.display = item.thumbnail ? 'block' : 'none';
    
    document.getElementById('mobile-detail-title').textContent = 
        item.title || item.series_title || item.slug || 'Izenbururik gabe';
    
    // Series info for episodes (add before description)
    const descriptionEl = document.getElementById('mobile-detail-description');
    let seriesInfoHtml = '';
    
    if (item.series_slug && item.series_title) {
        // This is an episode - add series info
        seriesInfoHtml = '<div class="episode-series-info">';
        seriesInfoHtml += `<div class="series-info-text">`;
        seriesInfoHtml += `<strong>${escapeHtml(item.series_title)}</strong>`;
        if (item.season_number) {
            seriesInfoHtml += ` • ${item.season_number}. denboraldia`;
        }
        if (item.episode_number) {
            seriesInfoHtml += ` • ${item.episode_number}. atala`;
        }
        seriesInfoHtml += `</div>`;
        seriesInfoHtml += `<button class="view-series-btn" data-series-slug="${escapeHtml(item.series_slug)}">Atal guztiak ikusi ›</button>`;
        seriesInfoHtml += '</div>';
    }
    
    descriptionEl.innerHTML = seriesInfoHtml + 
        '<p class="episode-description-text">' + 
        escapeHtml(item.description || 'Ez dago deskribapenik eskuragarri.') + 
        '</p>';
    
    // Add click handler for "view all episodes" button
    if (item.series_slug) {
        setTimeout(() => {
            const viewSeriesBtn = descriptionEl.querySelector('.view-series-btn');
            if (viewSeriesBtn) {
                viewSeriesBtn.addEventListener('click', () => {
                    // Find all episodes from this series
                    const seriesEpisodes = allContent.filter(content => 
                        content.series_slug === item.series_slug && content.type === 'episode'
                    );
                    
                    if (seriesEpisodes.length > 0) {
                        // Create series object
                        const seriesObj = {
                            series_slug: item.series_slug,
                            series_title: item.series_title,
                            episodes: seriesEpisodes,
                            thumbnail: item.thumbnail || seriesEpisodes[0]?.thumbnail
                        };
                        
                        openSeriesModal(seriesObj);
                    }
                });
            }
        }, 0);
    }
    
    // Meta
    const metaContainer = document.getElementById('mobile-detail-meta');
    let metaHtml = '';
    if (item.year) metaHtml += `<span>${item.year}</span> • `;
    if (item.duration) metaHtml += `<span>${formatDuration(item.duration)}</span> • `;
    if (item.age_rating) metaHtml += `<span class="age-rating-badge">${escapeHtml(item.age_rating)}</span>`;
    metaContainer.innerHTML = metaHtml;
    
    // Badges
    const badgesContainer = document.getElementById('mobile-detail-badges');
    let badgesHtml = '';
    
    // Platform
    if (item.platform) {
        const platforms = Array.isArray(item.platform) ? item.platform : [item.platform];
        badgesHtml += platforms.map(p => {
            const platformName = p.replace('.eus', '').toLowerCase();
            return `<span class="platform-badge platform-badge-${platformName}">${platformName.charAt(0).toUpperCase() + platformName.slice(1)}</span>`;
        }).join(' ');
    }
    
    // Geo restriction
    if (item.is_geo_restricted === true) {
        badgesHtml += '<span class="status-badge status-restricted">Geo-Murriztua</span>';
    }
    
    // Expiration date (if within next 12 months)
    if (shouldShowExpirationDate(item.available_until)) {
        const formattedDate = formatExpirationDate(item.available_until);
        badgesHtml += `<span class="expiration-badge">Noiz arte: ${formattedDate}</span>`;
    }
    
    badgesContainer.innerHTML = badgesHtml;
    
    // Link
    const linkBtn = document.getElementById('mobile-detail-link');
    if (item.content_url) {
        linkBtn.href = item.content_url;
        linkBtn.style.display = 'flex';
    } else {
        linkBtn.style.display = 'none';
    }
    
    // Update navigation buttons
    updateNavButtons();
    
    // Show modal
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    lockBodyScroll();
}

function openSeriesModal(series) {
    if (!series || !series.episodes || series.episodes.length === 0) return;
    
    const firstEpisode = series.episodes[0];
    
    // Store for navigation
    currentDetailItem = series;
    currentCategoryItems = series.episodes;
    currentItemIndex = 0;
    
    const modal = document.getElementById('mobile-detail-modal');
    
    // Populate modal
    const poster = document.getElementById('mobile-detail-poster');
    poster.src = series.thumbnail || '';
    poster.style.display = series.thumbnail ? 'block' : 'none';
    
    document.getElementById('mobile-detail-title').textContent = series.series_title;
    
    // Build episode list
    const descriptionEl = document.getElementById('mobile-detail-description');
    descriptionEl.innerHTML = renderEpisodeList(series.episodes);
    descriptionEl.classList.add('series-episode-list');
    
    // Meta
    const metaContainer = document.getElementById('mobile-detail-meta');
    metaContainer.innerHTML = `<span>${series.episodes.length} atal</span>`;
    
    // Badges
    const badgesContainer = document.getElementById('mobile-detail-badges');
    let badgesHtml = '';
    if (firstEpisode && firstEpisode.platform) {
        const platforms = Array.isArray(firstEpisode.platform) ? firstEpisode.platform : [firstEpisode.platform];
        badgesHtml = platforms.map(p => {
            const platformName = p.replace('.eus', '').toLowerCase();
            return `<span class="platform-badge platform-badge-${platformName}">${platformName.charAt(0).toUpperCase() + platformName.slice(1)}</span>`;
        }).join(' ');
    }
    
    // Check if any episode has expiration date within next 12 months
    const earliestExpiration = series.episodes
        .filter(ep => shouldShowExpirationDate(ep.available_until))
        .map(ep => new Date(ep.available_until))
        .sort((a, b) => a - b)[0];
    
    if (earliestExpiration) {
        const formattedDate = formatExpirationDate(earliestExpiration.toISOString());
        badgesHtml += `<span class="expiration-badge">Noiz arte: ${formattedDate}</span>`;
    }
    
    badgesContainer.innerHTML = badgesHtml;
    
    // Hide link button for series
    document.getElementById('mobile-detail-link').style.display = 'none';
    
    // Update navigation buttons
    updateNavButtons();
    
    // Show modal
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    lockBodyScroll();
    
    // Attach episode click handlers
    setTimeout(() => {
        const episodeItems = descriptionEl.querySelectorAll('.episode-list-item');
        episodeItems.forEach((el, idx) => {
            el.addEventListener('click', () => {
                currentItemIndex = idx;
                openDetailModal(series.episodes[idx]);
            });
        });
    }, 100);
}

function renderEpisodeList(episodes) {
    if (!episodes || episodes.length === 0) {
        return '<p class="no-episodes">Ez dago atalik eskuragarri.</p>';
    }
    
    let html = '<div class="episode-list-container">';
    
    // Group by season
    const episodesBySeason = new Map();
    episodes.forEach((episode, index) => {
        const seasonKey = episode.season_number || 'unknown';
        if (!episodesBySeason.has(seasonKey)) {
            episodesBySeason.set(seasonKey, []);
        }
        episodesBySeason.get(seasonKey).push({ episode, index });
    });
    
    // Sort seasons
    const sortedSeasons = Array.from(episodesBySeason.keys()).sort((a, b) => {
        if (a === 'unknown') return 1;
        if (b === 'unknown') return -1;
        return a - b;
    });
    
    sortedSeasons.forEach(seasonKey => {
        const seasonEpisodes = episodesBySeason.get(seasonKey);
        
        // Season header
        if (seasonKey !== 'unknown') {
            html += `<div class="episode-season-header">${seasonKey}. denboraldia</div>`;
        } else {
            html += `<div class="episode-season-header">Denboraldia ezezaguna</div>`;
        }
        
        // Episodes
        seasonEpisodes.forEach(({ episode, index }) => {
            const title = episode.title || episode.slug || 'Izen gabea';
            const duration = episode.duration ? formatDuration(episode.duration) : '';
            const thumbnail = episode.thumbnail || '';
            
            let episodeLabel = '';
            if (episode.season_number) {
                episodeLabel += `D${episode.season_number}`;
            }
            if (episode.episode_number) {
                episodeLabel += `:${episode.episode_number}`;
            }
            
            let restrictionBadge = '';
            if (episode.is_geo_restricted === true) {
                restrictionBadge = '<span class="episode-geo-badge restricted"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 1em; height: 1em; display: inline-block; vertical-align: middle;"><path stroke-linecap="round" stroke-linejoin="round" d="m20.893 13.393-1.135-1.135a2.252 2.252 0 0 1-.421-.585l-1.08-2.16a.414.414 0 0 0-.663-.107.827.827 0 0 1-.812.21l-1.273-.363a.89.89 0 0 0-.738 1.595l.587.39c.59.395.674 1.23.172 1.732l-.2.2c-.212.212-.33.498-.33.796v.41c0 .409-.11.809-.32 1.158l-1.315 2.191a2.11 2.11 0 0 1-1.81 1.025 1.055 1.055 0 0 1-1.055-1.055v-1.172c0-.92-.56-1.747-1.414-2.089l-.655-.261a2.25 2.25 0 0 1-1.383-2.46l.007-.042a2.25 2.25 0 0 1 .29-.787l.09-.15a2.25 2.25 0 0 1 2.37-1.048l1.178.236a1.125 1.125 0 0 0 1.302-.795l.208-.73a1.125 1.125 0 0 0-.578-1.315l-.665-.332-.091.091a2.25 2.25 0 0 1-1.591.659h-.18c-.249 0-.487.1-.662.274a.931.931 0 0 1-1.458-1.137l1.411-2.353a2.25 2.25 0 0 0 .286-.76m11.928 9.869A9 9 0 0 0 8.965 3.525m11.928 9.868A9 9 0 1 1 8.965 3.525" /></svg></span>';
            } else if (episode.is_geo_restricted === false) {
                restrictionBadge = '<span class="episode-geo-badge accessible">✓</span>';
            }
            
            html += `
                <div class="episode-list-item" data-episode-index="${index}">
                    <div class="episode-thumbnail">
                        ${thumbnail ? `<img src="${escapeHtml(thumbnail)}" alt="${escapeHtml(title)}" loading="lazy">` : '<div class="episode-thumbnail-placeholder"></div>'}
                    </div>
                    <div class="episode-info">
                        <div class="episode-header">
                            ${episodeLabel ? `<span class="episode-label">${escapeHtml(episodeLabel)}</span>` : ''}
                            ${restrictionBadge}
                        </div>
                        <div class="episode-title">${escapeHtml(title)}</div>
                        ${duration ? `<div class="episode-duration">${duration}</div>` : ''}
                    </div>
                    <div class="episode-arrow">›</div>
                </div>
            `;
        });
    });
    
    html += '</div>';
    return html;
}

function closeDetailModal() {
    const modal = document.getElementById('mobile-detail-modal');
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    unlockBodyScroll();
    
    // Clear series episode list class
    const descriptionEl = document.getElementById('mobile-detail-description');
    descriptionEl.classList.remove('series-episode-list');
}

function updateNavButtons() {
    const prevBtn = document.getElementById('mobile-nav-prev');
    const nextBtn = document.getElementById('mobile-nav-next');
    
    if (!prevBtn || !nextBtn) return;
    
    prevBtn.disabled = currentItemIndex <= 0;
    nextBtn.disabled = currentItemIndex >= currentCategoryItems.length - 1;
}

function navigateItem(direction) {
    const newIndex = currentItemIndex + direction;
    
    if (newIndex < 0 || newIndex >= currentCategoryItems.length) return;
    
    currentItemIndex = newIndex;
    openDetailModal(currentCategoryItems[newIndex]);
}

// Utility functions
function formatDuration(seconds) {
    if (!seconds) return '-';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    return `${minutes}:${String(secs).padStart(2, '0')}`;
}

// Check if content should show expiration date (within next 12 months)
function shouldShowExpirationDate(availableUntil) {
    if (!availableUntil) return false;
    
    const today = new Date();
    const expiryDate = new Date(availableUntil);
    const twelveMonthsFromNow = new Date(today);
    twelveMonthsFromNow.setMonth(twelveMonthsFromNow.getMonth() + 12);
    
    return expiryDate >= today && expiryDate <= twelveMonthsFromNow;
}

// Format date as YYYY/MM/DD
function formatExpirationDate(availableUntil) {
    if (!availableUntil) return '';
    
    const date = new Date(availableUntil);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}/${month}/${day}`;
}

function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function lockBodyScroll() {
    scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
    document.body.style.top = `-${scrollPosition}px`;
    document.body.classList.add('modal-open');
}

function unlockBodyScroll() {
    document.body.classList.remove('modal-open');
    document.body.style.top = '';
    window.scrollTo(0, scrollPosition);
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Show loading indicator
    const loadingIndicator = document.getElementById('loading-indicator');
    loadingIndicator.style.display = 'flex';
    
    // Load content
    allContent = await loadContent();
    
    // Hide loading indicator
    loadingIndicator.style.display = 'none';
    
    if (allContent.length === 0) {
        document.getElementById('categories-container').innerHTML = 
            '<div class="error-message">Ez da edukia kargatu. Mesedez, saiatu berriro.</div>';
        return;
    }
    
    // Define categories
    const categories = [
        { id: 'recent', title: 'Duela gutxi gehitutakoa', items: getRecentlyAdded(allContent) },
        { id: 'expiring', title: 'Azken aukera', items: getSoonUnavailable(allContent) },
        { id: 'movies', title: 'Filmak', items: getMovies(allContent) },
        { id: 'series', title: 'Serieak', items: getSeries(allContent) },
        { id: 'kids', title: 'Haurrak', items: getChildrenContent(allContent) }
    ];
    
    // Render hero banner with 10 most recent films (VOD only, no episodes)
    const recentFilms = allContent
        .filter(item => {
            const isVod = item.type === 'vod' || item.type === 'movie';
            const notEpisode = !item.series_slug;
            const hasImage = item.thumbnail;
            const hasDate = item.publication_date;
            return isVod && notEpisode && hasImage && hasDate;
        })
        .sort((a, b) => new Date(b.publication_date) - new Date(a.publication_date))
        .slice(0, 10);
    
    if (recentFilms.length > 0) {
        initFeaturedCarousel(recentFilms);
    }
    
    // Render categories
    const container = document.getElementById('categories-container');
    categories.forEach(cat => {
        if (cat.items.length > 0) {
            renderCategory(cat, cat.items, container);
        }
    });
    
    // Setup modal event listeners
    const closeBtn = document.getElementById('mobile-detail-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeDetailModal);
    }
    
    const prevBtn = document.getElementById('mobile-nav-prev');
    if (prevBtn) {
        prevBtn.addEventListener('click', () => navigateItem(-1));
    }
    
    const nextBtn = document.getElementById('mobile-nav-next');
    if (nextBtn) {
        nextBtn.addEventListener('click', () => navigateItem(1));
    }
    
    // Swipe gestures for mobile
    const modal = document.getElementById('mobile-detail-modal');
    if (modal) {
        modal.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });
        
        modal.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }, { passive: true });
    }
});

function handleSwipe() {
    const threshold = 50;
    const diff = touchStartX - touchEndX;
    
    if (Math.abs(diff) > threshold) {
        if (diff > 0) {
            // Swipe left -> next
            navigateItem(1);
        } else {
            // Swipe right -> previous
            navigateItem(-1);
        }
    }
}
