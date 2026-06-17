package com.sportstv.mobile

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.bumptech.glide.Glide
import com.sportstv.mobile.databinding.ItemStreamCardBinding
import com.sportstv.mobile.model.StreamItem

class StreamAdapter(
    private var streams: List<StreamItem>,
    private val onItemClick: (StreamItem) -> Unit
) : RecyclerView.Adapter<StreamAdapter.StreamViewHolder>() {

    fun updateData(newStreams: List<StreamItem>) {
        this.streams = newStreams
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): StreamViewHolder {
        val binding = ItemStreamCardBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return StreamViewHolder(binding)
    }

    override fun onBindViewHolder(holder: StreamViewHolder, position: Int) {
        holder.bind(streams[position])
    }

    override fun getItemCount(): Int = streams.size

    inner class StreamViewHolder(
        private val binding: ItemStreamCardBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(stream: StreamItem) {
            binding.tvTitle.text = stream.title
            binding.tvCategory.text = stream.categoryName
            binding.tvLiveBadge.visibility = if (stream.isLive) View.VISIBLE else View.GONE

            // Show favorite star indicator if favorited
            val isFavorite = FavoritesManager.isFavorite(itemView.context, stream.id)
            binding.tvFavoriteStar.visibility = if (isFavorite) View.VISIBLE else View.GONE

            // Glide thumbnail loading with default android icon as placeholder
            Glide.with(itemView.context)
                .load(stream.thumbnailUrl)
                .placeholder(android.R.drawable.ic_menu_gallery)
                .error(android.R.drawable.ic_menu_gallery)
                .into(binding.ivThumbnail)

            itemView.setOnClickListener {
                onItemClick(stream)
            }
        }
    }
}
