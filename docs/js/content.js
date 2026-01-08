// Content List JavaScript
let allContent = [];
let groupedContent = { series: [], standalone: [] };
let filteredGroupedContent = { series: [], standalone: [] };
let expandedSeries = new Set();
// Track which individual item (by slug) has its detail row expanded.
// We keep this as a Set for simplicity, but enforce a single active slug.
let expandedRows = new Set();
let currentDetailValues = {
    index: -1,
    items: []
};

// Touch handling variables
let touchStartX = 0;
let touchEndX = 0;

// Auto-hide navigation arrows timer
let navHideTimer = null;
const NAV_HIDE_DELAY = 3000; // 3 seconds

// Scroll position lock for modal (iOS Safari fix)
let scrollPosition = 0;


// Attempt to infer season number from a title prefix like "D7: 1. Tartaldea"
function inferSeasonFromTitle(title) {
    if (!title) return null;
    const match = String(title).trim().match(/^D\s*([0-9]+)/i);
    if (match && match[1]) {
        const num = parseInt(match[1], 10);
        return isNaN(num) ? null : num;
    }
    return null;
}
let currentSort = { field: null, direction: 'asc' };

// Pagination state
let pageSize = 100; // rows per page (flattened rows: standalone items, series headers, and expanded episodes)
let currentPage = 1; // 1-based index

// Build a flattened list of rows (standalone items, series headers, and expanded episodes)
function buildFlattenedRows() {
    const rows = [];

    // Standalone items first
    filteredGroupedContent.standalone.forEach(item => {
        rows.push({ type: 'standalone', item });
    });

    // Series and their episodes
    filteredGroupedContent.series.forEach(series => {
        const isExpanded = expandedSeries.has(series.series_slug);
        rows.push({ type: 'series', series, isExpanded });

        if (isExpanded) {
            series.episodes.forEach(episode => {
                rows.push({ type: 'episode', item: episode, seriesSlug: series.series_slug, isExpanded });
            });
        }
    });

    return rows;
}

// Get total number of rendered rows (for pagination)
function getTotalRows() {
    return buildFlattenedRows().length;
}

// Get total number of pages
function getPageCount(totalRows) {
    if (totalRows === 0) return 1;
    return Math.max(1, Math.ceil(totalRows / pageSize));
}

// Navigate to a specific page
function goToPage(page) {
    const totalRows = getTotalRows();
    const pageCount = getPageCount(totalRows);
    const targetPage = Math.min(Math.max(1, page), pageCount);
    if (targetPage !== currentPage) {
        currentPage = targetPage;
        renderTable();
        updateResultsCount(); // keep counts and page info in sync
    }
}

// Change page size
function changePageSize(newSize) {
    const size = parseInt(newSize, 10);
    if (!isNaN(size) && size > 0) {
        pageSize = size;
        currentPage = 1;
        renderTable();
        updateResultsCount();
    }
}

// Load content data
async function loadContent() {
    try {
        const response = await fetch('data/content.json');
        const data = await response.json();
        allContent = data.content || [];

        groupContentBySeries();
        filteredGroupedContent = JSON.parse(JSON.stringify(groupedContent));

        populateFilters();
        renderTable();
        updateResultsCount();
    } catch (error) {
        console.error('Error loading content:', error);
        document.getElementById('content-tbody').innerHTML =
            '<tr><td colspan="10" style="color: red;">Error loading content. Please ensure data/content.json exists.</td></tr>';
    }
}

// Group content by series
function groupContentBySeries() {
    const episodes = [];
    const standalone = [];
    const seriesRecords = new Map(); // Map of series records (type === 'series')
    const seriesMap = new Map(); // Map of series groups (from episodes)

    // First pass: separate content by type
    allContent.forEach(item => {
        if (item.type === 'series') {
            // Store series records separately
            seriesRecords.set(item.slug, item);
        } else if (item.series_slug) {
            // Group any content with series_slug as episodes (even if type is 'unknown' or other)
            // This handles cases where episodes were incorrectly saved with type='unknown'
            episodes.push(item);
        } else {
            standalone.push(item);
        }
    });

    // Group episodes by series
    episodes.forEach(episode => {
        const seriesSlug = episode.series_slug;
        if (!seriesMap.has(seriesSlug)) {
            // Check if we have a series record for this slug
            const seriesRecord = seriesRecords.get(seriesSlug);

            seriesMap.set(seriesSlug, {
                series_slug: seriesSlug,
                series_title: seriesRecord ? seriesRecord.title : (episode.series_title || seriesSlug),
                episodes: [],
                episode_count: 0,
                restricted_count: 0,
                accessible_count: 0,
                unknown_count: 0,
                is_expanded: false,
                platform: seriesRecord ? seriesRecord.platform : episode.platform // Use series record platform if available
            });
        }

        const series = seriesMap.get(seriesSlug);
        series.episodes.push(episode);
        series.episode_count++;

        if (episode.is_geo_restricted === true) {
            series.restricted_count++;
        } else if (episode.is_geo_restricted === false) {
            series.accessible_count++;
        } else {
            series.unknown_count++;
        }
    });

    // Also add series records that don't have episodes yet (if any)
    seriesRecords.forEach((seriesRecord, slug) => {
        if (!seriesMap.has(slug)) {
            // Series record exists but no episodes found - create empty series entry
            seriesMap.set(slug, {
                series_slug: slug,
                series_title: seriesRecord.title || slug,
                episodes: [],
                episode_count: 0,
                restricted_count: 0,
                accessible_count: 0,
                unknown_count: 0,
                is_expanded: false,
                platform: seriesRecord.platform
            });
        }
    });

    groupedContent = {
        series: Array.from(seriesMap.values()),
        standalone: standalone
    };

    // Enrich series with season ordering and computed season_display for episodes
    groupedContent.series.forEach(series => {
        // Build a stable season order: smallest season_number -> Season 1, etc.
        const seasonNumbers = Array.from(
            new Set(
                series.episodes
                    .map(ep => {
                        if (ep.season_number !== null && ep.season_number !== undefined) {
                            return ep.season_number;
                        }
                        // Fallback: try to infer from title
                        const inferred = inferSeasonFromTitle(ep.title);
                        return inferred !== null && inferred !== undefined ? inferred : null;
                    })
                    .filter(n => n !== null && n !== undefined)
            )
        ).sort((a, b) => a - b);

        const seasonOrderMap = {};
        seasonNumbers.forEach((num, idx) => {
            seasonOrderMap[num] = idx + 1;
        });
        series.season_order_map = seasonOrderMap;

        // Attach a season_display to each episode (preferred: mapped order; fallback: title prefix)
        series.episodes.forEach(ep => {
            if (ep.season_number != null && seasonOrderMap[ep.season_number]) {
                ep.season_display = seasonOrderMap[ep.season_number];
            } else {
                const inferred = inferSeasonFromTitle(ep.title);
                if (inferred != null) {
                    ep.season_display = inferred;
                }
            }
        });

        // Default sort for episodes: season (mapped/inferred) -> episode_number -> title
        series.episodes.sort((a, b) => {
            const seasonA = a.season_display ?? a.season_number ?? inferSeasonFromTitle(a.title) ?? Number.MAX_SAFE_INTEGER;
            const seasonB = b.season_display ?? b.season_number ?? inferSeasonFromTitle(b.title) ?? Number.MAX_SAFE_INTEGER;
            if (seasonA !== seasonB) return seasonA - seasonB;

            const epA = a.episode_number ?? Number.MAX_SAFE_INTEGER;
            const epB = b.episode_number ?? Number.MAX_SAFE_INTEGER;
            if (epA !== epB) return epA - epB;

            return String(a.title || a.slug || '').localeCompare(String(b.title || b.slug || ''));
        });
    });
}

