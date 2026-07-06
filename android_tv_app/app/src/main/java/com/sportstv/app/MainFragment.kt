package com.sportstv.app

import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.leanback.app.BrowseSupportFragment
import androidx.leanback.widget.*
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import com.sportstv.app.model.*

/**
 * MainFragment – the home screen of the TV app.
 *
 * Shows a horizontal row of stream cards for each sport category,
 * Netflix-style. Data is fetched from the Python backend.
 */
class MainFragment : BrowseSupportFragment() {

    private val rowsAdapter = ArrayObjectAdapter(ListRowPresenter())

    private fun getFavoritesSet(): MutableSet<String> {
        val prefs = requireContext().getSharedPreferences("SportsTVPrefs", android.content.Context.MODE_PRIVATE)
        return prefs.getStringSet("favorites", mutableSetOf()) ?: mutableSetOf()
    }

    private fun toggleFavorite(streamId: String) {
        val prefs = requireContext().getSharedPreferences("SportsTVPrefs", android.content.Context.MODE_PRIVATE)
        val favs = getFavoritesSet().toMutableSet()
        if (favs.contains(streamId)) {
            favs.remove(streamId)
        } else {
            favs.add(streamId)
        }
        prefs.edit().putStringSet("favorites", favs).apply()
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // ── Branding ─────────────────────────────────────────────────────────
        title          = "Sports TV"
        headersState   = HEADERS_ENABLED
        isHeadersTransitionOnBackEnabled = true
        brandColor     = requireContext().getColor(R.color.brand_color)
        badgeDrawable  = null
        searchAffordanceColor = requireContext().getColor(R.color.brand_color)

        // ── Search Orb → Launch SearchActivity ──────────────────────────────
        setOnSearchClickedListener {
            val intent = android.content.Intent(requireContext(), SearchActivity::class.java)
            startActivity(intent)
        }

        adapter = rowsAdapter

        // ── Item click → open player ──────────────────────────────────────────
        onItemViewClickedListener = OnItemViewClickedListener { _, item, _, _ ->
            val stream = item as StreamItem
            if (stream.hlsUrl == "system://update") {
                lifecycleScope.launch {
                    Toast.makeText(requireContext(), "Checking for updates...", Toast.LENGTH_SHORT).show()
                    UpdateChecker.checkForUpdate(requireActivity(), showToastIfLatest = true)
                }
            } else if (stream.hlsUrl == "system://refresh") {
                Toast.makeText(requireContext(), "Refreshing streams...", Toast.LENGTH_SHORT).show()
                loadStreams()
            } else {
                PlaybackActivity.start(requireContext(), stream)
            }
        }
        
        // ── Long click → toggle favorite ─────────────────────────────────────
        onItemViewSelectedListener = OnItemViewSelectedListener { _, _, _, _ -> }
        // Leanback doesn't natively support long click nicely through OnItemViewLongClickedListener unless we set it on the row or implement a custom listener
        // We will just use the standard View.OnLongClickListener in CardPresenter... wait, Leanback has setOnItemViewLongClickedListener.
        // Actually it doesn't. We'll set the listener on the ViewHolder view in CardPresenter... wait, easier: OnItemViewClickedListener for short click.
        // Since we can't easily add long click on BrowseSupportFragment without custom rows, we can just intercept KeyEvents or let's use setOnItemViewClickedListener and wait.
        // Actually, leanback RowPresenter.ViewHolder has setOnItemViewClickedListener. BrowseSupportFragment doesn't have LongClick.
        // Let's modify CardPresenter to add the long click listener directly to the view.
        
        loadStreams()
    }

    override fun onResume() {
        super.onResume()
        loadStreams()
    }

