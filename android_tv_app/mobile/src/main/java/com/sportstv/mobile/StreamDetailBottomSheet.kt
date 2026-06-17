package com.sportstv.mobile

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import com.bumptech.glide.Glide
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.sportstv.mobile.databinding.BottomSheetStreamDetailBinding
import com.sportstv.mobile.model.StreamItem

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

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