// Populate all filter dropdowns
function populateFilters() {
    populateTypeFilter();
    populateAgeRatingFilter();
    populateLanguageFilter();
    populatePlatformFilter();
    populateMediaTypeFilter();

    // Mobile filters toggle
    const filtersToggle = document.getElementById('filters-toggle');
    const filtersContainer = document.getElementById('filters-container');
    const filterModalClose = document.getElementById('filter-modal-close');
    const filterApplyBtn = document.getElementById('filter-apply-btn');

    if (filtersToggle && filtersContainer) {
        filtersToggle.addEventListener('click', () => {
            // Mobile modal: just add 'open' class
            filtersContainer.classList.add('open');
            lockBodyScroll();
        });
    }

    if (filterModalClose && filtersContainer) {
        filterModalClose.addEventListener('click', () => {
            filtersContainer.classList.remove('open');
            unlockBodyScroll();
        });
    }

    if (filterApplyBtn && filtersContainer) {
        filterApplyBtn.addEventListener('click', () => {
            filtersContainer.classList.remove('open');
            unlockBodyScroll();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
}

// Populate type filter dropdown
function populateTypeFilter() {
    const typeFilter = document.getElementById('type-filter');
    // Collect distinct types from content. We intentionally hide the synthetic
    // "series" type from the Mota (Type) dropdown because series are represented
    // as grouped episode rows in the UI, not as standalone items that can be
    // directly filtered by type.
    const types = [...new Set(
        allContent
            .map(item => item.type)
            .filter(type => type && type !== 'series')
    )].sort();

    types.forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        typeFilter.appendChild(option);
    });
}

// Populate age rating filter
function populateAgeRatingFilter() {
    const ageFilter = document.getElementById('age-rating-filter');
    const ratings = [...new Set(allContent.map(item => item.age_rating).filter(Boolean))].sort();

    ratings.forEach(rating => {
        const option = document.createElement('option');
        option.value = rating;
        option.textContent = rating;
        ageFilter.appendChild(option);
    });
}

// Populate language filter
function populateLanguageFilter() {
    const langFilter = document.getElementById('language-filter');
    const languages = new Set();

    allContent.forEach(item => {
        if (item.languages && Array.isArray(item.languages)) {
            item.languages.forEach(lang => languages.add(lang));
        }
    });

    Array.from(languages).sort().forEach(lang => {
        const option = document.createElement('option');
        option.value = lang;
        option.textContent = lang.toUpperCase();
        langFilter.appendChild(option);
    });
}

// Populate platform filter
function populatePlatformFilter() {
    const platformFilter = document.getElementById('platform-filter');
    const platformsSet = new Set();

    // Clear existing options except "Guztia"
    while (platformFilter.children.length > 1) {
        platformFilter.removeChild(platformFilter.lastChild);
    }

    // Extract platforms from array (platform is now a JSON array)
    allContent.forEach(item => {
        const itemPlatforms = Array.isArray(item.platform) ? item.platform :
            (typeof item.platform === 'string' ? JSON.parse(item.platform) : []);
        itemPlatforms.forEach(p => {
            if (p) platformsSet.add(p);
        });
    });

    const platforms = [...platformsSet].sort();

    platforms.forEach(platform => {
        const option = document.createElement('option');
        option.value = platform;
        // Display name: extract domain name (e.g., "makusi.eus" -> "Makusi")
        const displayName = platform.replace('.eus', '').replace('.', ' ').replace(/\b\w/g, l => l.toUpperCase());
        option.textContent = displayName;
        platformFilter.appendChild(option);
    });
}

// Populate media type filter
function populateMediaTypeFilter() {
    const mediaTypeFilter = document.getElementById('media-type-filter');

    // Clear existing options except "Guztia"
    while (mediaTypeFilter.children.length > 1) {
        mediaTypeFilter.removeChild(mediaTypeFilter.lastChild);
    }

    const mediaTypes = [...new Set(allContent.map(item => item.media_type).filter(Boolean))].sort();

    // Map English values to Basque display names
    const mediaTypeLabels = {
        'audio': 'Audio',
        'video': 'Bideo'
    };

    mediaTypes.forEach(mediaType => {
        const option = document.createElement('option');
        option.value = mediaType;
        option.textContent = mediaTypeLabels[mediaType] || mediaType.charAt(0).toUpperCase() + mediaType.slice(1);
        mediaTypeFilter.appendChild(option);
    });
}

// Apply filters
function applyFilters() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const typeFilter = document.getElementById('type-filter').value;
    const restrictionFilter = document.getElementById('restriction-filter').value;
    const ageRatingFilter = document.getElementById('age-rating-filter').value;
    const languageFilter = document.getElementById('language-filter').value;

    // Get platform filter
    const platformFilter = document.getElementById('platform-filter').value;

    // Get media type filter
    const mediaTypeFilter = document.getElementById('media-type-filter').value;

    // Filter standalone content
    filteredGroupedContent.standalone = groupedContent.standalone.filter(item => {
        return matchesFilters(item, searchTerm, typeFilter, restrictionFilter, ageRatingFilter, languageFilter, platformFilter, mediaTypeFilter);
    });

    // Filter series and their episodes
    filteredGroupedContent.series = groupedContent.series.map(series => {
        const filteredEpisodes = series.episodes.filter(episode => {
            return matchesFilters(episode, searchTerm, typeFilter, restrictionFilter, ageRatingFilter, languageFilter, platformFilter, mediaTypeFilter);
        });

        // Only include series if it has matching episodes
        if (filteredEpisodes.length === 0) {
            return null;
        }

        // Recalculate counts
        const newSeries = {
            ...series,
            episodes: filteredEpisodes,
            episode_count: filteredEpisodes.length,
            restricted_count: filteredEpisodes.filter(e => e.is_geo_restricted === true).length,
            accessible_count: filteredEpisodes.filter(e => e.is_geo_restricted === false).length,
            unknown_count: filteredEpisodes.filter(e => e.is_geo_restricted !== true && e.is_geo_restricted !== false).length
        };

        return newSeries;
    }).filter(series => series !== null);

    // Apply current sort
    if (currentSort.field) {
        sortContent(currentSort.field, currentSort.direction, false);
    }

    // Reset to first page after filtering
    currentPage = 1;

    renderTable();
    updateResultsCount();
}

