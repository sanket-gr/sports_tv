package com.sportstv.app

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.view.KeyEvent
import android.view.View
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.FragmentActivity
import androidx.lifecycle.lifecycleScope
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.hls.HlsMediaSource
import androidx.media3.ui.PlayerView
import kotlinx.coroutines.launch

/**
 * PlaybackActivity – full-screen ExoPlayer for HLS streams.
 *
 * Receives a StreamItem via Intent extras and starts HLS playback immediately.
 * D-pad: OK to play/pause, Back to exit.
 */
class PlaybackActivity : FragmentActivity() {

    companion object {
        private const val TAG = "PlaybackActivity"

        fun start(context: Context, stream: StreamItem) {
            val intent = Intent(context, PlaybackActivity::class.java).apply {
                putExtra("hls_url",      stream.hlsUrl)
                putExtra("stream_id",    stream.id)
                putExtra("title",        stream.title)
                putExtra("participants", stream.participants)
                putExtra("iframe_url",   stream.iframeUrl)
            }
            context.startActivity(intent)
        }
    }

    private var player: ExoPlayer? = null
    private lateinit var playerView: PlayerView
    private lateinit var loadingBar: ProgressBar
    private lateinit var errorView: View
    private lateinit var tvError: TextView
    private lateinit var btnRetry: Button
    private lateinit var tvMatchTitle: TextView
    private lateinit var tvMatchSub: TextView

