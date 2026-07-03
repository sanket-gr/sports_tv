package com.sportstv.mobile.model

import com.google.gson.annotations.SerializedName

data class SportSrcMatch(
    @SerializedName("id")     val id: String,
    @SerializedName("title")  val title: String,
    @SerializedName("status") val status: String,
    @SerializedName("sport")  val sport: String,
    @SerializedName("date")   val date: String
)

data class SportSrcStream(
    @SerializedName("streamNo") val streamNo: Int,
    @SerializedName("language") val language: String,
    @SerializedName("hd")       val hd: Boolean,
    @SerializedName("embedUrl") val embedUrl: String,
    @SerializedName("source")   val source: String
)

data class SportSrcMatchDetail(
    @SerializedName("id")         val id: String,
    @SerializedName("title")      val title: String,
    @SerializedName("stream_url") val streamUrl: String?,
    @SerializedName("hls_url")    val hlsUrl: String?,
    @SerializedName("streams")    val streams: List<SportSrcStream>?
)

data class ResolveResponse(
    @SerializedName("hls_url") val hlsUrl: String?
)