// Check if item matches all filters
function matchesFilters(item, searchTerm, typeFilter, restrictionFilter, ageRatingFilter, languageFilter, platformFilter, mediaTypeFilter) {
    // Search filter
    if (searchTerm) {
        const searchableText = [
            item.title,
            item.description,
            item.series_title
        ].filter(Boolean).join(' ').toLowerCase();

        if (!searchableText.includes(searchTerm)) {
            return false;
        }
    }

    // Type filter
    if (typeFilter && item.type !== typeFilter) {
        return false;
    }

    // Restriction filter
    if (restrictionFilter !== '') {
        const isRestricted = item.is_geo_restricted;
        if (restrictionFilter === 'true' && !isRestricted) return false;
        if (restrictionFilter === 'false' && isRestricted !== false) return false;
        if (restrictionFilter === 'null' && isRestricted !== null) return false;
    }

    // Age rating filter
    if (ageRatingFilter && item.age_rating !== ageRatingFilter) {
        return false;
    }

    // Language filter
    if (languageFilter) {
        if (!item.languages || !Array.isArray(item.languages) || !item.languages.includes(languageFilter)) {
            return false;
        }
    }

    // Platform filter - check if platform array includes the filter value
    if (platformFilter) {
        let itemPlatforms = [];
        if (Array.isArray(item.platform)) {
            itemPlatforms = item.platform;
        } else if (typeof item.platform === 'string') {
            try {
                itemPlatforms = JSON.parse(item.platform);
                if (!Array.isArray(itemPlatforms)) {
                    itemPlatforms = [item.platform];
                }
            } catch {
                itemPlatforms = [item.platform];
            }
        }
        if (!itemPlatforms.includes(platformFilter)) {
            return false;
        }
    }

    // Media type filter (audio/video)
    if (mediaTypeFilter && item.media_type !== mediaTypeFilter) {
        return false;
    }

    return true;
}

// Sort content
function sortContent(field, direction = 'asc', updateUI = true) {
    // Sort standalone content
    filteredGroupedContent.standalone.sort((a, b) => {
        return compareValues(a[field], b[field], direction);
    });

    // Sort series
    filteredGroupedContent.series.sort((a, b) => {
        // For series, we might want to sort by series title or episode count
        if (field === 'title' || field === 'series_title') {
            return compareValues(a.series_title, b.series_title, direction);
        } else if (field === 'episode_count') {
            return compareValues(a.episode_count, b.episode_count, direction);
        } else {
            return compareValues(a.series_title, b.series_title, direction);
        }
    });

    // Sort episodes within each series
    filteredGroupedContent.series.forEach(series => {
        series.episodes.sort((a, b) => {
            return compareValues(a[field], b[field], direction);
        });
    });

    if (updateUI) {
        currentSort = { field, direction };
        updateSortIndicators();
        // Reset to first page on sort change
        currentPage = 1;
        renderTable();
        updateResultsCount();
    }
}

// Compare values for sorting
function compareValues(aVal, bVal, direction) {
    // Handle null/undefined
    if (aVal == null) aVal = '';
    if (bVal == null) bVal = '';

    // Handle numbers
    if (typeof aVal === 'number' && typeof bVal === 'number') {
        return direction === 'asc' ? aVal - bVal : bVal - aVal;
    }

    // Handle strings
    aVal = String(aVal).toLowerCase();
    bVal = String(bVal).toLowerCase();

    if (direction === 'asc') {
        return aVal.localeCompare(bVal);
    } else {
        return bVal.localeCompare(aVal);
    }
}

// Update sort indicators
function updateSortIndicators() {
    document.querySelectorAll('th').forEach(th => {
        th.removeAttribute('data-sort-direction');
        const indicator = th.querySelector('.sort-indicator');
        if (indicator) {
            indicator.textContent = '';
        }
    });

    if (currentSort.field) {
        const th = document.querySelector(`th[data-sort="${currentSort.field}"]`);
        if (th) {
            th.setAttribute('data-sort-direction', currentSort.direction);
        }
    }
}

// Toggle series expansion
function toggleSeriesExpansion(seriesSlug) {
    if (expandedSeries.has(seriesSlug)) {
        expandedSeries.delete(seriesSlug);
    } else {
        expandedSeries.add(seriesSlug);
    }
    renderTable();
}

