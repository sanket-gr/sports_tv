package com.sportstv.app

import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.leanback.app.BrowseSupportFragment
import androidx.leanback.widget.*
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

/**
 * MainFragment – the home screen of the TV app.
 *
 * Shows a horizontal row of stream cards for each sport category,
 * Netflix-style. Data is fetched from the Python backend.
 */
class MainFragment : BrowseSupportFragment() {

    private val rowsAdapter = ArrayObjectAdapter(ListRowPresenter())

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
            if (stream.hlsUrl.isBlank()) {
                Toast.makeText(requireContext(), "Stream not ready yet, try again shortly.", Toast.LENGTH_SHORT).show()
            } else {
                PlaybackActivity.start(requireContext(), stream)
            }
        }

        loadStreams()
    }

    private fun loadStreams() {
        lifecycleScope.launch {
            try {
                val streams = ApiClient.service.getStreams(liveOnly = true)

                // Group by category name preserving order
                val grouped = streams.groupBy { it.categoryName }

                rowsAdapter.clear()
                grouped.forEach { (categoryName, categoryStreams) ->
                    val cardPresenter = CardPresenter()
                    val listRowAdapter = ArrayObjectAdapter(cardPresenter)
                    categoryStreams.forEach { listRowAdapter.add(it) }

                    val headerItem = HeaderItem(categoryName)
                    rowsAdapter.add(ListRow(headerItem, listRowAdapter))
                }

                if (streams.isEmpty()) {
                    Toast.makeText(
                        requireContext(),
                        "No live streams available. Add some via the admin panel.",
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
}
