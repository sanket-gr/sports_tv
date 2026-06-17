package com.sportstv.mobile

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
            // Launch PlaybackActivity when stream card is clicked
            PlaybackActivity.start(this, stream)
        }
        recyclerView.adapter = streamAdapter

        // Fetch streams from backend
        fetchStreams()

        // Setup bottom navigation selection listener
        binding.navView.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.navigation_home -> {
                    showHomeView()
                    true
                }
                R.id.navigation_favorites -> {
                    showFavoritesView()
                    true
                }
                else -> false
            }
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
                allStreams = streams

                if (streams.isEmpty()) {
                    statusTextView.text = "No streams found"
                    statusTextView.visibility = View.VISIBLE
                } else {
                    statusTextView.visibility = View.GONE
                    binding.container.removeAllViews()
                    binding.container.addView(recyclerView)
                    streamAdapter.updateData(streams)
                }
            } catch (e: Exception) {
                statusTextView.text = "Error fetching streams:\n${e.message}"
                statusTextView.visibility = View.VISIBLE
            }
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
        val favoritesPlaceholder = TextView(this).apply {
            text = "Favorites screen placeholder\n(Favorites persistence will be implemented in Phase 8)"
            textSize = 16f
            gravity = Gravity.CENTER
            setPadding(32, 32, 32, 32)
            setTextColor(0xFF64748B.toInt())
        }
        binding.container.addView(favoritesPlaceholder)
    }
}