// Render table
function renderTable() {
    const tbody = document.getElementById('content-tbody');

    const allRows = buildFlattenedRows();
    const totalRows = allRows.length;

    if (totalRows === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="loading">No content found matching filters.</td></tr>';
        renderPagination(1, 0, 0, 0);
        return;
    }

    const pageCount = getPageCount(totalRows);
    if (currentPage > pageCount) {
        currentPage = pageCount;
    }

    let startIndex = (currentPage - 1) * pageSize;
    let endIndex = startIndex + pageSize;

    if (startIndex >= totalRows) {
        startIndex = 0;
        endIndex = Math.min(pageSize, totalRows);
        currentPage = 1;
    }

    // Ensure we include the series header if the page would otherwise start in the middle of its episodes
    if (startIndex > 0 && allRows[startIndex].type === 'episode') {
        let i = startIndex - 1;
        while (i >= 0 && allRows[i].type !== 'series') {
            i--;
        }
        if (i >= 0) {
            startIndex = i;
        }
    }

    endIndex = Math.min(endIndex, totalRows);
    const pageRows = allRows.slice(startIndex, endIndex);

    let html = '';

    pageRows.forEach(row => {
        if (row.type === 'standalone') {
            const item = row.item;
            const isExpanded = expandedRows.has(item.slug);
            html += renderContentRow(item, false, isExpanded);
            if (isExpanded) {
                html += renderDetailRow(item, false);
            }
        } else if (row.type === 'series') {
            html += renderSeriesRow(row.series, row.isExpanded);
        } else if (row.type === 'episode') {
            const item = row.item;
            const isExpanded = expandedRows.has(item.slug);
            html += renderContentRow(item, true, isExpanded);
            if (isExpanded) {
                html += renderDetailRow(item, true);
            }
        }
    });

    tbody.innerHTML = html;

    // Re-attach event listeners for expand/collapse buttons
    document.querySelectorAll('.expand-toggle').forEach(button => {
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            const seriesSlug = button.getAttribute('data-series-slug');
            toggleSeriesExpansion(seriesSlug);
        });
    });

    // Add click handlers for series rows (mobile only)
    document.querySelectorAll('.series-row').forEach(rowEl => {
        rowEl.addEventListener('click', (e) => {
            // Don't trigger if clicking the expand button
            if (e.target.closest('.expand-toggle')) return;
            
            if (window.innerWidth <= 768) {
                // Mobile: Find series data and open series modal
                const expandBtn = rowEl.querySelector('.expand-toggle');
                const seriesSlug = expandBtn ? expandBtn.getAttribute('data-series-slug') : null;
                
                if (seriesSlug) {
                    const seriesData = pageRows.find(r => r.type === 'series' && r.series.series_slug === seriesSlug);
                    if (seriesData) {
                        openSeriesModal(seriesData.series);
                    }
                }
            }
        });
    });

    // Attach click handlers to data rows to toggle detail expansion
    document.querySelectorAll('tr[data-slug]').forEach(rowEl => {
        rowEl.addEventListener('click', () => {
            const slug = rowEl.getAttribute('data-slug');
            if (!slug) return;

            if (window.innerWidth <= 768) {
                // Mobile: Open Modal
                // Find item data from pageRows (which is in closure scope)
                let item = null;
                const rowData = pageRows.find(r => r.item && r.item.slug === slug);
                if (rowData) {
                    item = rowData.item;
                }

                if (item) {
                    openMobileDetail(item);
                }
                return; // Stop here, don't expand row
            }

            // Desktop: Expand/Collapse Row
            // Clicking an already expanded row collapses it.
            // Clicking a different row collapses any other and expands this one.
            if (expandedRows.has(slug)) {
                expandedRows.clear();
            } else {
                expandedRows.clear();
                expandedRows.add(slug);
            }

            renderTable();
        });
    });


    // Update pagination controls
    renderPagination(pageCount, totalRows, startIndex, endIndex);
}

// Helper function to render platform badges
function renderPlatformBadges(platforms) {
    if (!platforms || platforms.length === 0) {
        return '-';
    }

    const badges = platforms.map(platform => {
        // Extract platform name (e.g., "primeran.eus" -> "primeran")
        const platformName = platform.replace('.eus', '').toLowerCase();
        // Map to CSS class
        const badgeClass = `platform-badge-${platformName}`;
        // Display name (capitalize first letter)
        const displayName = platformName.charAt(0).toUpperCase() + platformName.slice(1);

        return `<span class="platform-badge ${badgeClass}">${escapeHtml(displayName)}</span>`;
    });

    return badges.join(' ');
}

// Render media type icon (audio/video) based on media_type field
function renderMediaTypeIcon(mediaType) {
    if (!mediaType) return '';
    const mt = String(mediaType).toLowerCase();
    if (mt === 'audio') {
        return `
            <span class="detail-media-type" title="Audio">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-label="Audio">
                    <path d="M2 13a2 2 0 0 0 2-2V7a2 2 0 0 1 4 0v13a2 2 0 0 0 4 0V4a2 2 0 0 1 4 0v13a2 2 0 0 0 4 0v-4a2 2 0 0 1 2-2"/>
                </svg>
            </span>
        `;
    }
    if (mt === 'video') {
        return `
            <span class="detail-media-type" title="Bideo">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-label="Bideo">
                    <path d="M20.2 6 3 11l-.9-2.4c-.3-1.1.3-2.2 1.3-2.5l13.5-4c1.1-.3 2.2.3 2.5 1.3Z"/>
                    <path d="m6.2 5.3 3.1 3.9"/>
                    <path d="m12.4 3.4 3.1 4"/>
                    <path d="M3 11h18v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>
                </svg>
            </span>
        `;
    }
    return '';
}

// Render series row
function renderSeriesRow(series, isExpanded) {
    const restrictedCount = series.restricted_count;
    const accessibleCount = series.accessible_count;
    const totalCount = series.episode_count;

    let restrictionSummary = '';
    if (restrictedCount > 0) {
        restrictionSummary += `<span class="status-badge status-restricted">${restrictedCount} Murriztua</span> `;
    }
    if (accessibleCount > 0) {
        restrictionSummary += `<span class="status-badge status-accessible">${accessibleCount} Murriztu gabea</span> `;
    }
    if (series.unknown_count > 0) {
        restrictionSummary += `<span class="status-badge status-unknown">${series.unknown_count} Ezezaguna</span>`;
    }

    // Get thumbnail from first episode if available
    let thumbnailHtml = '-';
    if (series.episodes && series.episodes.length > 0) {
        const firstEpisode = series.episodes[0];
        if (firstEpisode.thumbnail) {
            thumbnailHtml = `<img src="${escapeHtml(firstEpisode.thumbnail)}" alt="${escapeHtml(series.series_title)}" class="thumbnail-img" loading="lazy" onerror="this.style.display='none'">`;
        }
    }

    const expandIcon = isExpanded ? '▼' : '▶';

    // Get platform from first episode if available
    const firstEpisodePlatform = series.episodes && series.episodes.length > 0 ? series.episodes[0].platform : null;
    let platforms = [];
    if (firstEpisodePlatform) {
        if (Array.isArray(firstEpisodePlatform)) {
            platforms = firstEpisodePlatform;
        } else if (typeof firstEpisodePlatform === 'string') {
            try {
                const parsed = JSON.parse(firstEpisodePlatform);
                platforms = Array.isArray(parsed) ? parsed : [firstEpisodePlatform];
            } catch {
                platforms = [firstEpisodePlatform];
            }
        }
    }
    const platformDisplay = renderPlatformBadges(platforms);

    // IMPORTANT: Column order must match HTML header in index.html
    // 1. Empty (expand button), 2. Image, 3. Title, 4. Type, 5. Age, 6. Languages,
    // 7. Duration, 8. Year, 9. Geo-Restriction, 10. Platform (LAST)
    return `
        <tr class="series-row">
            <td>
                <button class="expand-toggle" data-series-slug="${escapeHtml(series.series_slug)}" aria-label="${isExpanded ? 'Collapse' : 'Expand'} series">
                    ${expandIcon}
                </button>
            </td>
            <td class="thumbnail-cell">${thumbnailHtml}</td>
            <td><strong>${escapeHtml(series.series_title)}</strong> <span class="series-episode-count">(${totalCount} atal)</span></td>
            <td>Series</td>
            <td>-</td>
            <td>-</td>
            <td>-</td>
            <td>-</td>
            <td>${restrictionSummary || '-'}</td>
            <td>${platformDisplay}</td>
        </tr>
    `;
}

