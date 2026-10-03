package de.konformitaetshelfer.daten

import android.content.Context
import de.konformitaetshelfer.BuildConfig
import java.io.File

/**
 * Holt die mitgelieferten Dateien aus dem Paket an eine Stelle, an der sie
 * sich öffnen lassen.
 *
 * SQLite braucht einen echten Dateipfad; eine Beigabe im Paket ist kein
 * Pfad. Also wird sie einmal herausgelegt. Das geschieht genau einmal je
 * App-Fassung: der Merker trägt die Fassungsnummer, und bei einem Update
 * wird neu gelegt, weil dann auch der Rechtsbestand neu ist.
 */
internal object Beigaben {

    fun herauslegen(kontext: Context, name: String): File {
        val ziel = File(kontext.filesDir, name)
        val merker = File(kontext.filesDir, "$name.fassung")
        val fassung = BuildConfig.VERSION_CODE.toString()

        if (ziel.isFile && merker.isFile && merker.readText() == fassung) {
            return ziel
        }

        // Erst vollständig daneben schreiben, dann umbenennen. Bricht das
        // Kopieren ab - kein Platz, App beendet -, bleibt keine halbe Datei
        // liegen, die beim nächsten Start als heil gilt.
        val halb = File(kontext.filesDir, "$name.teil")
        kontext.assets.open(name).use { quelle ->
            halb.outputStream().use { senke -> quelle.copyTo(senke, 1 shl 16) }
        }
        if (ziel.exists()) ziel.delete()
        if (!halb.renameTo(ziel)) {
            halb.delete()
            throw IllegalStateException("$name konnte nicht abgelegt werden")
        }
        merker.writeText(fassung)
        return ziel
    }
}
