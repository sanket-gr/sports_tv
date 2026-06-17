package com.sportstv.mobile.model

import com.google.gson.annotations.SerializedName

data class WatchTimeRequest(
    @SerializedName("stream_id") val streamId: Int,
    @SerializedName("duration_seconds") val durationSeconds: Int
)

data class WatchTimeResponse(
    val status: String,
    val recorded: Int
)
