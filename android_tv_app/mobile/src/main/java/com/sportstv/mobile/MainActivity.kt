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
    private lateinit var categoryAdapter: CategoryAdapter
    private lateinit var recyclerView: RecyclerView
    private lateinit var statusTextView: TextView
    private var currentTabId = R.id.navigation_home
    private var currentCategory = "All"

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

        // Initialize Category RecyclerView
        categoryAdapter = CategoryAdapter(emptyList()) { selected ->
            currentCategory = selected
            updateViewForTab(currentTabId)
        }
        binding.categoryRecycler.layoutManager = LinearLayoutManager(this, LinearLayoutManager.HORIZONTAL, false)
        binding.categoryRecycler.adapter = categoryAdapter

        // Initialize RecyclerView
        recyclerView = RecyclerView(this).apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
        }
        streamAdapter = StreamAdapter(emptyList()) { stream ->
            PlaybackActivity.start(this, stream)
        }
        recyclerView.adapter = streamAdapter

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
                    binding.categoryRecycler.visibility = View.GONE
                    binding.topLiveContainer.visibility = View.GONE
                } else {
                    statusTextView.visibility = View.GONE
                    
                    // Extract unique categories
                    val sports = combinedStreams.map { it.sport.replaceFirstChar { c -> c.uppercase() } }.distinct()
                    categoryAdapter.updateCategories(listOf("All") + sports)
                    
                    updateViewForTab(currentTabId)
                }
            } catch (e: Exception) {
                statusTextView.text = "Error fetching streams:\n${e.message}"
                statusTextView.visibility = View.VISIBLE
            }
        }
    }

    private fun refreshCurrentView(forceNetworkRefresh: Boolean = false) {
        if (forceNetworkRefresh) {
            fetchStreams()
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
            binding.categoryRecycler.visibility = View.GONE
            binding.topLiveContainer.visibility = View.GONE
            fetchStreams()
        } else {
            binding.categoryRecycler.visibility = View.VISIBLE
            binding.container.addView(recyclerView)
            
            // Filter by Category
            var filtered = allStreams
            if (currentCategory != "All") {
                filtered = allStreams.filter { it.sport.equals(currentCategory, ignoreCase = true) }
            }
            
            // Extract Top Live Stream
            val topLive = filtered.firstOrNull { it.isLive }
            if (topLive != null) {
                binding.topLiveContainer.visibility = View.VISIBLE
                binding.topLiveContainer.removeAllViews()
                
                // Inflate a stream card for Top Live
                val topLiveBinding = com.sportstv.mobile.databinding.ItemStreamCardBinding.inflate(layoutInflater, binding.topLiveContainer, false)
                val holder = streamAdapter.StreamViewHolder(topLiveBinding)
                holder.bind(topLive)
                binding.topLiveContainer.addView(topLiveBinding.root)
                
                // Show the rest in the recycler
                streamAdapter.updateData(filtered.filter { it.id != topLive.id })
            } else {
                binding.topLiveContainer.visibility = View.GONE
                streamAdapter.updateData(filtered)
            }
        }
    }

    private fun showFavoritesView() {
        binding.container.removeAllViews()
        binding.categoryRecycler.visibility = View.GONE
        binding.topLiveContainer.visibility = View.GONE
        
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