// Render content row
function renderContentRow(item, isEpisode, isExpanded) {
    // Only show "Murriztua" or "Murriztu gabea", not "Ezezaguna"
    const restrictedStatus = item.is_geo_restricted === true ? 'Murriztua' :
        item.is_geo_restricted === false ? 'Murriztu gabea' : '-';
    const statusClass = item.is_geo_restricted === true ? 'status-restricted' :
        item.is_geo_restricted === false ? 'status-accessible' : '';

    const duration = item.duration ? formatDuration(item.duration) : '-';

    // Thumbnail
    let thumbnailHtml = '-';
    if (item.thumbnail) {
        thumbnailHtml = `<img src="${escapeHtml(item.thumbnail)}" alt="${escapeHtml(item.title || '')}" class="thumbnail-img" loading="lazy" onerror="this.style.display='none'">`;
    }

    // Title with link and tooltip
    // Handle null/undefined explicitly - JSON null becomes JavaScript null
    const title = (item.title != null && item.title !== '') ? item.title :
        (item.slug != null && item.slug !== '') ? item.slug :
            (item.series_title != null && item.series_title !== '') ? item.series_title : '-';

    // Debug: Log if title seems wrong
    if (item.slug && item.slug.includes('christmas') && title === 'vod') {
        console.error('Title issue detected:', { slug: item.slug, title: item.title, type: item.type, computedTitle: title });
    }


    let titleHtml = escapeHtml(title);
    // Removed direct link on title to ensure row click always triggers expansion.
    // Link is now available in the detail view.
    // Tooltip removed as per UX request.

    // Age rating badge
    let ageRatingHtml = '-';
    if (item.age_rating) {
        ageRatingHtml = `<span class="age-rating-badge">${escapeHtml(item.age_rating)}</span>`;
    }

    // Language badges
    let languagesHtml = '-';
    if (item.languages && Array.isArray(item.languages) && item.languages.length > 0) {
        languagesHtml = item.languages.map(lang =>
            `<span class="language-badge">${escapeHtml(lang.toUpperCase())}</span>`
        ).join(' ');
    }

    // Episode indicator
    const rowClass = isEpisode ? 'episode-row' : '';
    const indentStyle = isEpisode && isExpanded ? 'padding-left: 2rem;' : '';

    // Platform display - handle as array
    let itemPlatforms = [];
    if (item.platform !== undefined && item.platform !== null) {
        if (Array.isArray(item.platform)) {
            itemPlatforms = item.platform;
        } else if (typeof item.platform === 'string') {
            try {
                const parsed = JSON.parse(item.platform);
                itemPlatforms = Array.isArray(parsed) ? parsed : [item.platform];
            } catch {
                itemPlatforms = [item.platform];
            }
        }
    }

    // Ensure we have a valid array
    if (!Array.isArray(itemPlatforms)) {
        itemPlatforms = [];
    }

    const platformDisplay = renderPlatformBadges(itemPlatforms) || '-';

    // IMPORTANT: Column order must match HTML header in index.html
    // 1. Empty (expand button), 2. Image, 3. Title, 4. Type, 5. Age, 6. Languages,
    // 7. Duration, 8. Year, 9. Geo-Restriction, 10. Platform (LAST)
    return `
        <tr class="${rowClass}" style="${indentStyle}" data-slug="${escapeHtml(item.slug || '')}">
            <td></td>
            <td class="thumbnail-cell">${thumbnailHtml}</td>
            <td>${titleHtml}</td>
            <td>${escapeHtml(item.type || 'unknown')}</td>
            <td>${ageRatingHtml}</td>
            <td>${languagesHtml}</td>
            <td>${duration}</td>
            <td>${item.year || '-'}</td>
            <td>${restrictedStatus !== '-' ? `<span class="status-badge ${statusClass}">${restrictedStatus}</span>` : '-'}</td>
            <td>${platformDisplay}</td>
        </tr>
    `;
}

