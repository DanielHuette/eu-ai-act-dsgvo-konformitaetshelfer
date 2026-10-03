package de.konformitaetshelfer.suche

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.content.Context
import de.konformitaetshelfer.daten.Beigaben
import java.io.File
import java.nio.LongBuffer
import java.nio.channels.FileChannel

/**
 * Rechnet Text in 384 Zahlen um - auf dem Gerät, ohne Netz.
 *
 * Mittelwertbildung über die Wortmarken und die Längennormierung stecken im
 * ONNX-Graphen (siehe scripts/export_android.py). Diese Klasse gibt also nur
 * Marken hinein und bekommt fertige Zahlen heraus. Alles, was sie selbst
 * nachrechnen würde, könnte sie anders rechnen als der Bau des Bestands -
 * und dann wäre die Suche still falsch.
 *
 * Die Zahlen sind auf Länge 1 gebracht. Das Skalarprodukt zweier solcher
 * Reihen IST das Kosinusmaß; die Vektorsuche spart sich damit je Vergleich
 * eine Wurzel.
 */
class Einbetter private constructor(
    private val umgebung: OrtEnvironment,
    private val sitzung: OrtSession,
    private val zerleger: Wortzerleger,
    private val hoechstensMarken: Int,
) {

    /**
     * Bettet eine Frage ein. [vorsilbe] ist die des Modells - "query: " für
     * Fragen, "passage: " für Bestandstexte. Ohne die richtige Vorsilbe
     * fällt die Trefferqualität messbar ab, weil das Modell beides im
     * Training unterschieden hat.
     */
    fun einbetten(text: String, vorsilbe: String): FloatArray {
        val marken = zerleger.zerlegen(vorsilbe + text, hoechstensMarken)
        val form = longArrayOf(1L, marken.size.toLong())
        val maske = LongArray(marken.size) { 1L }

        val markenFeld = OnnxTensor.createTensor(umgebung, LongBuffer.wrap(marken), form)
        try {
            val maskenFeld = OnnxTensor.createTensor(umgebung, LongBuffer.wrap(maske), form)
            try {
                val eingabe = HashMap<String, OnnxTensor>(2)
                eingabe["input_ids"] = markenFeld
                eingabe["attention_mask"] = maskenFeld
                sitzung.run(eingabe).use { ergebnis ->
                    val puffer = (ergebnis.get(0) as OnnxTensor).floatBuffer
                    return FloatArray(puffer.remaining()) { puffer.get(it) }
                }
            } finally {
                maskenFeld.close()
            }
        } finally {
            markenFeld.close()
        }
    }

    fun schliessen() {
        sitzung.close()
    }

    companion object {
        /**
         * Öffnet Modell und Wortschatz.
         *
         * Das Modell wird möglichst aus dem App-Paket in den Speicher
         * eingeblendet statt herauskopiert: es ist 118 MB groß, und eine
         * zweite Kopie im Gerätespeicher wäre 118 MB für nichts. Das geht
         * nur, weil die Beigabe unkomprimiert abgelegt ist (siehe
         * androidResources in app/build.gradle.kts). Lässt sich die Beigabe
         * nicht einblenden, wird sie herausgelegt - langsamer beim ersten
         * Start, aber es läuft.
         */
        fun oeffnen(kontext: Context, hoechstensMarken: Int): Einbetter {
            val zerleger = kontext.assets.open("tokenizer.json").use { Wortzerleger.lesen(it) }
            val umgebung = OrtEnvironment.getEnvironment()
            val einstellungen = OrtSession.SessionOptions()
            einstellungen.setOptimizationLevel(
                OrtSession.SessionOptions.OptLevel.ALL_OPT
            )
            // Zwei Rechenwege: mehr bringt bei einer einzigen kurzen Frage
            // nichts und belegt nur Kerne, die die Oberfläche braucht.
            einstellungen.setIntraOpNumThreads(2)

            val eingeblendet = einblenden(kontext, "einbetter.onnx")
            val sitzung = if (eingeblendet != null) {
                umgebung.createSession(eingeblendet, einstellungen)
            } else {
                val datei = Beigaben.herauslegen(kontext, "einbetter.onnx")
                umgebung.createSession(datei.absolutePath, einstellungen)
            }
            return Einbetter(umgebung, sitzung, zerleger, hoechstensMarken)
        }

        /** Blendet eine unkomprimierte Beigabe aus dem Paket in den Speicher ein. */
        private fun einblenden(kontext: Context, name: String): java.nio.ByteBuffer? {
            return try {
                kontext.assets.openFd(name).use { beschreibung ->
                    FileChannel.open(
                        File(kontext.applicationInfo.sourceDir).toPath(),
                        java.nio.file.StandardOpenOption.READ,
                    ).use { kanal ->
                        kanal.map(
                            FileChannel.MapMode.READ_ONLY,
                            beschreibung.startOffset,
                            beschreibung.length,
                        )
                    }
                }
            } catch (fehler: Exception) {
                // Komprimiert abgelegt, geteiltes Paket oder kein Zugriff auf
                // die Paketdatei: dann wird herausgelegt.
                null
            }
        }
    }
}
