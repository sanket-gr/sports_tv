package com.sportstv.mobile.model

import com.google.gson.annotations.SerializedName

// ─── Lineups Models ──────────────────────────────────────────────────────────
data class PlayerItem(
    @SerializedName("name")  val name: String,
    @SerializedName("photo") val photo: String
)

data class TeamLineup(
    @SerializedName("formation") val formation: String,
    @SerializedName("players")   val players: List<PlayerItem>
)

data class MatchLineups(
    @SerializedName("home") val home: TeamLineup,
    @SerializedName("away") val away: TeamLineup
)

// ─── Stats Models ─────────────────────────────────────────────────────────────
data class StatValue(
    @SerializedName("home") val home: String,
    @SerializedName("away") val away: String
)

data class MatchStats(
    @SerializedName("possession")      val possession: StatValue?,
    @SerializedName("shots")           val shots: StatValue?,
    @SerializedName("xG")              val xG: StatValue?,
    @SerializedName("shots_on_target") val shotsOnTarget: StatValue?,
    @SerializedName("fouls")           val fouls: StatValue?,
    @SerializedName("corners")         val corners: StatValue?
)

// ─── Incidents Models ─────────────────────────────────────────────────────────
data class IncidentItem(
    @SerializedName("time")   val time: String,
    @SerializedName("type")   val type: String, // goal, card, substitution, etc.
    @SerializedName("player") val player: String,
    @SerializedName("detail") val detail: String = "",
    @SerializedName("team")   val team: String // home or away
)

// ─── Odds Models ──────────────────────────────────────────────────────────────
data class OddsValues(
    @SerializedName("home") val home: Double,
    @SerializedName("draw") val draw: Double,
    @SerializedName("away") val away: Double
)

data class OddsFractional(
    @SerializedName("home") val home: String,
    @SerializedName("draw") val draw: String,
    @SerializedName("away") val away: String
)

data class MatchOdds(
    @SerializedName("bookmaker")  val bookmaker: String,
    @SerializedName("decimal")    val decimal: OddsValues,
    @SerializedName("fractional") val fractional: OddsFractional
)

// ─── Predictions (Votes) Models ──────────────────────────────────────────────
data class VoteRatio(
    @SerializedName("home") val home: String,
    @SerializedName("draw") val draw: String,
    @SerializedName("away") val away: String
)

data class BttsRatio(
    @SerializedName("yes") val yes: String,
    @SerializedName("no")  val no: String
)

data class MatchVotes(
    @SerializedName("winner") val winner: VoteRatio,
    @SerializedName("btts")   val btts: BttsRatio
)