// Render detail row shown when a content row is expanded
function renderDetailRow(item, isEpisode) {
    const description = item.description || '';
    const hasDescription = description && description.trim().length > 0;

    // Large poster image (reuse thumbnail, but allow it to be bigger)
    let posterHtml = '';
    if (item.thumbnail) {
        posterHtml = `<img src="${escapeHtml(item.thumbnail)}" alt="${escapeHtml(item.title || '')}" class="detail-poster" loading="lazy" onerror="this.style.display='none'">`;
    }

    // Series / episode info
    let episodeInfo = '';
    if (isEpisode) {
        const parts = [];
        if (item.series_title) {
            parts.push(escapeHtml(item.series_title));
        }
        const se = [];
        // Prefer computed season_display; fallback to raw season_number; last resort infer from title
        let seasonDisplay = item.season_display;
        if (seasonDisplay == null && item.season_number != null) {
            seasonDisplay = item.season_number;
        }
        if (seasonDisplay == null) {
            const inferredSeason = inferSeasonFromTitle(item.title);
            if (inferredSeason != null) {
                seasonDisplay = inferredSeason;
            }
        }
        if (seasonDisplay != null) {
            se.push(`${escapeHtml(String(seasonDisplay))}. denboraldia`);
        }
        if (item.episode_number != null) {
            se.push(`${escapeHtml(String(item.episode_number))}. atala`);
        }
        if (se.length > 0) {
            parts.push(se.join(' · '));
        }
        if (parts.length > 0) {
            episodeInfo = `<div class="detail-meta-line detail-episode-info">${parts.join(' — ')}</div>`;
        }
    }

    // Meta info: year (kept separate above the inline meta row)
    const metaParts = [];
    if (item.year) metaParts.push(`${escapeHtml(String(item.year))}`);
    const metaLine = metaParts.length > 0
        ? `<div class="detail-meta-line">${metaParts.join(' · ')}</div>`
        : '';

    // Availability (date only)
    let availableText = '';
    if (item.available_until) {
        const availableDate = String(item.available_until).split('T')[0] || String(item.available_until);
        availableText = `Noiz arte: ${escapeHtml(availableDate)}`;
    }

    // Languages
    let languagesBadges = '';
    if (item.languages && Array.isArray(item.languages) && item.languages.length > 0) {
        languagesBadges = item.languages.map(lang =>
            `<span class="language-badge">${escapeHtml(lang.toUpperCase())}</span>`
        ).join(' ');
    }

    // Genres
    let genresHtml = '';
    if (item.genres && Array.isArray(item.genres) && item.genres.length > 0) {
        genresHtml = `<div class="detail-meta-line detail-genres">${item.genres.map(g => escapeHtml(g)).join(', ')}</div>`;
    }

    // Platforms (reuse platform badges)
    let itemPlatforms = [];
    if (item.platform !== undefined && item.platform !== null) {
        if (Array.isArray(item.platform)) {
            itemPlatforms = item.platform;
        } else if (typeof item.platform === 'string') {
            try {
                const parsed = JSON.parse(item.platform);
                itemPlatforms = Array.isArray(parsed) ? parsed : [item.platform];
            } catch {
                itemPlatforms = [item.platform];
            }
        }
    }
    if (!Array.isArray(itemPlatforms)) {
        itemPlatforms = [];
    }
    const platformDisplay = renderPlatformBadges(itemPlatforms) || '-';

    // Content URL (explicit link if available)
    let linkHtml = '';
    if (item.content_url) {
        const linkTitle = (item.title != null && item.title !== '') ? item.title :
            (item.slug != null && item.slug !== '') ? item.slug : '';
        linkHtml = `
            <div class="detail-meta-line">
                <a href="${escapeHtml(item.content_url)}" target="_blank" class="content-link" onclick="event.stopPropagation();" title="${escapeHtml(linkTitle)}">
                    Ireki edukia platforman <span class="external-link-icon">↗</span>
                </a>
            </div>
        `;
    }

    // Combined inline meta row: duration, age badge, media type icon, languages, platforms, availability (Noiz arte last)
    const inlineParts = [];
    if (item.duration) inlineParts.push(formatDuration(item.duration));
    if (item.age_rating) inlineParts.push(`<span class="age-rating-badge">${escapeHtml(item.age_rating)}</span>`);
    const mediaTypeIcon = item.media_type ? renderMediaTypeIcon(item.media_type) : '';
    if (mediaTypeIcon) inlineParts.push(mediaTypeIcon);
    if (languagesBadges) inlineParts.push(languagesBadges);
    if (platformDisplay) inlineParts.push(platformDisplay);
    if (availableText) inlineParts.push(availableText);
    const inlineMeta = inlineParts.length > 0
        ? `<div class="detail-meta-line detail-meta-inline">${inlineParts.join(' ')}</div>`
        : '';

    const descriptionHtml = hasDescription
        ? `<p class="detail-description">${escapeHtml(description)}</p>`
        : '';

    return `
        <tr class="detail-row">
            <td colspan="10">
                <div class="detail-container">
                    ${posterHtml ? `<div class="detail-poster-wrapper">${posterHtml}</div>` : ''}
                    <div class="detail-content">
                        ${episodeInfo}
                        ${metaLine}
                        ${inlineMeta}
                        ${genresHtml}
                        ${linkHtml}
                        ${descriptionHtml}
                    </div>
                </div>
            </td>
        </tr>
    `;
}

// Format duration (seconds to HH:MM:SS)
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

// Escape HTML
function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Update results count
function updateResultsCount() {
    const standaloneCount = filteredGroupedContent.standalone.length;
    const episodeCount = filteredGroupedContent.series.reduce((sum, s) => sum + s.episode_count, 0);
    const seriesCount = filteredGroupedContent.series.length;
    const totalCount = standaloneCount + episodeCount;

    const totalRows = getTotalRows();
    const pageCount = getPageCount(totalRows);
    const countText = `${totalCount.toLocaleString()} elementu (${standaloneCount} filma, ${seriesCount} serie, ${episodeCount} atalekin) — Orrialdea ${currentPage} / ${pageCount}`;
    document.getElementById('results-count').textContent = countText;

    // Mobile results count
    const mobileCountEl = document.getElementById('mobile-results-count');
    if (mobileCountEl) {
        mobileCountEl.textContent = totalCount.toLocaleString();
    }
}

// Render pagination controls
function renderPagination(pageCount, totalRows, startIndex, endIndex) {
    const pageInfoEl = document.getElementById('page-info');
    const firstBtn = document.getElementById('first-page');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const lastBtn = document.getElementById('last-page');
    const pageSizeSelect = document.getElementById('page-size');

    if (pageSizeSelect) {
        if (!pageSizeSelect.value) {
            pageSizeSelect.value = String(pageSize);
        }
    }

    if (pageInfoEl) {
        if (totalRows === 0) {
            pageInfoEl.textContent = 'No rows';
        } else {
            const from = startIndex + 1;
            const to = endIndex;
            pageInfoEl.textContent = `Page ${currentPage} of ${pageCount} · Rows ${from}-${to} of ${totalRows}`;
        }
    }

    const atFirstPage = currentPage <= 1;
    const atLastPage = currentPage >= pageCount;

    if (firstBtn) firstBtn.disabled = atFirstPage;
    if (prevBtn) prevBtn.disabled = atFirstPage;
    if (nextBtn) nextBtn.disabled = atLastPage;
    if (lastBtn) lastBtn.disabled = atLastPage;
}

// Clear filters
function clearFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('type-filter').value = '';
    document.getElementById('restriction-filter').value = '';
    document.getElementById('age-rating-filter').value = '';
    document.getElementById('language-filter').value = '';
    document.getElementById('platform-filter').value = '';
    document.getElementById('media-type-filter').value = '';
    currentPage = 1;
    applyFilters();
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    initMobileNavigation();
    loadContent();

    // Filter inputs
    document.getElementById('search-input').addEventListener('input', applyFilters);
    document.getElementById('type-filter').addEventListener('change', applyFilters);
    document.getElementById('restriction-filter').addEventListener('change', applyFilters);
    document.getElementById('age-rating-filter').addEventListener('change', applyFilters);
    document.getElementById('language-filter').addEventListener('change', applyFilters);
    document.getElementById('platform-filter').addEventListener('change', applyFilters);
    document.getElementById('media-type-filter').addEventListener('change', applyFilters);
    document.getElementById('clear-filters').addEventListener('click', clearFilters);

    // Pagination controls
    const pageSizeSelect = document.getElementById('page-size');
    if (pageSizeSelect) {
        pageSizeSelect.value = String(pageSize);
        pageSizeSelect.addEventListener('change', (event) => {
            changePageSize(event.target.value);
        });
    }

    const firstBtn = document.getElementById('first-page');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const lastBtn = document.getElementById('last-page');

    if (firstBtn) firstBtn.addEventListener('click', () => goToPage(1));
    if (prevBtn) prevBtn.addEventListener('click', () => goToPage(currentPage - 1));
    if (nextBtn) nextBtn.addEventListener('click', () => goToPage(currentPage + 1));
    if (lastBtn) lastBtn.addEventListener('click', () => {
        const totalRows = getTotalRows();
        goToPage(getPageCount(totalRows));
    });

    // Sort headers
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', () => {
            const field = th.getAttribute('data-sort');
            const currentDirection = currentSort.field === field ? currentSort.direction : 'asc';
            const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
            sortContent(field, newDirection);
        });
    });
});

