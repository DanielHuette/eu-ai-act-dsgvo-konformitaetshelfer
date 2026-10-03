package de.konformitaetshelfer

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import de.konformitaetshelfer.ui.Oberflaeche
import de.konformitaetshelfer.ui.Thema

/**
 * Der Einstieg. Mehr als das Fenster aufzuspannen tut diese Klasse nicht -
 * der Zustand lebt im Ansichtsmodell, damit ein Drehen des Geräts die
 * Auskunft nicht verwirft.
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        setContent {
            Thema {
                Oberflaeche()
            }
        }
    }
}
