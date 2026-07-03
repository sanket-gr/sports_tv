package com.sportstv.app

import android.os.Bundle
import androidx.fragment.app.FragmentActivity
import androidx.leanback.app.SearchSupportFragment
import androidx.leanback.widget.*
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import com.sportstv.app.model.StreamItem

class SearchActivity : FragmentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_search)

        if (savedInstanceState == null) {
            supportFragmentManager.beginTransaction()
                .replace(R.id.search_fragment, MySearchFragment())
                .commit()
        }
    }
}

class MySearchFragment : SearchSupportFragment(), SearchSupportFragment.SearchResultProvider {

    private val rowsAdapter = ArrayObjectAdapter(ListRowPresenter())
    private var allStreams = listOf<StreamItem>()
    private var allSportSrcMatches = listOf<StreamItem>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setSearchResultProvider(this)

        setOnItemViewClickedListener { _, item, _, _ ->
            val stream = item as StreamItem
            PlaybackActivity.start(requireContext(), stream)
        }

        // Preload all streams and matches for local filtering
        lifecycleScope.launch {
            try {
                allStreams = ApiClient.service.getStreams(liveOnly = false)
            } catch (e: Exception) {
                // ignore
            }
            try {
                allSportSrcMatches = ApiClient.service.getSportSrcMatches().map { match ->
                    StreamItem(
                        id = match.id.hashCode(),
                        categoryId = -1,
                        categoryName = "SportSRC",
                        categoryIcon = "🏆",
                        title = match.title,
                        participants = match.title,
                        sport = match.sport,
                        hlsUrl = "sportsrc://${match.id}",
                        thumbnailUrl = "",
                        isLive = true
                    )
                }
            } catch (e: Exception) {
                // ignore
            }
        }
    }

    override fun getResultsAdapter(): ObjectAdapter = rowsAdapter

    override fun onQueryTextChange(newQuery: String?): Boolean {
        filterResults(newQuery)
        return true
    }

    override fun onQueryTextSubmit(query: String?): Boolean {
        filterResults(query)
        return true
    }

    private fun filterResults(query: String?) {
        rowsAdapter.clear()
        if (query.isNullOrBlank()) return

        val q = query.lowercase().trim()

        // 1. Filter local streams
        val filteredStreams = allStreams.filter {
            it.title.lowercase().contains(q) || it.participants.lowercase().contains(q) || it.categoryName.lowercase().contains(q)
        }
        if (filteredStreams.isNotEmpty()) {
            val listAdapter = ArrayObjectAdapter(CardPresenter(emptySet()) {})
            filteredStreams.forEach { listAdapter.add(it) }
            rowsAdapter.add(ListRow(HeaderItem("Local Streams"), listAdapter))
        }

        // 2. Filter SportSRC matches
        val filteredSportSrc = allSportSrcMatches.filter {
            it.title.lowercase().contains(q) || it.sport.lowercase().contains(q)
        }
        if (filteredSportSrc.isNotEmpty()) {
            val listAdapter = ArrayObjectAdapter(CardPresenter(emptySet()) {})
            filteredSportSrc.forEach { listAdapter.add(it) }
            rowsAdapter.add(ListRow(HeaderItem("SportSRC Matches"), listAdapter))
        }
    }
}
