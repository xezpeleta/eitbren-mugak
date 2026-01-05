// Content List JavaScript
let allContent = [];
let groupedContent = { series: [], standalone: [] };
let filteredGroupedContent = { series: [], standalone: [] };
let expandedSeries = new Set();
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
            '<tr><td colspan="11" style="color: red;">Error loading content. Please ensure data/content.json exists.</td></tr>';
    }
}

// Group content by series
function groupContentBySeries() {
    const episodes = [];
    const standalone = [];
    const seriesMap = new Map();
    
    // Separate episodes from standalone content
    allContent.forEach(item => {
        if (item.type === 'episode' && item.series_slug) {
            episodes.push(item);
        } else {
            standalone.push(item);
        }
    });
    
    // Group episodes by series
    episodes.forEach(episode => {
        const seriesSlug = episode.series_slug;
        if (!seriesMap.has(seriesSlug)) {
            seriesMap.set(seriesSlug, {
                series_slug: seriesSlug,
                series_title: episode.series_title || seriesSlug,
                episodes: [],
                episode_count: 0,
                restricted_count: 0,
                accessible_count: 0,
                unknown_count: 0,
                is_expanded: false
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
    
    groupedContent = {
        series: Array.from(seriesMap.values()),
        standalone: standalone
    };
}

// Populate all filter dropdowns
function populateFilters() {
    populateTypeFilter();
    populateAgeRatingFilter();
    populateLanguageFilter();
    populatePlatformFilter();
}

// Populate type filter dropdown
function populateTypeFilter() {
    const typeFilter = document.getElementById('type-filter');
    const types = [...new Set(allContent.map(item => item.type).filter(Boolean))].sort();
    
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
    const platforms = [...new Set(allContent.map(item => item.platform).filter(Boolean))].sort();
    
    platforms.forEach(platform => {
        const option = document.createElement('option');
        option.value = platform;
        // Display name: extract domain name (e.g., "makusi.eus" -> "Makusi")
        const displayName = platform.replace('.eus', '').replace('.', ' ').replace(/\b\w/g, l => l.toUpperCase());
        option.textContent = displayName;
        platformFilter.appendChild(option);
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
    
    // Filter standalone content
    filteredGroupedContent.standalone = groupedContent.standalone.filter(item => {
        return matchesFilters(item, searchTerm, typeFilter, restrictionFilter, ageRatingFilter, languageFilter, platformFilter);
    });
    
    // Filter series and their episodes
    filteredGroupedContent.series = groupedContent.series.map(series => {
        const filteredEpisodes = series.episodes.filter(episode => {
            return matchesFilters(episode, searchTerm, typeFilter, restrictionFilter, ageRatingFilter, languageFilter, platformFilter);
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
function matchesFilters(item, searchTerm, typeFilter, restrictionFilter, ageRatingFilter, languageFilter) {
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
        tbody.innerHTML = '<tr><td colspan="11" class="loading">No content found matching filters.</td></tr>';
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
            html += renderContentRow(row.item, false, false);
        } else if (row.type === 'series') {
            html += renderSeriesRow(row.series, row.isExpanded);
        } else if (row.type === 'episode') {
            html += renderContentRow(row.item, true, row.isExpanded);
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

    // Update pagination controls
    renderPagination(pageCount, totalRows, startIndex, endIndex);
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
    const platform = series.episodes && series.episodes.length > 0 ? series.episodes[0].platform : '-';
    const platformDisplay = platform !== '-' ? platform.replace('.eus', '').replace('.', ' ').replace(/\b\w/g, l => l.toUpperCase()) : '-';
    
    return `
        <tr class="series-row">
            <td>
                <button class="expand-toggle" data-series-slug="${escapeHtml(series.series_slug)}" aria-label="${isExpanded ? 'Collapse' : 'Expand'} series">
                    ${expandIcon}
                </button>
            </td>
            <td class="thumbnail-cell">${thumbnailHtml}</td>
            <td>${escapeHtml(platformDisplay)}</td>
            <td><strong>${escapeHtml(series.series_title)}</strong> <span class="series-episode-count">(${totalCount} atal)</span></td>
            <td>Series</td>
            <td>-</td>
            <td>-</td>
            <td>-</td>
            <td>-</td>
            <td>${restrictionSummary || '-'}</td>
            <td>-</td>
        </tr>
    `;
}

// Render content row
function renderContentRow(item, isEpisode, isExpanded) {
    const restrictedStatus = item.is_geo_restricted === true ? 'Murriztua' :
                            item.is_geo_restricted === false ? 'Murriztu-gabea' : 'Ezezaguna';
    const statusClass = item.is_geo_restricted === true ? 'status-restricted' :
                       item.is_geo_restricted === false ? 'status-accessible' : 'status-unknown';
    
    const duration = item.duration ? formatDuration(item.duration) : '-';
    
    // Thumbnail
    let thumbnailHtml = '-';
    if (item.thumbnail) {
        thumbnailHtml = `<img src="${escapeHtml(item.thumbnail)}" alt="${escapeHtml(item.title || '')}" class="thumbnail-img" loading="lazy" onerror="this.style.display='none'">`;
    }
    
    // Title with link and tooltip
    let titleHtml = escapeHtml(item.title || item.slug);
    if (item.content_url) {
        titleHtml = `<a href="${escapeHtml(item.content_url)}" target="_blank" class="content-link" title="${escapeHtml(item.description || item.title || '')}">${titleHtml} <span class="external-link-icon">↗</span></a>`;
    } else if (item.description) {
        titleHtml = `<span class="content-title-tooltip" title="${escapeHtml(item.description)}">${titleHtml}</span>`;
    }
    
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
    
    // Platform display
    const platform = item.platform || '-';
    const platformDisplay = platform !== '-' ? platform.replace('.eus', '').replace('.', ' ').replace(/\b\w/g, l => l.toUpperCase()) : '-';
    
    return `
        <tr class="${rowClass}" style="${indentStyle}">
            <td></td>
            <td class="thumbnail-cell">${thumbnailHtml}</td>
            <td>${escapeHtml(platformDisplay)}</td>
            <td>${titleHtml}</td>
            <td>${escapeHtml(item.type || 'unknown')}</td>
            <td>${ageRatingHtml}</td>
            <td>${languagesHtml}</td>
            <td>${duration}</td>
            <td>${item.year || '-'}</td>
            <td><span class="status-badge ${statusClass}">${restrictedStatus}</span></td>
            <td>${escapeHtml(item.restriction_type || '-')}</td>
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
    currentPage = 1;
    applyFilters();
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadContent();
    
    // Filter inputs
    document.getElementById('search-input').addEventListener('input', applyFilters);
    document.getElementById('type-filter').addEventListener('change', applyFilters);
    document.getElementById('restriction-filter').addEventListener('change', applyFilters);
    document.getElementById('age-rating-filter').addEventListener('change', applyFilters);
    document.getElementById('language-filter').addEventListener('change', applyFilters);
    document.getElementById('platform-filter').addEventListener('change', applyFilters);
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