// ------------------------------------------------------------------------
// Mobile Navigation Logic
// ------------------------------------------------------------------------

// Get a flat list of all currently navigable items (respecting filters/sort)
// Order: All Standalone -> All Series Episodes (flattened)
function getNavigableItems() {
    const items = [];

    // 1. Add all standalone items
    filteredGroupedContent.standalone.forEach(item => items.push(item));

    // 2. Add all episodes from all filtered series
    filteredGroupedContent.series.forEach(series => {
        if (series.episodes) {
            series.episodes.forEach(ep => items.push(ep));
        }
    });

    return items;
}

// Find index of current item in the navigable list
function findItemIndex(item, items) {
    if (!item || !items) return -1;
    // Match by slug (primary) or fall back to strict equality
    return items.findIndex(i => i.slug === item.slug);
}

// Show navigation arrows and reset auto-hide timer
function showNavButtons() {
    const prevBtn = document.getElementById('mobile-nav-prev');
    const nextBtn = document.getElementById('mobile-nav-next');

    if (prevBtn) prevBtn.classList.remove('nav-hidden');
    if (nextBtn) nextBtn.classList.remove('nav-hidden');

    // Reset timer
    resetNavHideTimer();
}

// Hide navigation arrows
function hideNavButtons() {
    const prevBtn = document.getElementById('mobile-nav-prev');
    const nextBtn = document.getElementById('mobile-nav-next');

    if (prevBtn) prevBtn.classList.add('nav-hidden');
    if (nextBtn) nextBtn.classList.add('nav-hidden');
}

// Reset the auto-hide timer for navigation arrows
function resetNavHideTimer() {
    // Clear existing timer
    if (navHideTimer) {
        clearTimeout(navHideTimer);
    }

    // Set new timer to hide arrows after delay
    navHideTimer = setTimeout(() => {
        hideNavButtons();
    }, NAV_HIDE_DELAY);
}

// Cancel the auto-hide timer (e.g., when modal is closed)
function cancelNavHideTimer() {
    if (navHideTimer) {
        clearTimeout(navHideTimer);
        navHideTimer = null;
    }
}

// Lock body scroll (save position and apply fixed positioning)
function lockBodyScroll() {
    scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
    document.body.style.top = `-${scrollPosition}px`;
    document.body.classList.add('modal-open');
}

// Unlock body scroll (restore position and remove fixed positioning)
function unlockBodyScroll() {
    document.body.classList.remove('modal-open');
    document.body.style.top = '';
    window.scrollTo(0, scrollPosition);
}

function updateNavButtons() {
    const prevBtn = document.getElementById('mobile-nav-prev');
    const nextBtn = document.getElementById('mobile-nav-next');

    if (!prevBtn || !nextBtn) return;

    const { index, items } = currentDetailValues;

    if (index <= 0) {
        prevBtn.disabled = true;
    } else {
        prevBtn.disabled = false;
    }

    if (index >= items.length - 1 || index === -1) {
        nextBtn.disabled = true;
    } else {
        nextBtn.disabled = false;
    }
}

function navigateItem(direction) {
    const { index, items } = currentDetailValues;
    if (index === -1 || !items.length) return;

    let newIndex = index + direction;

    // Bounds check
    if (newIndex < 0) newIndex = 0;
    if (newIndex >= items.length) newIndex = items.length - 1;

    if (newIndex !== index) {
        const newItem = items[newIndex];
        openMobileDetail(newItem);
        // Show arrows when user actively navigates
        showNavButtons();
    }
}

// Initialize Navigation Listeners
function initMobileNavigation() {
    const prevBtn = document.getElementById('mobile-nav-prev');
    const nextBtn = document.getElementById('mobile-nav-next');
    const modal = document.getElementById('mobile-detail-modal');
    const closeBtn = document.getElementById('mobile-detail-close');

    if (prevBtn) {
        // Clone to remove old listeners if any (simple way to ensure no duplicates)
        const newPrev = prevBtn.cloneNode(true);
        prevBtn.parentNode.replaceChild(newPrev, prevBtn);
        newPrev.addEventListener('click', (e) => {
            e.stopPropagation();
            navigateItem(-1);
        });
    }

    if (nextBtn) {
        const newNext = nextBtn.cloneNode(true);
        nextBtn.parentNode.replaceChild(newNext, nextBtn);
        newNext.addEventListener('click', (e) => {
            e.stopPropagation();
            navigateItem(1);
        });
    }

    if (closeBtn) {
        // Ensure close button works (re-adding just in case)
        closeBtn.addEventListener('click', closeMobileDetail);
    }

    // Swipe Gestures and Touch Interaction
    if (modal) {
        // Remove old listeners? Hard to do without reference. 
        // We'll rely on this running once on DOMContentLoaded or check a flag.
        if (!modal.hasAttribute('data-swipe-init')) {
            modal.addEventListener('touchstart', (e) => {
                touchStartX = e.changedTouches[0].screenX;
                // Show arrows on any touch
                showNavButtons();
            }, { passive: true });

            modal.addEventListener('touchend', (e) => {
                touchEndX = e.changedTouches[0].screenX;
                handleSwipe();
            }, { passive: true });

            // Show arrows on tap/click anywhere in modal
            modal.addEventListener('click', (e) => {
                // Don't trigger if clicking on buttons or links
                if (!e.target.closest('button') && !e.target.closest('a')) {
                    showNavButtons();
                }
            });

            modal.setAttribute('data-swipe-init', 'true');
        }
    }
}

function handleSwipe() {
    const threshold = 50; // min distance to be considered a swipe
    const diff = touchStartX - touchEndX;

    if (Math.abs(diff) > threshold) {
        if (diff > 0) {
            // Swiped Left -> Show Next
            navigateItem(1);
        } else {
            // Swiped Right -> Show Previous
            navigateItem(-1);
        }
    }
}

