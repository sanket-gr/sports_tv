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

        adapter = rowsAdapter

        // ── Item click → open player ──────────────────────────────────────────
        onItemViewClickedListener = OnItemViewClickedListener { _, item, _, _ ->
            val stream = item as StreamItem
            PlaybackActivity.start(requireContext(), stream)
        }
        
        // ── Long click → toggle favorite ─────────────────────────────────────
        onItemViewSelectedListener = OnItemViewSelectedListener { _, _, _, _ -> }
        setOnItemViewClickedListener { _, item, _, _ ->
             val stream = item as StreamItem
             PlaybackActivity.start(requireContext(), stream)
        }
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

                // Separate Live vs Upcoming
                val liveStreams = streams.filter { it.isLive }
                val upcomingStreams = streams.filter { !it.isLive }
                
                // Extract favorites
                val favoriteStreams = streams.filter { favs.contains(it.id.toString()) }

                rowsAdapter.clear()
                
                // 1. Favorites Row
                if (favoriteStreams.isNotEmpty()) {
                    val cardPresenter = CardPresenter(favs) { streamId -> onToggleFavorite(streamId) }
                    val listRowAdapter = ArrayObjectAdapter(cardPresenter)
                    favoriteStreams.forEach { listRowAdapter.add(it) }
                    rowsAdapter.add(ListRow(HeaderItem("⭐ Favorites"), listRowAdapter))
                }

                // 2. Live Categories
                val grouped = liveStreams.groupBy { it.categoryName }
                grouped.forEach { (categoryName, categoryStreams) ->
                    val cardPresenter = CardPresenter(favs) { streamId -> onToggleFavorite(streamId) }
                    val listRowAdapter = ArrayObjectAdapter(cardPresenter)
                    categoryStreams.forEach { listRowAdapter.add(it) }

                    val headerItem = HeaderItem(categoryName)
                    rowsAdapter.add(ListRow(headerItem, listRowAdapter))
                }
                
                // 3. Upcoming Streams
                if (upcomingStreams.isNotEmpty()) {
                    val cardPresenter = CardPresenter(favs) { streamId -> onToggleFavorite(streamId) }
                    val listRowAdapter = ArrayObjectAdapter(cardPresenter)
                    upcomingStreams.forEach { listRowAdapter.add(it) }
                    rowsAdapter.add(ListRow(HeaderItem("📅 Upcoming / Offline"), listRowAdapter))
                }

                if (streams.isEmpty()) {
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
