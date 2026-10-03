package de.konformitaetshelfer.daten

import android.content.Context
import androidx.sqlite.SQLiteConnection
import androidx.sqlite.SQLiteStatement
import androidx.sqlite.driver.bundled.SQLITE_OPEN_READONLY
import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/**
 * Der Rechtsbestand auf dem Gerät.
 *
 * Geöffnet wird mit dem MITGELIEFERTEN SQLite, nicht mit dem des Telefons.
 * Nachgemessen am 2026-10-03 an androidx.sqlite:sqlite-bundled-android:2.7.1:
 * dort sind FTS5, der Zerteiler unicode61 und remove_diacritics=2 eingebaut.
 * Das SQLite des Telefons hat FTS5 je nach Android-Fassung nicht - die
 * Stichwortsuche fiele dann aus, und zwar still, was schlimmer wäre.
 *
 * Geöffnet wird NUR LESEND. Die Datenbank ist fertig; die App hat keinen
 * Grund, daran zu schreiben, und mit dem Nur-Lese-Zeichen kann sie es auch
 * durch einen Fehler nicht.
 */
class Rechtsbestand private constructor(private val verbindung: SQLiteConnection) {

    companion object {
        private val json = Json { ignoreUnknownKeys = true }

        fun oeffnen(kontext: Context): Rechtsbestand {
            val datei = Beigaben.herauslegen(kontext, "recht.db")
            val fahrer = BundledSQLiteDriver()
            return Rechtsbestand(
                fahrer.open(datei.absolutePath, SQLITE_OPEN_READONLY)
            )
        }

        /** JSON-Spalte zu einer Liste von Zeichenfolgen. */
        internal fun textListe(roh: String): List<String> =
            if (roh.isBlank()) emptyList()
            else runCatching {
                json.parseToJsonElement(roh).jsonArray.map { it.jsonPrimitive.content }
            }.getOrDefault(emptyList())

        /**
         * JSON-Spalte zu einer Karte, deren Werte roher JSON-Text bleiben.
         *
         * Die Spalte zusatz enthält je Regel verschiedenes - einmal eine
         * Liste von Stufen, einmal ein Textstück. Es in ein festes Muster zu
         * zwingen hieße, für jede Regelart eine eigene Klasse zu bauen, von
         * der die Oberfläche am Ende nur einen Satz anzeigt.
         */
        internal fun rohKarte(roh: String): Map<String, String> =
            if (roh.isBlank()) emptyMap()
            else runCatching {
                json.parseToJsonElement(roh).jsonObject.mapValues { (_, wert) ->
                    if (wert is kotlinx.serialization.json.JsonPrimitive && wert.isString) {
                        wert.content
                    } else {
                        wert.toString()
                    }
                }
            }.getOrDefault(emptyMap())

        internal fun bedingungen(roh: String): List<Bedingung> =
            if (roh.isBlank()) emptyList()
            else runCatching {
                json.parseToJsonElement(roh).jsonArray.map { eintrag ->
                    val o = eintrag.jsonObject
                    Bedingung(
                        feld = o["feld"]?.jsonPrimitive?.content.orEmpty(),
                        ist = o["ist"]?.jsonPrimitive?.content?.toBoolean() ?: true,
                    )
                }.filter { it.feld.isNotEmpty() }
            }.getOrDefault(emptyList())
    }

    // ------------------------------------------------------------ Grundzüge

    /**
     * Führt eine Abfrage aus und liest jede Zeile mit [lesen].
     *
     * Die Anweisung wird in jedem Fall geschlossen. Eine offen gelassene
     * Anweisung hält in SQLite eine Lesesperre und einen Speicherblock.
     */
    private fun <T> abfragen(
        sql: String,
        binden: (SQLiteStatement) -> Unit = {},
        lesen: (SQLiteStatement) -> T,
    ): List<T> {
        val anweisung = verbindung.prepare(sql)
        try {
            binden(anweisung)
            val ergebnis = ArrayList<T>()
            while (anweisung.step()) {
                ergebnis.add(lesen(anweisung))
            }
            return ergebnis
        } finally {
            anweisung.close()
        }
    }