    private var streamId: Int = -1
    private var hlsUrl: String = ""
    private var iframeUrl: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_playback)

        playerView  = findViewById(R.id.player_view)
        loadingBar  = findViewById(R.id.loading_bar)
        errorView   = findViewById(R.id.error_view)
        tvError     = findViewById(R.id.tv_error)
        btnRetry    = findViewById(R.id.btn_retry)
        tvMatchTitle = findViewById(R.id.tv_match_title)
        tvMatchSub   = findViewById(R.id.tv_match_sub)

        // Grab stream info
        hlsUrl       = intent.getStringExtra("hls_url") ?: ""
        streamId     = intent.getIntExtra("stream_id", -1)
        iframeUrl    = intent.getStringExtra("iframe_url") ?: ""
        val title        = intent.getStringExtra("title") ?: ""
        val participants = intent.getStringExtra("participants") ?: ""

        tvMatchTitle.text = if (participants.isNotBlank()) participants else title
        tvMatchSub.text   = title

        // Retry button: re-fetch HLS from backend then play
        btnRetry.setOnClickListener { refreshAndPlay() }

        if (hlsUrl.isNotBlank()) {
            initPlayer(hlsUrl)
        } else {
            // No HLS yet – try to fetch fresh from backend
            refreshAndPlay()
        }

        // Hide info overlay after 4 seconds
        playerView.postDelayed({
            findViewById<View>(R.id.match_info_overlay)
                .animate().alpha(0f).setDuration(600).start()
        }, 4000)
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Player setup
    // ──────────────────────────────────────────────────────────────────────────

    private fun initPlayer(url: String) {
        Log.d(TAG, "initPlayer url=$url")

        releasePlayer()
        showLoading(true)
        showError(false)

        // Build data source with browser-like headers so CDNs don't reject us
        val referer = if (iframeUrl.isNotBlank()) iframeUrl else "https://www.google.com/"
        val dataSourceFactory = DefaultHttpDataSource.Factory()
            .setUserAgent("Mozilla/5.0 (Linux; Android 11; TV) AppleWebKit/537.36 Chrome/119 Safari/537.36")
            .setDefaultRequestProperties(
                mapOf(
                    "Referer"        to referer,
                    "Origin"         to Uri.parse(referer).let { "${it.scheme}://${it.host}" },
                    "Accept"         to "*/*",
                    "Accept-Language" to "en-US,en;q=0.9",
                )
            )
            .setConnectTimeoutMs(15_000)
            .setReadTimeoutMs(15_000)

        player = ExoPlayer.Builder(this).build().also { exo ->
            playerView.player = exo

            val hlsSource = HlsMediaSource.Factory(dataSourceFactory)
                .createMediaSource(MediaItem.fromUri(Uri.parse(url)))

            exo.addListener(object : Player.Listener {
                override fun onIsLoadingChanged(isLoading: Boolean) {
                    if (!isLoading && exo.playbackState == Player.STATE_READY) {
                        showLoading(false)
                    }
                }

                override fun onPlaybackStateChanged(state: Int) {
                    when (state) {
                        Player.STATE_READY   -> showLoading(false)
                        Player.STATE_BUFFERING -> showLoading(true)
                        Player.STATE_ENDED   -> finish()
                        else -> {}
                    }
                }

                override fun onPlayerError(error: PlaybackException) {
                    Log.e(TAG, "Player error: ${error.message}", error)
                    showLoading(false)
                    val is404 = error.message?.contains("404") == true
                    val is403 = error.message?.contains("403") == true
                    when {
                        // Token expired — auto-refresh from backend silently
                        is404 || is403 -> {
                            Log.d(TAG, "Stream token expired (${if (is404) "404" else "403"}), auto-refreshing...")
                            refreshAndPlay()
                        }
                        error.message?.contains("Unable to connect") == true ||
                        error.message?.contains("Failed to connect") == true ||
                        error.message?.contains("UnknownHostException") == true -> {
                            showError(true, "Cannot reach stream server.\nCheck your network and tap Retry.")
                        }
                        else -> {
                            showError(true, "Playback error: ${error.message}\n\nTap Retry to try again.")
                        }
                    }
                }
            })

            exo.setMediaSource(hlsSource)
            exo.prepare()
            exo.playWhenReady = true
        }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Refresh HLS URL from backend, then play
    // ──────────────────────────────────────────────────────────────────────────

    private fun refreshAndPlay() {
        if (streamId < 0) {
            showError(true, "No stream ID available. Go back and re-open the stream.")
            return
        }
        releasePlayer()
        showLoading(true)
        showError(false)

        lifecycleScope.launch {
            try {
                // 1. Kick off re-extraction on backend
                Log.d(TAG, "Triggering re-extraction for stream $streamId")
                ApiClient.service.refreshStream(streamId)

                // 2. Poll backend every 5 seconds until we get a fresh URL (max 4 tries = 20s)
                var freshUrl = ""
                repeat(4) { attempt ->
                    if (freshUrl.isNotBlank()) return@repeat
                    kotlinx.coroutines.delay(5_000)
                    Log.d(TAG, "Polling for fresh URL (attempt ${attempt + 1}/4)...")
                    val stream = ApiClient.service.getStream(streamId)
                    if (stream.hlsUrl.isNotBlank() &&
                        stream.hlsUrl != hlsUrl) {   // make sure it's actually new
                        freshUrl  = stream.hlsUrl
                        iframeUrl = stream.iframeUrl
                    }
                }

                if (freshUrl.isBlank()) {
                    // Extraction may still be in progress or failed — use old URL as fallback
                    val stream = ApiClient.service.getStream(streamId)
                    freshUrl = stream.hlsUrl
                }

                if (freshUrl.isBlank()) {
                    showLoading(false)
                    showError(true, "Could not get a fresh stream link.\nThe event may have ended.\nTap Retry to try again.")
                } else {
                    hlsUrl = freshUrl
                    initPlayer(freshUrl)
                }
            } catch (e: Exception) {
                Log.e(TAG, "refreshAndPlay error", e)
                showLoading(false)
                showError(true, "Could not reach the backend server.\n${e.localizedMessage}\n\nMake sure the server is running and tap Retry.")
            }
        }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // UI helpers
    // ──────────────────────────────────────────────────────────────────────────

    private fun showLoading(show: Boolean) {
        loadingBar.visibility = if (show) View.VISIBLE else View.GONE
    }

    private fun showError(show: Boolean, msg: String = "") {
        errorView.visibility = if (show) View.VISIBLE else View.GONE
        if (show && msg.isNotEmpty()) tvError.text = msg
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Lifecycle / input
    // ──────────────────────────────────────────────────────────────────────────

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        return when (keyCode) {
            KeyEvent.KEYCODE_DPAD_CENTER,
            KeyEvent.KEYCODE_ENTER,
            KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE -> {
                player?.let { if (it.isPlaying) it.pause() else it.play() }
                // Show the overlay briefly
                val overlay = findViewById<View>(R.id.match_info_overlay)
                overlay.animate().cancel()
                overlay.alpha = 1f
                overlay.postDelayed({
                    overlay.animate().alpha(0f).setDuration(600).start()
                }, 3000)
                true
            }
            else -> super.onKeyDown(keyCode, event)
        }
    }

    private fun releasePlayer() {
        player?.release()
        player = null
    }

    override fun onStop()    { super.onStop();    player?.pause() }
    override fun onDestroy() { super.onDestroy(); releasePlayer() }
}
