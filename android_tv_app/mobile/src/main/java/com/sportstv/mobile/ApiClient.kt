package com.sportstv.mobile

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import retrofit2.http.Path
import com.sportstv.mobile.model.*
import retrofit2.http.POST
import retrofit2.http.Body
import retrofit2.http.Query
import java.util.concurrent.TimeUnit

// ─── Backend URL configuration ───────────────────────────────────────────────
// IMPORTANT: Change this to your backend's IP address.
// LOCAL TESTING: "http://192.168.100.104:8000/" (Your laptop's IP)
// PRODUCTION AWS: "http://13.126.62.185/" 
const val BASE_URL = "http://13.126.62.185/"

// ─── Retrofit interface ──────────────────────────────────────────────────────
interface SportsApiService {

    @GET("api/streams")
    suspend fun getStreams(
        @Query("live_only") liveOnly: Boolean = true,
    ): List<StreamItem>

    @GET("api/streams/{id}")
    suspend fun getStream(
        @Path("id") id: Int,
    ): StreamItem

    /** Triggers re-extraction on backend; returns current data. */
    @GET("api/streams/{id}/refresh")
    suspend fun refreshStream(
        @Path("id") id: Int,
    ): StreamItem

    /** Record watch time analytics */
    @POST("api/analytics/watch_time")
    suspend fun recordWatchTime(
        @Body request: WatchTimeRequest
    ): WatchTimeResponse
}

// ─── Singleton client ─────────────────────────────────────────────────────────
object ApiClient {
    private val logging = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BASIC
    }

    private val httpClient = OkHttpClient.Builder()
        .addInterceptor(logging)
        .connectTimeout(20, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .build()

    val service: SportsApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(httpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(SportsApiService::class.java)
    }
}
