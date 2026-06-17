package com.sportstv.mobile

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.sportstv.mobile.databinding.ActivityMainBinding
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Add a default placeholder text in FrameLayout
        val textView = TextView(this).apply {
            text = "Loading streams..."
            textSize = 20f
            gravity = android.view.Gravity.CENTER
        }
        binding.container.addView(textView)

        // Fetch streams from backend on startup
        lifecycleScope.launch {
            try {
                val streams = withContext(Dispatchers.IO) {
                    ApiClient.service.getStreams(liveOnly = false)
                }
                val titles = if (streams.isEmpty()) "No streams found" else streams.joinToString("\n") { it.title }
                textView.text = "Retrieved streams:\n$titles"
            } catch (e: Exception) {
                textView.text = "Error fetching streams: ${e.message}"
            }
        }

        binding.navView.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.navigation_home -> {
                    textView.text = "Home screen placeholder"
                    true
                }
                R.id.navigation_favorites -> {
                    textView.text = "Favorites screen placeholder"
                    true
                }
                else -> false
            }
        }
    }
}
