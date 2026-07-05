package com.sportstv.mobile

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.sportstv.mobile.databinding.ActivityMainBinding
import com.sportstv.mobile.model.StreamItem
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var allStreams: List<StreamItem> = emptyList()
    private lateinit var streamAdapter: StreamAdapter
    private lateinit var recyclerView: RecyclerView
    private lateinit var statusTextView: TextView
    private var currentTabId = R.id.navigation_home

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Initialize status TextView
        statusTextView = TextView(this).apply {
            text = "Loading streams..."
            textSize = 18f
            gravity = Gravity.CENTER
            setTextColor(0xFF0F172A.toInt())
        }
        binding.container.addView(statusTextView)

        // Initialize RecyclerView
        recyclerView = RecyclerView(this).apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        }

        streamAdapter = StreamAdapter(emptyList()) { stream ->
            // Launch StreamDetailBottomSheet when stream card is clicked
            val bottomSheet = StreamDetailBottomSheet.newInstance(stream).apply {
                onFavoritesChangedListener = {
                    refreshCurrentView()
                }
            }
            bottomSheet.show(supportFragmentManager, "stream_detail")
        }

        binding.root.findViewById<View>(R.id.fab_refresh)?.setOnClickListener {
            refreshCurrentView(forceNetworkRefresh = true)
        }
        recyclerView.adapter = streamAdapter

        // Fetch streams from backend
        fetchStreams()

        // Setup bottom navigation selection listener
        binding.navView.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.navigation_home -> {
                    currentTabId = item.itemId
                    showHomeView()
                    true
                }
                R.id.navigation_favorites -> {
                    currentTabId = item.itemId
                    showFavoritesView()
                    true
                }
                R.id.navigation_update -> {
                    lifecycleScope.launch {
                        android.widget.Toast.makeText(this@MainActivity, "Checking for updates...", android.widget.Toast.LENGTH_SHORT).show()
                        UpdateChecker.checkForUpdate(this@MainActivity, showToastIfLatest = true)
                    }
                    false // Don't highlight/switch to this tab
                }
                else -> false
            }
        }

        // Handle deep link if app is launched via URI
        handleIntent(intent)

        // Check for updates automatically on startup
        lifecycleScope.launch {
            UpdateChecker.checkForUpdate(this@MainActivity)
        }
    }

    private fun fetchStreams() {
        lifecycleScope.launch {
            try {
                statusTextView.text = "Loading streams..."
                statusTextView.visibility = View.VISIBLE
                
                val streams = withContext(Dispatchers.IO) {
                    ApiClient.service.getStreams(liveOnly = false)
                }

                val sportSrcStreams = try {
                    withContext(Dispatchers.IO) {
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
                    }
                } catch (e: Exception) {
                    emptyList()
                }

                // Combine sportSrc streams with regular streams
                val combinedStreams = sportSrcStreams + streams
                allStreams = combinedStreams

                if (combinedStreams.isEmpty()) {
                    statusTextView.text = "No streams found"
                    statusTextView.visibility = View.VISIBLE
                } else {
                    statusTextView.visibility = View.GONE
                    binding.container.removeAllViews()
                    binding.container.addView(recyclerView)
                    streamAdapter.updateData(combinedStreams)
                }
            } catch (e: Exception) {
                statusTextView.text = "Error fetching streams:\n${e.message}"
                statusTextView.visibility = View.VISIBLE
            }
        }
    }

    private fun refreshCurrentView(forceNetworkRefresh: Boolean = false) {
        if (forceNetworkRefresh) {
            statusTextView.text = "Refreshing..."
            statusTextView.visibility = View.VISIBLE
            recyclerView.visibility = View.GONE
            
            lifecycleScope.launch {
                try {
                    val matches = withContext(Dispatchers.IO) {
                        ApiClient.service.getSportSrcMatches()
                    }
                    
                    val streams = matches.map { match ->
                        StreamItem(
                            id = match.id.hashCode(),
                            categoryId = match.sport.hashCode(),
                            categoryName = match.sport.replaceFirstChar { it.uppercase() },
                            categoryIcon = "",
                            title = match.title,
                            participants = match.title,
                            sport = match.sport,
                            hlsUrl = "sportsrc://${match.id}",
                            iframeUrl = "",
                            cfDomain = "",
                            thumbnailUrl = match.thumbnail,
                            isLive = match.status == "inprogress"
                        )
                    }
                    allStreams = streams
                    updateViewForTab(currentTabId)
                } catch (e: Exception) {
                    statusTextView.text = "Failed to load streams: ${e.message}"
                    statusTextView.visibility = View.VISIBLE
                    recyclerView.visibility = View.GONE
                }
            }
        } else {
            updateViewForTab(currentTabId)
        }
    }

    private fun updateViewForTab(tabId: Int) {
        if (tabId == R.id.navigation_home) {
            showHomeView()
        } else if (tabId == R.id.navigation_favorites) {
            showFavoritesView()
        }
    }

    private fun showHomeView() {
        binding.container.removeAllViews()
        if (allStreams.isEmpty()) {
            binding.container.addView(statusTextView)
            fetchStreams()
        } else {
            binding.container.addView(recyclerView)
            streamAdapter.updateData(allStreams)
        }
    }

    private fun showFavoritesView() {
        binding.container.removeAllViews()
        val favIds = FavoritesManager.getFavoriteIds(this)
        val favStreams = allStreams.filter { favIds.contains(it.id) }

        if (favStreams.isEmpty()) {
            val favoritesPlaceholder = TextView(this).apply {
                text = "No favorites added yet.\nTap on any stream card to add it to favorites."
                textSize = 16f
                gravity = Gravity.CENTER
                setPadding(48, 48, 48, 48)
                setTextColor(0xFF64748B.toInt())
            }
            binding.container.addView(favoritesPlaceholder)
        } else {
            binding.container.addView(recyclerView)
            streamAdapter.updateData(favStreams)
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIntent(intent)
    }

    private fun handleIntent(intent: Intent) {
        val action = intent.action
        val data: Uri? = intent.data
        if (Intent.ACTION_VIEW == action && data != null) {
            val id = parseStreamId(data)
            if (id != -1) {
                PlaybackActivity.startWithId(this, id)
            } else {
                android.widget.Toast.makeText(this, "Invalid stream ID in deep link", android.widget.Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun parseStreamId(uri: Uri): Int {
        val idParam = uri.getQueryParameter("id")
        if (!idParam.isNullOrEmpty()) {
            return idParam.toIntOrNull() ?: -1
        }
        val pathSegments = uri.pathSegments
        if (pathSegments.isNotEmpty()) {
            return pathSegments.last().toIntOrNull() ?: -1
        }
        return -1
    }
}