// Mobile Detail Modal Functions
function openMobileDetail(item) {
    const modal = document.getElementById('mobile-detail-modal');
    if (!modal) return;

    // Update Navigation State
    // Check if we're coming from a series modal
    const isFromSeries = currentDetailValues?.isSeries;
    const seriesEpisodes = isFromSeries ? currentDetailValues.items : null;
    
    let items, index;
    if (seriesEpisodes) {
        // Navigate within series episodes only
        items = seriesEpisodes;
        index = findItemIndex(item, items);
    } else {
        // Navigate through all items
        items = getNavigableItems();
        index = findItemIndex(item, items);
    }

    currentDetailValues = { index, items, isSeries: false };
    updateNavButtons();

    // Remove series-specific class if present
    const descriptionEl = document.getElementById('mobile-detail-description');
    descriptionEl.classList.remove('series-episode-list');

    // Populate Content
    const poster = document.getElementById('mobile-detail-poster');
    poster.src = item.thumbnail || '';
    poster.style.display = item.thumbnail ? 'block' : 'none';

    document.getElementById('mobile-detail-title').textContent =
        (item.title != null && item.title !== '') ? item.title :
            (item.series_title != null && item.series_title !== '') ? item.series_title :
                (item.slug || 'Izenbururik gabe');

    descriptionEl.textContent = item.description || 'Ez dago deskribapenik eskuragarri.';

    // Meta (Year, Duration, Age)
    const metaContainer = document.getElementById('mobile-detail-meta');
    metaContainer.innerHTML = '';

    if (item.year) metaContainer.innerHTML += `<span>${item.year}</span> • `;
    // Check if formatDuration is available globally or needs to be copied/exposed. It is global in content.js
    if (item.duration) metaContainer.innerHTML += `<span>${formatDuration(item.duration)}</span> • `;
    if (item.age_rating) metaContainer.innerHTML += `<span class="age-rating-badge">${item.age_rating}</span>`;

    // Badges (Platform, Geo)
    const badgesContainer = document.getElementById('mobile-detail-badges');
    badgesContainer.innerHTML = '';

    // Platform
    let platforms = [];
    if (item.platform) {
        try {
            platforms = Array.isArray(item.platform) ? item.platform : JSON.parse(item.platform);
        } catch {
            platforms = [item.platform];
        }
    }
    if (!Array.isArray(platforms)) platforms = [platforms];

    // renderPlatformBadges is defined in content.js
    const platformHtml = renderPlatformBadges(platforms);
    if (platformHtml) badgesContainer.innerHTML += platformHtml;

    // Geo
    if (item.is_geo_restricted === true) {
        badgesContainer.innerHTML += `<span class="status-badge status-restricted">Geo-Murriztua</span>`;
    }

    // Link
    const linkBtn = document.getElementById('mobile-detail-link');
    if (item.content_url) {
        linkBtn.href = item.content_url;
        linkBtn.style.display = 'flex';
    } else {
        linkBtn.style.display = 'none';
    }

    // Show Modal
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    lockBodyScroll();
    // Lock body scroll with position saving

    // Start auto-hide timer for navigation arrows
    showNavButtons();
}

// Open series modal showing episode list
function openSeriesModal(series) {
    const modal = document.getElementById('mobile-detail-modal');
    if (!modal) return;

    // Store series context for navigation
    currentDetailValues = { 
        index: -1, 
        items: series.episodes,
        isSeries: true,
        seriesData: series
    };
    
    // Get poster from first episode
    const poster = document.getElementById('mobile-detail-poster');
    const firstEpisode = series.episodes[0];
    poster.src = firstEpisode?.thumbnail || '';
    poster.style.display = firstEpisode?.thumbnail ? 'block' : 'none';

    // Set series title
    document.getElementById('mobile-detail-title').textContent = series.series_title;

    // Set meta info (episode count, platform)
    const metaContainer = document.getElementById('mobile-detail-meta');
    metaContainer.innerHTML = `<span>${series.episode_count} atal</span>`;

    // Platform badges
    const badgesContainer = document.getElementById('mobile-detail-badges');
    let platforms = [];
    if (firstEpisode?.platform) {
        platforms = Array.isArray(firstEpisode.platform) ? firstEpisode.platform : [firstEpisode.platform];
    }
    badgesContainer.innerHTML = renderPlatformBadges(platforms);

    // Build episode list instead of description
    const descriptionEl = document.getElementById('mobile-detail-description');
    descriptionEl.innerHTML = renderEpisodeList(series.episodes);
    descriptionEl.classList.add('series-episode-list');

    // Attach click handlers to episode list items (using event delegation)
    descriptionEl.addEventListener('click', (e) => {
        const episodeItem = e.target.closest('.episode-list-item');
        if (episodeItem) {
            const episodeIndex = parseInt(episodeItem.getAttribute('data-episode-index'));
            const episode = series.episodes[episodeIndex];
            if (episode) {
                // Transition to episode detail modal
                openMobileDetail(episode);
            }
        }
    }, { once: false }); // Don't use once, we might reopen

    // Hide the platform link button for series
    const linkBtn = document.getElementById('mobile-detail-link');
    linkBtn.style.display = 'none';

    // Hide navigation arrows for series view
    hideNavButtons();

    // Show modal
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    lockBodyScroll();
}

// Render episode list for series modal
function renderEpisodeList(episodes) {
    if (!episodes || episodes.length === 0) {
        return '<p class="no-episodes">Ez dago atalik eskuragarri.</p>';
    }

    let html = '<div class="episode-list-container">';
    
    episodes.forEach((episode, index) => {
        // Season/Episode info
        let episodeLabel = '';
        if (episode.season_display || episode.season_number) {
            episodeLabel += `D${episode.season_display || episode.season_number}`;
        }
        if (episode.episode_number) {
            episodeLabel += `:${episode.episode_number}`;
        }
        
        // Duration
        const duration = episode.duration ? formatDuration(episode.duration) : '';
        
        // Thumbnail
        const thumbnail = episode.thumbnail || '';
        
        // Title
        const title = episode.title || episode.slug || 'Izen gabea';
        
        // Geo restriction badge
        let restrictionBadge = '';
        if (episode.is_geo_restricted === true) {
            restrictionBadge = '<span class="episode-geo-badge restricted">🔒</span>';
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
    
    html += '</div>';
    return html;
}

function closeMobileDetail() {
    const modal = document.getElementById('mobile-detail-modal');
    if (!modal) return;

    // Check if we should return to series modal
    const wasInSeriesContext = currentDetailValues?.items && 
                               currentDetailValues.items.length > 0 &&
                               currentDetailValues.items[0]?.series_slug;
    
    if (wasInSeriesContext) {
        // Find parent series and reopen series modal
        const seriesSlug = currentDetailValues.items[0].series_slug;
        const series = filteredGroupedContent.series.find(s => s.series_slug === seriesSlug);
        if (series) {
            openSeriesModal(series);
            return;
        }
    }

    // Default close behavior
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    unlockBodyScroll();
    // Unlock body scroll and restore position

    // Cancel auto-hide timer when modal closes
    cancelNavHideTimer();
}

// Initialize Mobile Modal Listeners
document.addEventListener('DOMContentLoaded', () => {
    const closeBtn = document.getElementById('mobile-detail-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeMobileDetail);
    }
});
