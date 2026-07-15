package com.sportstv.app

import android.animation.ObjectAnimator
import android.animation.ValueAnimator
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.view.KeyEvent
import android.view.View
import android.view.WindowManager
import android.view.animation.LinearInterpolator
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import android.widget.LinearLayout
import android.view.ViewGroup
import androidx.fragment.app.FragmentActivity
import androidx.lifecycle.lifecycleScope
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.datasource.DataSource
import androidx.media3.datasource.DataSpec
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.datasource.TransferListener
import androidx.media3.exoplayer.DefaultLoadControl
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.hls.HlsMediaSource
import androidx.media3.ui.PlayerView
import kotlinx.coroutines.launch
import com.sportstv.app.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
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
                putExtra("cf_domain",    stream.cfDomain)
            }
            context.startActivity(intent)
        }
    }

    private var player: ExoPlayer? = null
    private lateinit var playerView: PlayerView
    private lateinit var loadingView: View
    private lateinit var tvLoadingTitle: TextView
    private lateinit var loadingBar: ProgressBar
    private lateinit var errorView: View
    private lateinit var tvError: TextView
    private lateinit var tvErrorCountdown: TextView
    private lateinit var btnRetry: Button
    private lateinit var tvMatchTitle: TextView
    private lateinit var tvMatchSub: TextView
    private var errorCountdownJob: kotlinx.coroutines.Job? = null
    private var autoRetryCount = 0
    private val MAX_AUTO_RETRIES = 3

    private var streamId: Int = -1
    private var hlsUrl: String = ""
    private var originalUrl: String = ""
    private var iframeUrl: String = ""
    private var cfDomain: String = ""
    private var sportSrcMatchDetail: SportSrcMatchDetail? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Keep the screen on during video playback to prevent screensaver/sleep mode
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        
        setContentView(R.layout.activity_playback)

        playerView   = findViewById(R.id.player_view)
        loadingView  = findViewById(R.id.loading_view)
        tvLoadingTitle = findViewById(R.id.tv_loading_title)
        loadingBar   = findViewById(R.id.loading_bar)
        errorView    = findViewById(R.id.error_view)
        tvError      = findViewById(R.id.tv_error)
        tvErrorCountdown = findViewById(R.id.tv_error_countdown)
        btnRetry     = findViewById(R.id.btn_retry)
        tvMatchTitle = findViewById(R.id.tv_match_title)
        tvMatchSub   = findViewById(R.id.tv_match_sub)

        // Grab stream info
        hlsUrl       = intent.getStringExtra("hls_url") ?: ""
        originalUrl  = hlsUrl
        streamId     = intent.getIntExtra("stream_id", -1)
        iframeUrl    = intent.getStringExtra("iframe_url") ?: ""
        cfDomain     = intent.getStringExtra("cf_domain") ?: ""
        val title        = intent.getStringExtra("title") ?: ""
        val participants = intent.getStringExtra("participants") ?: ""

        tvMatchTitle.text = if (participants.isNotBlank()) participants else title
        tvMatchSub.text   = title
        tvLoadingTitle.text = tvMatchTitle.text

        // ── Ticker setup ────────────────────────────────────────────────────
        val tickerContainer = findViewById<View>(R.id.ticker_container)
        val tickerText      = findViewById<TextView>(R.id.ticker_text)
        val btnToggleTicker = findViewById<Button>(R.id.btn_toggle_ticker)
        val topControls     = findViewById<View>(R.id.top_controls)

        val tickerMessage = getString(R.string.ticker_message)
        if (tickerMessage.isBlank()) {
            tickerContainer.visibility = View.GONE
            btnToggleTicker.visibility = View.GONE
        } else {
            startTickerAnimation(tickerText, tickerMessage)

            btnToggleTicker.setOnClickListener {
                if (tickerContainer.visibility == View.VISIBLE) {
                    tickerContainer.visibility = View.GONE
                    tickerText.isSelected = false
                    btnToggleTicker.text = "📺 Ticker: OFF"
                } else {
                    tickerContainer.visibility = View.VISIBLE
                    tickerText.isSelected = true
                    btnToggleTicker.text = "📺 Ticker: ON"
                }
            }
        }


        // ── Retry button ────────────────────────────────────────────────────
        btnRetry.setOnClickListener { triggerRetry() }

        // If hlsUrl is a direct IP URL (not proxied via backend), always refresh first
        val isProxied = hlsUrl.contains("/api/proxy")

        if (hlsUrl.startsWith("sportsrc://")) {
            resolveSportSrcAndPlay(hlsUrl)
        } else if (hlsUrl.isNotBlank() && isProxied) {
            initPlayer(hlsUrl)
        } else {
            // No URL, or old-style direct IP URL → fetch fresh proxied URL from backend
            triggerRetry()
        }

        // Hide match info overlay + ticker toggle button after 4 seconds
        playerView.postDelayed({
            findViewById<View>(R.id.match_info_overlay)
                .animate().alpha(0f).setDuration(600).start()
            topControls.animate().alpha(0f).setDuration(600).withEndAction {
                topControls.visibility = View.GONE
            }.start()
        }, 4000)

        // ── Server Selection Sidebar setup ──────────────────────────────────
        val sidebar = findViewById<View>(R.id.match_center_sidebar)
        val btnToggleStats = findViewById<Button>(R.id.btn_toggle_stats)

        btnToggleStats.text = "📡 Servers"
        btnToggleStats.setOnClickListener {
            val isHidden = sidebar.visibility == View.GONE
            toggleSidebar(isHidden)
            if (isHidden) populateServersList()
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    private fun startTickerAnimation(tickerText: TextView, tickerMessage: String) {
        // Repeat the text a few times with spacing so the native marquee loop feels continuous
        val repeatedText = (tickerMessage + "          ").repeat(10)
        tickerText.text = repeatedText
        
        // Native marquee only runs when the TextView is selected
        tickerText.isSelected = true
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Player setup
    // ─────────────────────────────────────────────────────────────────────────

    private fun cleanReferer(url: String): String {
        if (url.isBlank()) return "https://www.google.com/"
        return try {
            val uri = Uri.parse(url)
            val scheme = uri.scheme ?: "https"
            val host = uri.host ?: return url
            "$scheme://$host/"
        } catch (e: Exception) {
            url
        }
    }

    private fun initPlayer(url: String) {
        Log.d(TAG, "initPlayer url=$url  iframeUrl=$iframeUrl  cfDomain=$cfDomain")

        releasePlayer()
        showLoading(true)
        showError(false)

        // Primary referer: the iframe embed page
        val referer = cleanReferer(iframeUrl)

        val baseHttpDataSourceFactory = DefaultHttpDataSource.Factory()
            .setAllowCrossProtocolRedirects(true)
            .setUserAgent("Mozilla/5.0 (Linux; Android 11; TV) AppleWebKit/537.36 Chrome/119 Safari/537.36")
            .setDefaultRequestProperties(
                mapOf(
                    "Referer"         to referer,
                    "Origin"          to Uri.parse(referer).let { "${it.scheme}://${it.host}" },
                    "Accept"          to "*/*",
                    "Accept-Language" to "en-US,en;q=0.9",
                )
            )
            .setConnectTimeoutMs(30_000)
            .setReadTimeoutMs(30_000)

        val dataSourceFactory = DynamicHeaderDataSourceFactory(
            baseHttpDataSourceFactory,
            iframeUrl,
            cfDomain
        )

        // Balanced live streaming buffers: enough cushion to absorb proxy latency
        val loadControl = DefaultLoadControl.Builder()
            .setBufferDurationsMs(
                5_000,   // minBufferMs  – buffer 5s before starting
                30_000,  // maxBufferMs  – keep up to 30s ahead for stability
                2_500,   // bufferForPlaybackMs – resume after 2.5s buffered
                3_000    // bufferForPlaybackAfterRebufferMs – 3s after rebuffer
            )
            .build()

        player = ExoPlayer.Builder(this)
            .setLoadControl(loadControl)
            .build().also { exo ->
            playerView.player = exo

            // Force HLS MIME type — CDNs disguise playlists as .txt/.woff2 etc.
            val mediaItem = MediaItem.Builder()
                .setUri(Uri.parse(url))
                .setMimeType("application/x-mpegURL")
                .setLiveConfiguration(
                    MediaItem.LiveConfiguration.Builder()
                        .setTargetOffsetMs(5_000)     // target 5s behind live
                        .setMaxOffsetMs(10_000)        // max 10s behind
                        .setMinPlaybackSpeed(0.97f)    // slow down slightly if too close
                        .setMaxPlaybackSpeed(1.04f)    // speed up to catch up
                        .build()
                )
                .build()
            val hlsSource = HlsMediaSource.Factory(dataSourceFactory)
                .setAllowChunklessPreparation(true)
                .createMediaSource(mediaItem)

            exo.addListener(object : Player.Listener {
                override fun onIsLoadingChanged(isLoading: Boolean) {
                    if (!isLoading && exo.playbackState == Player.STATE_READY) {
                        showLoading(false)
                    }
                }

                override fun onPlaybackStateChanged(state: Int) {
                    when (state) {
                        Player.STATE_READY    -> {
                            showLoading(false)
                            autoRetryCount = 0 // Reset retry counter on successful playback
                        }
                        Player.STATE_BUFFERING -> showLoading(true)
                        Player.STATE_ENDED    -> finish()
                        else -> {}
                    }
                }

                override fun onPlayerError(error: PlaybackException) {
                    Log.e(TAG, "Player error code=${error.errorCode} msg=${error.message} retryCount=$autoRetryCount", error)
                    showLoading(false)
                    val msg = error.message ?: ""
                    when {
                        // Token expired — auto-refresh from backend silently
                        msg.contains("404") || msg.contains("403") -> {
                            Log.d(TAG, "Stream token expired, auto-refreshing...")
                            triggerRetry()
                        }
                        msg.contains("Unable to connect") ||
                        msg.contains("Failed to connect") ||
                        msg.contains("UnknownHostException") -> {
                            if (autoRetryCount < MAX_AUTO_RETRIES) {
                                autoRetryCount++
                                Log.d(TAG, "Network error, silent retry #$autoRetryCount...")
                                lifecycleScope.launch {
                                    kotlinx.coroutines.delay(1_500L * autoRetryCount)
                                    initPlayer(url)
                                }
                            } else {
                                showError(true, "Cannot reach stream server.\nCheck your network and tap Retry.", 5)
                            }
                        }
                        else -> {
                            // HLS errors (3002, etc.) — auto-retry silently before showing error
                            if (autoRetryCount < MAX_AUTO_RETRIES) {
                                autoRetryCount++
                                Log.d(TAG, "Playback error ${error.errorCode}, silent retry #$autoRetryCount...")
                                lifecycleScope.launch {
                                    kotlinx.coroutines.delay(1_500L * autoRetryCount)
                                    initPlayer(url)
                                }
                            } else {
                                showError(true, "Playback error (${error.errorCode}): $msg\n\nTap Retry to try again.", 5)
                            }
                        }
                    }
                }
            })

            exo.setMediaSource(hlsSource)
            exo.prepare()
            exo.playWhenReady = true
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Refresh HLS URL from backend, then play
    // ─────────────────────────────────────────────────────────────────────────

    private fun refreshAndPlay() {
        errorCountdownJob?.cancel()
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
                var freshUrl  = ""
                var freshCfDomain = ""
                repeat(4) { attempt ->
                    if (freshUrl.isNotBlank()) return@repeat
                    kotlinx.coroutines.delay(5_000)
                    Log.d(TAG, "Polling for fresh URL (attempt ${attempt + 1}/4)...")
                    val stream = ApiClient.service.getStream(streamId)
                    if (stream.hlsUrl.isNotBlank() &&
                        stream.hlsUrl != hlsUrl) {   // make sure it's actually new
                        freshUrl      = stream.hlsUrl
                        iframeUrl     = stream.iframeUrl
                        freshCfDomain = stream.cfDomain
                    }
                }

                if (freshUrl.isBlank()) {
                    // Extraction may still be in progress or failed — use old URL as fallback
                    val stream = ApiClient.service.getStream(streamId)
                    freshUrl      = stream.hlsUrl
                    freshCfDomain = stream.cfDomain
                }

                if (freshUrl.isBlank()) {
                    showLoading(false)
                    showError(true, "Could not get a fresh stream link.\nThe event may have ended.\nTap Retry to try again.")
                } else {
                    hlsUrl   = freshUrl
                    cfDomain = freshCfDomain
                    initPlayer(freshUrl)
                }
            } catch (e: Exception) {
                Log.e(TAG, "refreshAndPlay error", e)
                showLoading(false)
                showError(true, "Could not reach the backend server.\n${e.localizedMessage}\n\nMake sure the server is running and tap Retry.")
            }
        }
    }

    private fun resolveSportSrcAndPlay(url: String) {
        val matchId = url.removePrefix("sportsrc://")
        showLoading(true)
        showError(false)
        lifecycleScope.launch {
            try {
                val detail = withContext(Dispatchers.IO) {
                    ApiClient.service.getSportSrcDetail(matchId)
                }
                sportSrcMatchDetail = detail  // Save for server selection sidebar
                val realHls = detail.hlsUrl ?: ""
                if (realHls.isNotBlank()) {
                    iframeUrl = detail.streamUrl ?: ""
                    cfDomain = try { Uri.parse(realHls).host ?: "" } catch(e: Exception) { "" }
                    
                    // Route through backend proxy to handle Referer/Origin headers and bypass CORS
                    val proxiedUrl = if (realHls.startsWith("http")) {
                        val encodedHls = Uri.encode(realHls)
                        val encodedReferer = Uri.encode(iframeUrl)
                        "${BASE_URL}api/proxy?url=$encodedHls&referer=$encodedReferer"
                    } else {
                        realHls
                    }
                    
                    hlsUrl = proxiedUrl
                    initPlayer(proxiedUrl)
                } else {
                    showLoading(false)
                    showError(true, "No active HLS link found for this match.")
                }
            } catch (e: Exception) {
                showLoading(false)
                showError(true, "Failed to load match details.\n${e.localizedMessage}")
            }
        }
    }

    private fun triggerRetry() {
        if (originalUrl.startsWith("sportsrc://")) {
            resolveSportSrcAndPlay(originalUrl)
        } else {
            refreshAndPlay()
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // UI helpers
    // ─────────────────────────────────────────────────────────────────────────

    private fun showLoading(show: Boolean) {
        loadingView.visibility = if (show) View.VISIBLE else View.GONE
    }

    private fun showError(show: Boolean, msg: String = "", autoRetryDelay: Int = 0) {
        errorCountdownJob?.cancel()
        errorView.visibility = if (show) View.VISIBLE else View.GONE
        
        if (show) {
            if (msg.isNotEmpty()) tvError.text = msg
            
            if (autoRetryDelay > 0) {
                tvErrorCountdown.visibility = View.VISIBLE
                errorCountdownJob = lifecycleScope.launch {
                    for (i in autoRetryDelay downTo 1) {
                        tvErrorCountdown.text = "Retrying in $i..."
                        kotlinx.coroutines.delay(1000)
                    }
                    tvErrorCountdown.text = "Retrying now..."
                    triggerRetry()
                }
            } else {
                tvErrorCountdown.visibility = View.GONE
            }
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Lifecycle / input
    // ─────────────────────────────────────────────────────────────────────────

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        return when (keyCode) {
            KeyEvent.KEYCODE_BACK -> {
                val sidebar = findViewById<View>(R.id.match_center_sidebar)
                if (sidebar.visibility == View.VISIBLE) {
                    toggleSidebar(false)
                    true
                } else {
                    super.onKeyDown(keyCode, event)
                }
            }
            KeyEvent.KEYCODE_DPAD_DOWN -> {
                val sidebar = findViewById<View>(R.id.match_center_sidebar)
                if (sidebar.visibility == View.GONE) {
                    toggleSidebar(true)
                    true
                } else {
                    super.onKeyDown(keyCode, event)
                }
            }
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

    private fun toggleSidebar(show: Boolean) {
        val sidebar = findViewById<View>(R.id.match_center_sidebar)
        sidebar.visibility = if (show) View.VISIBLE else View.GONE
        if (show) {
            populateServersList()
            // Focus the first server button if available
            val container = findViewById<LinearLayout>(R.id.layout_tv_server_list)
            if (container.childCount > 0) {
                container.getChildAt(0).requestFocus()
            }
        }
    }

    private fun populateServersList() {
        val container = findViewById<LinearLayout>(R.id.layout_tv_server_list)
        container.removeAllViews()

        val detail = sportSrcMatchDetail
        val streams = detail?.streams

        if (streams.isNullOrEmpty()) {
            val tvMsg = TextView(this).apply {
                text = "No additional servers available for this stream."
                setTextColor(0xFFE2E8F0.toInt())
                textSize = 14f
                setPadding(16, 24, 16, 24)
            }
            container.addView(tvMsg)
            return
        }

        streams.forEachIndexed { index, stream ->
            val btn = Button(this).apply {
                val hdText = if (stream.hd) " ★ HD" else ""
                text = "Server ${index + 1}: ${stream.language}$hdText"
                textSize = 13f
                setTextColor(0xFFFFFFFF.toInt())
                val bgColor = if (stream.hd) 0xFF0F766E.toInt() else 0xFF1E293B.toInt()
                backgroundTintList = android.content.res.ColorStateList.valueOf(bgColor)
                focusable = View.FOCUSABLE
                isClickable = true
                setPadding(24, 20, 24, 20)

                val lp = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                )
                lp.setMargins(0, 6, 0, 6)
                this.layoutParams = lp

                setOnClickListener {
                    toggleSidebar(false)
                    playSelectedServer(stream)
                }
            }
            container.addView(btn)
        }
    }

    private fun playSelectedServer(stream: SportSrcStream) {
        showLoading(true)
        showError(false)
        lifecycleScope.launch {
            try {
                val response = withContext(Dispatchers.IO) {
                    ApiClient.service.resolveStream(stream.embedUrl)
                }
                val realHls = response.hlsUrl ?: ""
                if (realHls.isNotBlank()) {
                    iframeUrl = stream.embedUrl
                    cfDomain = try { Uri.parse(realHls).host ?: "" } catch(e: Exception) { "" }

                    val proxiedUrl = if (realHls.startsWith("http")) {
                        val encodedHls = Uri.encode(realHls)
                        val encodedReferer = Uri.encode(iframeUrl)
                        "${BASE_URL}api/proxy?url=$encodedHls&referer=$encodedReferer"
                    } else {
                        realHls
                    }

                    hlsUrl = proxiedUrl
                    initPlayer(proxiedUrl)
                } else {
                    showLoading(false)
                    showError(true, "Failed to resolve stream link for this server.")
                }
            } catch (e: Exception) {
                showLoading(false)
                showError(true, "Error resolving server stream.\n${e.localizedMessage}")
            }
        }
    }

    private fun releasePlayer() {
        player?.release()
        player = null
    }

    override fun onStop()    { super.onStop();    player?.pause() }
    override fun onDestroy() { super.onDestroy(); releasePlayer() }
}

// =============================================================================
// DynamicHeaderDataSource  –  sets the right Referer/Origin per request domain
// =============================================================================

class DynamicHeaderDataSource(
    private val baseDataSource: DefaultHttpDataSource,
    private val iframeUrl: String,
    private val cfDomain: String   // e.g. "silverpathgardens.space" from backend
) : DataSource {

    override fun addTransferListener(transferListener: TransferListener) {
        baseDataSource.addTransferListener(transferListener)
    }

    private fun cleanReferer(url: String): String {
        if (url.isBlank()) return "https://www.google.com/"
        return try {
            val uri = Uri.parse(url)
            val scheme = uri.scheme ?: "https"
            val host = uri.host ?: return url
            "$scheme://$host/"
        } catch (e: Exception) {
            url
        }
    }

    override fun open(dataSpec: DataSpec): Long {
        val url     = dataSpec.uri.toString()
        val host    = dataSpec.uri.host ?: ""
        val headers = dataSpec.httpRequestHeaders.toMutableMap()

        when {
            // ── sportsurge / aapmains CDN ─────────────────────────────────
            host.endsWith(".hereisman.net") || host.endsWith(".aapmains.net") ||
            host == "hereisman.net" || host.contains("aapmains") -> {
                if (url.contains("load-playlist")) {
                    headers["Referer"] = "https://gooz.aapmains.net/"
                    headers["Origin"]  = "https://gooz.aapmains.net"
                } else {
                    headers["Referer"] = "https://chatgpt.hereisman.net/"
                    headers["Origin"]  = "https://chatgpt.hereisman.net"
                }
            }

            // ── suisports / cfDomain CDN: IP-based or matching cfDomain ──
            // The cfDomain is the "silverpathgardens.space"-type CDN domain.
            // Segments may come from an IP or from the cfDomain itself.
            host.matches(Regex("""^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$""")) ||
            (cfDomain.isNotBlank() && host.endsWith(cfDomain)) ||
            host.contains("virtualinfrastructure.space") -> {
                // Use cfDomain as referer when available, otherwise fall back to iframeUrl
                val cdnReferer = if (cfDomain.isNotBlank()) {
                    "https://$cfDomain/"
                } else {
                    cleanReferer(iframeUrl)
                }
                headers["Referer"] = cdnReferer
                headers["Origin"]  = cdnReferer.removeSuffix("/")
            }
        }

        val newSpec = dataSpec.buildUpon()
            .setHttpRequestHeaders(headers)
            .build()
        return baseDataSource.open(newSpec)
    }

    override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
        return baseDataSource.read(buffer, offset, length)
    }

    override fun getUri(): Uri? = baseDataSource.uri

    override fun close() {
        baseDataSource.close()
    }
}

class DynamicHeaderDataSourceFactory(
    private val baseFactory: DefaultHttpDataSource.Factory,
    private val iframeUrl: String,
    private val cfDomain: String
) : DataSource.Factory {
    override fun createDataSource(): DataSource {
        return DynamicHeaderDataSource(baseFactory.createDataSource(), iframeUrl, cfDomain)
    }
}
