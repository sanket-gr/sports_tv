package com.sportstv.mobile

import android.content.Context
import android.content.Intent
import android.content.res.Configuration
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.view.View
import android.view.WindowManager
import android.widget.SeekBar
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.lifecycle.lifecycleScope
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.datasource.DataSource
import androidx.media3.datasource.DataSpec
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.datasource.TransferListener
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.hls.HlsMediaSource
import androidx.media3.ui.AspectRatioFrameLayout
import com.sportstv.mobile.databinding.ActivityPlaybackBinding
import com.sportstv.mobile.model.StreamItem
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import androidx.media3.datasource.okhttp.OkHttpDataSource

class PlaybackActivity : AppCompatActivity() {

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

        fun startWithId(context: Context, streamId: Int) {
            val intent = Intent(context, PlaybackActivity::class.java).apply {
                putExtra("stream_id", streamId)
            }
            context.startActivity(intent)
        }
    }

    private lateinit var binding: ActivityPlaybackBinding
    private var player: ExoPlayer? = null
    private var errorCountdownJob: Job? = null

    private var streamId: Int = -1
    private var hlsUrl: String = ""
    private var iframeUrl: String = ""
    private var cfDomain: String = ""

    private var watchSessionStartTime: Long = 0L

    private val resizeModes = listOf(
        AspectRatioFrameLayout.RESIZE_MODE_FIT,
        AspectRatioFrameLayout.RESIZE_MODE_FILL,
        AspectRatioFrameLayout.RESIZE_MODE_ZOOM
    )
    private val modeNames = listOf("Fit", "Fill", "Zoom")
    private var currentModeIndex = 0

    private val hideControlsRunnable = Runnable {
        binding.controlsContainer.animate().alpha(0f).setDuration(300).withEndAction {
            binding.controlsContainer.visibility = View.GONE
        }.start()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Keep the screen on during video playback to prevent screen dimming/sleep mode
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        
        binding = ActivityPlaybackBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Grab stream info from Intent
        hlsUrl       = intent.getStringExtra("hls_url") ?: ""
        streamId     = intent.getIntExtra("stream_id", -1)
        iframeUrl    = intent.getStringExtra("iframe_url") ?: ""
        cfDomain     = intent.getStringExtra("cf_domain") ?: ""
        val title        = intent.getStringExtra("title") ?: ""
        val participants = intent.getStringExtra("participants") ?: ""

        binding.tvTitle.text = if (participants.isNotBlank()) participants else title

        // ── Controls UI Setup ───────────────────────────────────────────────
        binding.btnBack.setOnClickListener {
            finish()
        }

        binding.btnPlayPause.setOnClickListener {
            player?.let {
                if (it.isPlaying) {
                    it.pause()
                    binding.btnPlayPause.setImageResource(R.drawable.ic_play)
                } else {
                    it.play()
                    binding.btnPlayPause.setImageResource(R.drawable.ic_pause)
                }
                showControls() // Reschedule auto-hide
            }
        }

        binding.btnRatio.setOnClickListener {
            currentModeIndex = (currentModeIndex + 1) % resizeModes.size
            binding.playerView.resizeMode = resizeModes[currentModeIndex]
            Toast.makeText(this, "Aspect Ratio: ${modeNames[currentModeIndex]}", Toast.LENGTH_SHORT).show()
            showControls() // Reschedule auto-hide
        }

        binding.sbVolume.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                if (fromUser) {
                    val vol = progress / 100f
                    player?.volume = vol
                    showControls() // Reschedule auto-hide
                }
            }
            override fun onStartTrackingTouch(seekBar: SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: SeekBar?) {}
        })

        // Overlay touch behavior
        binding.playerView.setOnClickListener {
            toggleControls()
        }
        binding.controlsContainer.setOnClickListener {
            toggleControls()
        }

        binding.btnRetry.setOnClickListener {
            refreshAndPlay()
        }

        // Adjust screen mode based on initial orientation
        adjustScreenMode(resources.configuration.orientation)

        // Start playback
        val isProxied = hlsUrl.contains("/api/proxy")
        if (hlsUrl.isNotBlank() && isProxied) {
            initPlayer(hlsUrl)
        } else {
            refreshAndPlay()
        }

        // Schedule initial hide of controls
        showControls()
    }

    private fun showControls() {
        binding.controlsContainer.animate().cancel()
        binding.controlsContainer.alpha = 1f
        binding.controlsContainer.visibility = View.VISIBLE
        
        binding.controlsContainer.removeCallbacks(hideControlsRunnable)
        binding.controlsContainer.postDelayed(hideControlsRunnable, 3500)
    }

    private fun toggleControls() {
        if (binding.controlsContainer.visibility == View.VISIBLE) {
            binding.controlsContainer.animate().alpha(0f).setDuration(300).withEndAction {
                binding.controlsContainer.visibility = View.GONE
            }.start()
        } else {
            showControls()
        }
    }

    private fun adjustScreenMode(orientation: Int) {
        val windowInsetsController = WindowCompat.getInsetsController(window, window.decorView)
        if (orientation == Configuration.ORIENTATION_LANDSCAPE) {
            windowInsetsController.hide(WindowInsetsCompat.Type.statusBars() or WindowInsetsCompat.Type.navigationBars())
            windowInsetsController.systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        } else {
            windowInsetsController.show(WindowInsetsCompat.Type.statusBars() or WindowInsetsCompat.Type.navigationBars())
        }
    }

    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        adjustScreenMode(newConfig.orientation)
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

    private fun initPlayer(url: String) {
        Log.d(TAG, "initPlayer url=$url iframeUrl=$iframeUrl cfDomain=$cfDomain")

        releasePlayer()
        showLoading(true)
        showError(false)
        
        watchSessionStartTime = System.currentTimeMillis()

        val referer = cleanReferer(iframeUrl)
        val baseHttpDataSourceFactory = OkHttpDataSource.Factory(getSecureOkHttpClient())
            .setUserAgent("Mozilla/5.0 (Linux; Android 11; TV) AppleWebKit/537.36 Chrome/119 Safari/537.36")
            .setDefaultRequestProperties(
                mapOf(
                    "Referer"         to referer,
                    "Origin"          to Uri.parse(referer).let { "${it.scheme}://${it.host}" },
                    "Accept"          to "*/*",
                    "Accept-Language" to "en-US,en;q=0.9",
                )
            )

        val dataSourceFactory = DynamicHeaderDataSourceFactory(
            baseHttpDataSourceFactory,
            iframeUrl,
            cfDomain
        )

        player = ExoPlayer.Builder(this).build().also { exo ->
            binding.playerView.player = exo

            // Set seekbar matching current player volume
            binding.sbVolume.progress = (exo.volume * 100).toInt()

            val mediaItem = MediaItem.Builder()
                .setUri(Uri.parse(url))
                .setMimeType("application/x-mpegURL")
                .build()
            val hlsSource = HlsMediaSource.Factory(dataSourceFactory)
                .createMediaSource(mediaItem)

            exo.addListener(object : Player.Listener {
                override fun onIsLoadingChanged(isLoading: Boolean) {
                    if (!isLoading && exo.playbackState == Player.STATE_READY) {
                        showLoading(false)
                    }
                }

                override fun onPlaybackStateChanged(state: Int) {
                    when (state) {
                        Player.STATE_READY     -> {
                            showLoading(false)
                            binding.btnPlayPause.setImageResource(R.drawable.ic_pause)
                        }
                        Player.STATE_BUFFERING -> showLoading(true)
                        Player.STATE_ENDED     -> finish()
                        else -> {}
                    }
                }

                override fun onPlayerError(error: PlaybackException) {
                    Log.e(TAG, "Player error code=${error.errorCode} msg=${error.message}", error)
                    showLoading(false)
                    val msg = error.message ?: ""
                    when {
                        msg.contains("404") || msg.contains("403") -> {
                            Log.d(TAG, "Stream token expired, auto-refreshing...")
                            refreshAndPlay()
                        }
                        msg.contains("Unable to connect") ||
                        msg.contains("Failed to connect") ||
                        msg.contains("UnknownHostException") -> {
                            showError(true, "Cannot reach stream server.\nCheck your network and tap Retry.", 5)
                        }
                        else -> {
                            showError(true, "Playback error (${error.errorCode}): $msg\n\nTap Retry to try again.", 5)
                        }
                    }
                }
            })

            exo.setMediaSource(hlsSource)
            exo.prepare()
            exo.playWhenReady = true
        }
    }

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
                Log.d(TAG, "Triggering re-extraction for stream $streamId")
                ApiClient.service.refreshStream(streamId)

                var freshUrl  = ""
                var freshCfDomain = ""
                var freshTitle = ""
                var freshParticipants = ""
                repeat(4) { attempt ->
                    if (freshUrl.isNotBlank()) return@repeat
                    delay(5_000)
                    Log.d(TAG, "Polling for fresh URL (attempt ${attempt + 1}/4)...")
                    val stream = ApiClient.service.getStream(streamId)
                    if (stream.hlsUrl.isNotBlank() && stream.hlsUrl != hlsUrl) {
                        freshUrl      = stream.hlsUrl
                        iframeUrl     = stream.iframeUrl
                        freshCfDomain = stream.cfDomain
                        freshTitle    = stream.title
                        freshParticipants = stream.participants
                    }
                }

                if (freshUrl.isBlank()) {
                    val stream = ApiClient.service.getStream(streamId)
                    freshUrl      = stream.hlsUrl
                    iframeUrl     = stream.iframeUrl
                    freshCfDomain = stream.cfDomain
                    freshTitle    = stream.title
                    freshParticipants = stream.participants
                }

                if (freshUrl.isBlank()) {
                    showLoading(false)
                    showError(true, "Could not get a fresh stream link.\nThe event may have ended.\nTap Retry to try again.")
                } else {
                    hlsUrl   = freshUrl
                    cfDomain = freshCfDomain
                    binding.tvTitle.text = if (freshParticipants.isNotBlank()) freshParticipants else freshTitle
                    initPlayer(freshUrl)
                }
            } catch (e: Exception) {
                Log.e(TAG, "refreshAndPlay error", e)
                showLoading(false)
                showError(true, "Could not reach the backend server.\n${e.localizedMessage}\n\nMake sure the server is running and tap Retry.")
            }
        }
    }

    private fun showLoading(show: Boolean) {
        binding.loadingView.visibility = if (show) View.VISIBLE else View.GONE
    }

    private fun showError(show: Boolean, msg: String = "", autoRetryDelay: Int = 0) {
        errorCountdownJob?.cancel()
        binding.errorView.visibility = if (show) View.VISIBLE else View.GONE
        
        if (show) {
            if (msg.isNotEmpty()) binding.tvError.text = msg
            
            if (autoRetryDelay > 0) {
                errorCountdownJob = lifecycleScope.launch {
                    for (i in autoRetryDelay downTo 1) {
                        binding.tvError.text = "$msg\n\nRetrying in $i..."
                        delay(1000)
                    }
                    binding.tvError.text = "Retrying now..."
                    refreshAndPlay()
                }
            }
        }
    }

    private fun releasePlayer() {
        if (watchSessionStartTime > 0L && streamId >= 0) {
            val durationMs = System.currentTimeMillis() - watchSessionStartTime
            val durationSec = (durationMs / 1000).toInt()
            if (durationSec > 0) {
                val currentStreamId = streamId
                lifecycleScope.launch(kotlinx.coroutines.Dispatchers.IO) {
                    try {
                        ApiClient.service.recordWatchTime(
                            com.sportstv.mobile.model.WatchTimeRequest(currentStreamId, durationSec)
                        )
                        Log.d(TAG, "Recorded watch time: $durationSec seconds for stream $currentStreamId")
                    } catch (e: Exception) {
                        Log.e(TAG, "Failed to record watch time", e)
                    }
                }
            }
            watchSessionStartTime = 0L
        }
        player?.release()
        player = null
    }

    override fun onStop() {
        super.onStop()
        player?.pause()
    }

    override fun onDestroy() {
        super.onDestroy()
        releasePlayer()
    }

    private fun getSecureOkHttpClient(): OkHttpClient {
        return OkHttpClient.Builder()
            .connectTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
            .build()
    }
}

// ─── Custom DataSource classes for dynamic headers ─────────────────────────

class DynamicHeaderDataSource(
    private val baseDataSource: androidx.media3.datasource.HttpDataSource,
    private val iframeUrl: String,
    private val cfDomain: String
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
            host.matches(Regex("""^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$""")) ||
            (cfDomain.isNotBlank() && host.endsWith(cfDomain)) ||
            host.contains("virtualinfrastructure.space") -> {
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
    private val baseFactory: androidx.media3.datasource.HttpDataSource.Factory,
    private val iframeUrl: String,
    private val cfDomain: String
) : DataSource.Factory {
    override fun createDataSource(): DataSource {
        return DynamicHeaderDataSource(baseFactory.createDataSource(), iframeUrl, cfDomain)
    }
}
