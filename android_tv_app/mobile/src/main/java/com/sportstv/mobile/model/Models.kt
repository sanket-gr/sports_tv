package com.sportstv.mobile.model

import com.google.gson.annotations.SerializedName

// ─── API response models ────────────────────────────────────────────────────

data class StreamItem(
    @SerializedName("id")            val id: Int,
    @SerializedName("category_id")   val categoryId: Int,
    @SerializedName("category_name") val categoryName: String,
    @SerializedName("category_icon") val categoryIcon: String,
    @SerializedName("title")         val title: String,
    @SerializedName("participants")  val participants: String,
    @SerializedName("sport")         val sport: String,
    @SerializedName("hls_url")       val hlsUrl: String,
    @SerializedName("iframe_url")    val iframeUrl: String = "",
    @SerializedName("cf_domain")     val cfDomain: String = "",
    @SerializedName("thumbnail_url") val thumbnailUrl: String,
    @SerializedName("is_live")       val isLive: Boolean,
)
