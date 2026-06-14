package com.sportstv.app

import android.content.Context
import android.graphics.Color
import android.view.LayoutInflater
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.leanback.widget.Presenter
import com.bumptech.glide.Glide
import com.bumptech.glide.load.resource.drawable.DrawableTransitionOptions

/**
 * CardPresenter renders a single match/stream as a TV card in the Leanback browse grid.
 */
class CardPresenter : Presenter() {

    override fun onCreateViewHolder(parent: ViewGroup): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_stream_card, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(viewHolder: ViewHolder, item: Any) {
        val stream = item as StreamItem
        val view = viewHolder.view

        val tvTitle    = view.findViewById<TextView>(R.id.tv_title)
        val tvSub      = view.findViewById<TextView>(R.id.tv_subtitle)
        val tvBadge    = view.findViewById<TextView>(R.id.tv_live_badge)
        val ivThumb    = view.findViewById<ImageView>(R.id.iv_thumbnail)

        tvTitle.text = if (stream.participants.isNotBlank()) stream.participants else stream.title
        tvSub.text   = if (stream.participants.isNotBlank()) stream.title else stream.categoryName
        tvBadge.text = if (stream.isLive) "● LIVE" else "OFFLINE"
        tvBadge.setTextColor(if (stream.isLive) Color.parseColor("#22c55e") else Color.parseColor("#64748b"))

        if (stream.thumbnailUrl.isNotBlank()) {
            Glide.with(view.context)
                .load(stream.thumbnailUrl)
                .transition(DrawableTransitionOptions.withCrossFade())
                .placeholder(R.drawable.placeholder_card)
                .into(ivThumb)
        } else {
            ivThumb.setImageResource(R.drawable.placeholder_card)
        }
    }

    override fun onUnbindViewHolder(viewHolder: ViewHolder) {
        val ivThumb = viewHolder.view.findViewById<ImageView>(R.id.iv_thumbnail)
        Glide.with(viewHolder.view.context).clear(ivThumb)
    }
}