    fun schliessen() = verbindung.close()

    // ------------------------------------------------------------- Einheiten

    private fun einheitAus(a: SQLiteStatement) = Einheit(
        nummer = a.getInt(0),
        kennung = a.getText(1),
        rechtsakt = a.getText(2),
        art = a.getText(3),
        nummerImAkt = a.getText(4),
        absatz = if (a.isNull(5)) null else a.getText(5),
        titel = a.getText(6),
        text = a.getText(7),
        fundstelle = a.getText(8),
        quelle = a.getText(9),
    )

    private val einheitSpalten =
        "nummer, kennung, rechtsakt, art, nummer_im_akt, absatz, titel, text, fundstelle, quelle"

    fun einheitNachKennung(kennung: String): Einheit? = abfragen(
        "SELECT $einheitSpalten FROM einheit WHERE kennung = ?",
        binden = { it.bindText(1, kennung) },
        lesen = ::einheitAus,
    ).firstOrNull()

    fun einheitenNachNummern(nummern: List<Int>): Map<Int, Einheit> {
        if (nummern.isEmpty()) return emptyMap()
        val platzhalter = nummern.joinToString(",") { "?" }
        return abfragen(
            "SELECT $einheitSpalten FROM einheit WHERE nummer IN ($platzhalter)",
            binden = { a -> nummern.forEachIndexed { i, n -> a.bindLong(i + 1, n.toLong()) } },
            lesen = ::einheitAus,
        ).associateBy { it.nummer }
    }

    fun anzahlEinheiten(): Int =
        abfragen("SELECT count(*) FROM einheit") { it.getInt(0) }.firstOrNull() ?: 0

    /**
     * Stichwortsuche über FTS5.
     *
     * [abfrage] muss eine fertige FTS5-Abfrage sein; sie wird in
     * [de.konformitaetshelfer.suche.Stichwortabfrage] gebaut und dort auch
     * entschärft. Die Reihenfolge macht bm25: der Wert ist negativ, je
     * kleiner, desto besser.
     */
    fun stichwortsuche(abfrage: String, anzahl: Int): List<Int> = abfragen(
        """
        SELECT einheit_fts.rowid
        FROM einheit_fts
        WHERE einheit_fts MATCH ?
        ORDER BY bm25(einheit_fts, 2.0, 1.0)
        LIMIT ?
        """.trimIndent(),
        binden = { a ->
            a.bindText(1, abfrage)
            a.bindLong(2, anzahl.toLong())
        },
        lesen = { it.getInt(0) },
    )

    // -------------------------------------------------------------- Vektoren

    /**
     * Lädt alle Vektoren in einen Block.
     *
     * Ein zusammenhängender FloatArray statt 1972 einzelner: der Vergleich
     * läuft dann über fortlaufenden Speicher, und das ist der Unterschied
     * zwischen einer merklichen Wartezeit und keiner.
     */
    fun alleVektoren(dimensionen: Int): Vektorblock {
        val nummern = ArrayList<Int>(2048)
        val werte = ArrayList<ByteArray>(2048)
        abfragen(
            """
            SELECT einheit.nummer, vektor.werte
            FROM vektor JOIN einheit ON einheit.kennung = vektor.kennung
            ORDER BY einheit.nummer
            """.trimIndent(),
        ) { a ->
            nummern.add(a.getInt(0))
            werte.add(a.getBlob(1))
        }
        val block = FloatArray(nummern.size * dimensionen)
        var ziel = 0
        for (rohe in werte) {
            val puffer = java.nio.ByteBuffer.wrap(rohe).order(java.nio.ByteOrder.LITTLE_ENDIAN)
            for (i in 0 until dimensionen) {
                block[ziel++] = puffer.getFloat(i * 4)
            }
        }
        return Vektorblock(nummern.toIntArray(), block, dimensionen)
    }

    // -------------------------------------------------------------- Regelwerk

