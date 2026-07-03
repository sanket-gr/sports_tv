package com.sportstv.mobile

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.lifecycle.lifecycleScope
import com.bumptech.glide.Glide
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.google.android.material.button.MaterialButton
import com.sportstv.mobile.databinding.BottomSheetStreamDetailBinding
import com.sportstv.mobile.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import android.graphics.Color

class StreamDetailBottomSheet : BottomSheetDialogFragment() {

    companion object {
        fun newInstance(stream: StreamItem): StreamDetailBottomSheet {
            return StreamDetailBottomSheet().apply {
                arguments = Bundle().apply {
                    putInt("id", stream.id)
                    putInt("category_id", stream.categoryId)
                    putString("category_name", stream.categoryName)
                    putString("title", stream.title)
                    putString("participants", stream.participants)
                    putString("hls_url", stream.hlsUrl)
                    putString("iframe_url", stream.iframeUrl)
                    putString("cf_domain", stream.cfDomain)
                    putString("thumbnail_url", stream.thumbnailUrl)
                    putBoolean("is_live", stream.isLive)
                }
            }
        }
    }

    private var _binding: BottomSheetStreamDetailBinding? = null
    private val binding get() = _binding!!

    private lateinit var stream: StreamItem
    var onFavoritesChangedListener: (() -> Unit)? = null
    private var selectedTab = "lineups"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val args = requireArguments()
        stream = StreamItem(
            id = args.getInt("id"),
            categoryId = args.getInt("category_id"),
            categoryName = args.getString("category_name") ?: "",
            categoryIcon = "",
            title = args.getString("title") ?: "",
            participants = args.getString("participants") ?: "",
            sport = "",
            hlsUrl = args.getString("hls_url") ?: "",
            iframeUrl = args.getString("iframe_url") ?: "",
            cfDomain = args.getString("cf_domain") ?: "",
            thumbnailUrl = args.getString("thumbnail_url") ?: "",
            isLive = args.getBoolean("is_live")
        )
    }

    override fun onCreateView(
        LayoutInflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = BottomSheetStreamDetailBinding.inflate(LayoutInflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.tvDetailTitle.text = if (stream.participants.isNotBlank()) stream.participants else stream.title
        binding.tvDetailCategory.text = stream.categoryName
        binding.tvDetailLiveBadge.visibility = if (stream.isLive) View.VISIBLE else View.GONE

        // Load thumbnail image using Glide
        Glide.with(this)
            .load(stream.thumbnailUrl)
            .placeholder(android.R.drawable.ic_menu_gallery)
            .error(android.R.drawable.ic_menu_gallery)
            .into(binding.ivDetailThumbnail)

        // Read and display favorite state
        var isFav = FavoritesManager.isFavorite(requireContext(), stream.id)
        updateFavoriteButtonState(isFav)

        // Favorite Toggle action
        binding.btnDetailFavorite.setOnClickListener {
            isFav = FavoritesManager.toggleFavorite(requireContext(), stream.id)
            updateFavoriteButtonState(isFav)
            onFavoritesChangedListener?.invoke()
        }

        // Play action
        binding.btnDetailWatch.setOnClickListener {
            PlaybackActivity.start(requireContext(), stream)
            dismiss()
        }

        // Setup SportSRC Deep Data Tabs
        setupMatchCenterTabs()
    }

    private fun updateFavoriteButtonState(isFavorite: Boolean) {
        if (isFavorite) {
            binding.btnDetailFavorite.text = "Favorited"
            binding.btnDetailFavorite.setIconResource(R.drawable.ic_star)
            binding.btnDetailFavorite.setIconTintResource(R.color.yellow_star)
            binding.btnDetailFavorite.setTextColor(0xFFFBBF24.toInt())
        } else {
            binding.btnDetailFavorite.text = "Add Favorite"
            binding.btnDetailFavorite.setIconResource(R.drawable.ic_star_border)
            binding.btnDetailFavorite.setIconTintResource(R.color.gray_outline)
            binding.btnDetailFavorite.setTextColor(0xFF64748B.toInt())
        }
    }

    private fun setupMatchCenterTabs() {
        val matchId = if (stream.title.contains("vs", ignoreCase = true)) {
            stream.title.replace(" ", "-").lowercase() + "-101"
        } else {
            "arsenal-vs-chelsea-101"
        }

        // Default tab selection
        loadTabContent("lineups", matchId)

        binding.btnTabLineups.setOnClickListener { loadTabContent("lineups", matchId) }
        binding.btnTabStats.setOnClickListener { loadTabContent("stats", matchId) }
        binding.btnTabTimeline.setOnClickListener { loadTabContent("timeline", matchId) }
        binding.btnTabOdds.setOnClickListener { loadTabContent("odds", matchId) }
        binding.btnTabVotes.setOnClickListener { loadTabContent("votes", matchId) }
    }

    private fun updateTabStyles(activeTab: String) {
        selectedTab = activeTab
        val activeColor = 0xFF3B82F6.toInt() // Neon Blue / Active Blue
        val inactiveColor = 0xFF94A3B8.toInt() // Slate grey

        binding.btnTabLineups.setTextColor(if (activeTab == "lineups") activeColor else inactiveColor)
        binding.btnTabStats.setTextColor(if (activeTab == "stats") activeColor else inactiveColor)
        binding.btnTabTimeline.setTextColor(if (activeTab == "timeline") activeColor else inactiveColor)
        binding.btnTabOdds.setTextColor(if (activeTab == "odds") activeColor else inactiveColor)
        binding.btnTabVotes.setTextColor(if (activeTab == "votes") activeColor else inactiveColor)
    }

    private fun loadTabContent(tab: String, matchId: String) {
        updateTabStyles(tab)
        binding.tvMatchCenter_display.text = "Fetching data from SportSRC..."

        lifecycleScope.launch {
            try {
                when (tab) {
                    "lineups" -> {
                        val lineups = withContext(Dispatchers.IO) {
                            ApiClient.service.getSportSrcLineups(matchId)
                        }
                        renderLineups(lineups)
                    }
                    "stats" -> {
                        val stats = withContext(Dispatchers.IO) {
                            ApiClient.service.getSportSrcStats(matchId)
                        }
                        renderStats(stats)
                    }
                    "timeline" -> {
                        val incidents = withContext(Dispatchers.IO) {
                            ApiClient.service.getSportSrcIncidents(matchId)
                        }
                        renderTimeline(incidents)
                    }
                    "odds" -> {
                        val odds = withContext(Dispatchers.IO) {
                            ApiClient.service.getSportSrcOdds(matchId)
                        }
                        renderOdds(odds)
                    }
                    "votes" -> {
                        val votes = withContext(Dispatchers.IO) {
                            ApiClient.service.getSportSrcVotes(matchId)
                        }
                        renderPredictions(votes)
                    }
                }
            } catch (e: Exception) {
                binding.tvMatchCenter_display.text = "Data unavailable for this match.\nDetails: ${e.localizedMessage}"
            }
        }
    }

    private fun renderLineups(lineups: MatchLineups) {
        val sb = StringBuilder()
        sb.append("📋 HOME Formation: ${lineups.home.formation}\n")
        lineups.home.players.forEach { sb.append("  • ${it.name}\n") }
        sb.append("\n📋 AWAY Formation: ${lineups.away.formation}\n")
        lineups.away.players.forEach { sb.append("  • ${it.name}\n") }
        binding.tvMatchCenter_display.text = sb.toString()
    }

    private fun renderStats(stats: MatchStats) {
        val sb = StringBuilder()
        sb.append("📈 Live Match Stats:\n\n")
        stats.possession?.let { sb.append("⚽ Possession: Home ${it.home} - Away ${it.away}\n") }
        stats.shots?.let { sb.append("🎯 Total Shots: Home ${it.home} - Away ${it.away}\n") }
        stats.xG?.let { sb.append("📊 Expected Goals (xG): Home ${it.home} - Away ${it.away}\n") }
        stats.shotsOnTarget?.let { sb.append("🥅 Shots On Target: Home ${it.home} - Away ${it.away}\n") }
        stats.fouls?.let { sb.append("⚠️ Fouls: Home ${it.home} - Away ${it.away}\n") }
        stats.corners?.let { sb.append("🚩 Corners: Home ${it.home} - Away ${it.away}\n") }
        binding.tvMatchCenter_display.text = sb.toString()
    }

    private fun renderTimeline(incidents: List<IncidentItem>) {
        if (incidents.isEmpty()) {
            binding.tvMatchCenter_display.text = "No live incidents recorded yet."
            return
        }
        val sb = StringBuilder()
        sb.append("⏰ Match Events Timeline:\n\n")
        incidents.forEach {
            val emoji = when (it.type.lowercase()) {
                "goal" -> "⚽ GOAL!"
                "card" -> "🟨 Card"
                "substitution" -> "🔄 Subs"
                else -> "📢 Event"
            }
            sb.append("${it.time} - $emoji: ${it.player} (${it.team.uppercase()}) ${it.detail}\n")
        }
        binding.tvMatchCenter_display.text = sb.toString()
    }

    private fun renderOdds(odds: MatchOdds) {
        val sb = StringBuilder()
        sb.append("🎲 Betting Odds (via ${odds.bookmaker}):\n\n")
        sb.append("💵 Decimal Format:\n")
        sb.append("  • Home: ${odds.decimal.home}\n")
        sb.append("  • Draw: ${odds.decimal.draw}\n")
        sb.append("  • Away: ${odds.decimal.away}\n\n")
        sb.append("💵 Fractional Format:\n")
        sb.append("  • Home: ${odds.fractional.home}\n")
        sb.append("  • Draw: ${odds.fractional.draw}\n")
        sb.append("  • Away: ${odds.fractional.away}\n")
        binding.tvMatchCenter_display.text = sb.toString()
    }

    private fun renderPredictions(votes: MatchVotes) {
        val sb = StringBuilder()
        sb.append("🗳️ Fan Predictions & Sentiment:\n\n")
        sb.append("🏆 Who will win?\n")
        sb.append("  • Home Win: ${votes.winner.home}\n")
        sb.append("  • Draw: ${votes.winner.draw}\n")
        sb.append("  • Away Win: ${votes.winner.away}\n\n")
        sb.append("🥅 Both Teams to Score (BTTS):\n")
        sb.append("  • Yes: ${votes.btts.yes}\n")
        sb.append("  • No: ${votes.btts.no}\n")
        binding.tvMatchCenter_display.text = sb.toString()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