    private fun loadStreams() {
        lifecycleScope.launch {
            try {
                val streams = ApiClient.service.getStreams(liveOnly = false)
                val favs = getFavoritesSet()

                // Fetch SportSRC matches
                val sportSrcStreams = try {
                    ApiClient.service.getSportSrcMatches().map { match ->
                        val encodedTitle = java.net.URLEncoder.encode(match.title, "UTF-8")
                        val thumb = if (!match.thumbnail.isNullOrBlank()) match.thumbnail else "https://placehold.co/400x225/1e293b/14b8a6.png?text=$encodedTitle"
                        // Parse date and calculate time remaining if upcoming
                        var subtitle = match.title
                        var isLive = match.status != "upcoming"
                        if (!isLive && match.date.isNotBlank()) {
                            try {
                                val matchTime = match.date.toLong()
                                val diff = matchTime - System.currentTimeMillis()
                                if (diff > 0) {
                                    val hours = diff / (1000 * 60 * 60)
                                    val minutes = (diff / (1000 * 60)) % 60
                                    subtitle = if (hours > 0) "Starts in ${hours}h ${minutes}m" else "Starts in ${minutes}m"
                                } else {
                                    isLive = true
                                }
                            } catch (e: Exception) { }
                        }
                        
                        val sportCap = match.sport.replaceFirstChar { if (it.isLowerCase()) it.titlecase(java.util.Locale.getDefault()) else it.toString() }
                        val catName = if (isLive) "🏆 Live $sportCap" else "📅 Upcoming $sportCap"
                        
                        StreamItem(
                            id = match.id.hashCode(),
                            categoryId = -1,
                            categoryName = catName,
                            categoryIcon = if (isLive) "🔴" else "📅",
                            title = match.title,
                            participants = subtitle,
                            sport = match.sport,
                            hlsUrl = "sportsrc://${match.id}",
                            thumbnailUrl = thumb,
                            isLive = isLive
                        )
                    }
                } catch (e: Exception) {
                    emptyList()
                }

                // Separate Live vs Upcoming and add SportSRC streams
                val combinedStreams = streams + sportSrcStreams
                val liveStreams = combinedStreams.filter { it.isLive }
                val upcomingStreams = combinedStreams.filter { !it.isLive }
                
                // Extract favorites
                val favoriteStreams = streams.filter { favs.contains(it.id.toString()) }

                rowsAdapter.clear()
                
                // 1. Featured Top Live Row
                val topLive = liveStreams.firstOrNull()
                if (topLive != null) {
                    val cardPresenter = CardPresenter(favs) { streamId -> onToggleFavorite(streamId) }
                    val listRowAdapter = ArrayObjectAdapter(cardPresenter)
                    listRowAdapter.add(topLive)
                    rowsAdapter.add(ListRow(HeaderItem("🔥 Top Live Match"), listRowAdapter))
                }
                
                // 2. Favorites Row
                if (favoriteStreams.isNotEmpty()) {
                    val cardPresenter = CardPresenter(favs) { streamId -> onToggleFavorite(streamId) }
                    val listRowAdapter = ArrayObjectAdapter(cardPresenter)
                    favoriteStreams.forEach { listRowAdapter.add(it) }
                    rowsAdapter.add(ListRow(HeaderItem("⭐ Favorites"), listRowAdapter))
                }

                // 3. Live Categories (excluding Top Live)
                val remainingLive = if (topLive != null) liveStreams.filter { it.id != topLive.id } else liveStreams
                val grouped = remainingLive.groupBy { it.sport.replaceFirstChar { c -> c.uppercase() } }
                grouped.forEach { (sportName, categoryStreams) ->
                    val cardPresenter = CardPresenter(favs) { streamId -> onToggleFavorite(streamId) }
                    val listRowAdapter = ArrayObjectAdapter(cardPresenter)
                    categoryStreams.forEach { listRowAdapter.add(it) }

                    val headerItem = HeaderItem("🔴 Live $sportName")
                    rowsAdapter.add(ListRow(headerItem, listRowAdapter))
                }
                
                // 4. Upcoming Categories
                val upcomingGrouped = upcomingStreams.groupBy { it.sport.replaceFirstChar { c -> c.uppercase() } }
                upcomingGrouped.forEach { (sportName, categoryStreams) ->
                    val cardPresenter = CardPresenter(favs) { streamId -> onToggleFavorite(streamId) }
                    val listRowAdapter = ArrayObjectAdapter(cardPresenter)
                    categoryStreams.forEach { listRowAdapter.add(it) }

                    val headerItem = HeaderItem("📅 Upcoming $sportName")
                    rowsAdapter.add(ListRow(headerItem, listRowAdapter))
                }

                // 4. Update Check Row
                val updateCardPresenter = CardPresenter(favs) { }
                val updateRowAdapter = ArrayObjectAdapter(updateCardPresenter)
                updateRowAdapter.add(
                    StreamItem(
                        id = 999998,
                        categoryId = -2,
                        categoryName = "System",
                        categoryIcon = "🔄",
                        title = "Refresh Streams",
                        participants = "Reload the latest streams",
                        sport = "System",
                        hlsUrl = "system://refresh",
                        thumbnailUrl = "",
                        isLive = false
                    )
                )
                updateRowAdapter.add(
                    StreamItem(
                        id = 999999,
                        categoryId = -2,
                        categoryName = "System",
                        categoryIcon = "⚙️",
                        title = "Check for Updates",
                        participants = "System Update Manager",
                        sport = "System",
                        hlsUrl = "system://update",
                        thumbnailUrl = "",
                        isLive = false
                    )
                )
                rowsAdapter.add(ListRow(HeaderItem("⚙️ System Updates"), updateRowAdapter))

                if (streams.isEmpty() && sportSrcStreams.isEmpty()) {
                    Toast.makeText(
                        requireContext(),
                        "No streams available. Add some via the admin panel.",
                        Toast.LENGTH_LONG
                    ).show()
                }

            } catch (e: Exception) {
                Toast.makeText(
                    requireContext(),
                    "Cannot connect to backend: ${e.localizedMessage}",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }
    
    fun onToggleFavorite(streamId: String) {
        toggleFavorite(streamId)
        loadStreams() // Refresh UI
    }
}
