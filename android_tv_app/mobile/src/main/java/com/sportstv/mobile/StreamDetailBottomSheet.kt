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

        // Setup Stream Servers
        setupStreamServers()
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

    private fun setupStreamServers() {
        if (!stream.hlsUrl.startsWith("sportsrc://")) {
            binding.layoutServersContainer.visibility = View.GONE
            return
        }

        binding.layoutServersContainer.visibility = View.VISIBLE
        binding.tvServersHint.text = "Fetching available servers..."
        val matchId = stream.hlsUrl.removePrefix("sportsrc://")

        lifecycleScope.launch {
            try {
                val detail = withContext(Dispatchers.IO) {
                    ApiClient.service.getSportSrcDetail(matchId)
                }
                
                val streams = detail.streams
                if (streams.isNullOrEmpty()) {
                    binding.tvServersHint.text = "No stream servers available yet."
                    return@launch
                }
                
                binding.tvServersHint.text = "Select a server to switch stream quality"
                binding.layoutServerList.removeAllViews()
                
                streams.forEach { streamServer ->
                    val btn = MaterialButton(requireContext(), null, com.google.android.material.R.attr.borderlessButtonStyle).apply {
                        text = "Server ${streamServer.streamNo} ${if (streamServer.hd) "(HD)" else ""}"
                        setTextColor(if (streamServer.hd) Color.parseColor("#14B8A6") else Color.parseColor("#94A3B8"))
                        isAllCaps = false
                        setOnClickListener {
                            playSelectedServer(streamServer)
                        }
                    }
                    binding.layoutServerList.addView(btn)
                }
            } catch (e: Exception) {
                binding.tvServersHint.text = "Failed to load servers: ${e.localizedMessage}"
            }
        }
    }

    private fun playSelectedServer(streamServer: SportSrcStream) {
        _binding?.tvServersHint?.text = "Resolving stream, please wait..."
        val ctx = context ?: return
        lifecycleScope.launch {
            try {
                val response = withContext(Dispatchers.IO) {
                    ApiClient.service.resolveStream(streamServer.embedUrl)
                }
                val realHls = response.hlsUrl ?: ""
                if (realHls.isNotBlank()) {
                    val proxiedUrl = if (realHls.startsWith("http")) {
                        val serverBase = BASE_URL
                        val encodedUrl = android.net.Uri.encode(realHls)
                        val encodedReferer = android.net.Uri.encode(streamServer.embedUrl)
                        "${serverBase}api/proxy?url=$encodedUrl&referer=$encodedReferer"
                    } else {
                        realHls
                    }
                    
                    val updatedStream = stream.copy(
                        hlsUrl = proxiedUrl,
                        iframeUrl = streamServer.embedUrl,
                        cfDomain = try { android.net.Uri.parse(realHls).host ?: "" } catch(e: Exception) { "" }
                    )
                    if (isAdded) {
                        PlaybackActivity.start(ctx, updatedStream)
                        dismiss()
                    }
                } else {
                    _binding?.tvServersHint?.text = "Failed to resolve stream link."
                }
            } catch (e: Exception) {
                _binding?.tvServersHint?.text = "Error resolving stream: ${e.localizedMessage}"
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
