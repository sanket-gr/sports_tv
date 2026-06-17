package com.sportstv.app

import android.os.Bundle
import android.view.View
import android.widget.TextView
import androidx.fragment.app.FragmentActivity

import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import android.widget.Toast
import android.content.Intent

/**
 * MainActivity hosts the MainFragment (Leanback BrowseSupportFragment).
 */
class MainActivity : FragmentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        if (savedInstanceState == null) {
            supportFragmentManager.beginTransaction()
                .replace(R.id.main_browse_fragment, MainFragment())
                .commit()
        }

        handleIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleIntent(intent)
    }

    private fun handleIntent(intent: Intent) {
        val action = intent.action
        val data = intent.data

        if (Intent.ACTION_VIEW == action && data != null && data.scheme == "sportstv" && data.host == "watch") {
            val streamIdStr = data.lastPathSegment
            val streamId = streamIdStr?.toIntOrNull()
            
            if (streamId != null) {
                lifecycleScope.launch {
                    try {
                        val stream = ApiClient.service.getStream(streamId)
                        PlaybackActivity.start(this@MainActivity, stream)
                    } catch (e: Exception) {
                        Toast.makeText(this@MainActivity, "Could not load stream: ${e.message}", Toast.LENGTH_LONG).show()
                    }
                }
            }
        }
    }
}