    fun pflichten(): List<Pflicht> = abfragen(
        "SELECT kennung, titel, was_zu_tun_ist, rechtsgrundlage, fundstellen_text," +
            " rollen, klassen, schwere, gilt_ab, nachweis, bei_verstoss FROM pflicht",
    ) { a ->
        Pflicht(
            kennung = a.getText(0),
            titel = a.getText(1),
            wasZuTunIst = a.getText(2),
            rechtsgrundlage = textListe(a.getText(3)),
            fundstellenText = a.getText(4),
            rollen = textListe(a.getText(5)).toSet(),
            klassen = textListe(a.getText(6)).toSet(),
            schwere = a.getText(7),
            giltAb = if (a.isNull(8)) null else a.getText(8),
            nachweis = a.getText(9),
            beiVerstoss = a.getText(10),
        )
    }

    fun risikoregeln(): List<Risikoregel> = abfragen(
        "SELECT kennung, art, rang, klasse, rolle, titel, fundstelle, rechtsgrundlage," +
            " bedingungen, stichworte, frage, begruendung, sicherheit, gilt_ab, zusatz" +
            " FROM risikoregel ORDER BY rang",
    ) { a ->
        Risikoregel(
            kennung = a.getText(0),
            art = a.getText(1),
            rang = a.getInt(2),
            klasse = if (a.isNull(3)) null else a.getText(3),
            rolle = if (a.isNull(4)) null else a.getText(4),
            titel = a.getText(5),
            fundstelle = a.getText(6),
            rechtsgrundlage = textListe(a.getText(7)),
            bedingungen = bedingungen(a.getText(8)),
            stichworte = textListe(a.getText(9)),
            frage = a.getText(10),
            begruendung = a.getText(11),
            sicherheit = a.getText(12),
            giltAb = if (a.isNull(13)) null else a.getText(13),
            zusatz = rohKarte(a.getText(14)),
        )
    }

    fun faelle(): List<Fall> = abfragen(
        "SELECT kennung, gebiet, titel, lage, rolle, einstufung, begruendung," +
            " rechtsgrundlage, pflichten, lernhinweis, stolperstein, verwandte_faelle" +
            " FROM fall ORDER BY kennung",
    ) { a ->
        Fall(
            kennung = a.getText(0),
            gebiet = a.getText(1),
            titel = a.getText(2),
            lage = a.getText(3),
            rolle = a.getText(4),
            einstufung = a.getText(5),
            begruendung = a.getText(6),
            rechtsgrundlage = textListe(a.getText(7)),
            pflichten = textListe(a.getText(8)),
            lernhinweis = a.getText(9),
            stolperstein = a.getText(10),
            verwandteFaelle = textListe(a.getText(11)),
        )
    }

    fun pruefabschnitte(): List<Pruefabschnitt> = abfragen(
        "SELECT kennung, rang, titel, frage, rechtsgrundlage, fundstellen_text," +
            " was_zu_tun_ist, nachweis, bei_verstoss FROM pruefabschnitt ORDER BY rang",
    ) { a ->
        Pruefabschnitt(
            kennung = a.getText(0),
            rang = a.getInt(1),
            titel = a.getText(2),
            frage = a.getText(3),
            rechtsgrundlage = textListe(a.getText(4)),
            fundstellenText = a.getText(5),
            wasZuTunIst = a.getText(6),
            nachweis = a.getText(7),
            beiVerstoss = a.getText(8),
        )
    }

    /** Die Tabelle meta: Datenstand, Modellname, Vorsilben. */
    fun meta(): Map<String, String> = abfragen(
        "SELECT schluessel, wert FROM meta",
    ) { a -> a.getText(0) to a.getText(1) }.toMap()
}

/**
 * Alle Vektoren in einem Block, dazu die Zuordnung zur Einheit.
 *
 * [nummern] und die Abschnitte in [werte] stehen in derselben Reihenfolge:
 * Zeile i beginnt bei i * dimensionen.
 */
class Vektorblock(
    val nummern: IntArray,
    val werte: FloatArray,
    val dimensionen: Int,
) {
    val anzahl: Int get() = nummern.size
}
