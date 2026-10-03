// Wo Gradle seine Werkzeuge und die Abhängigkeiten holt.
//
// Die Quellen sind hier und nur hier festgelegt. Ein Modul kann sich keine
// eigene Quelle dazuholen: bei einem Rechtsauskunftswerkzeug soll niemand
// nachträglich eine fremde Paketquelle einschleusen können.

pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "konformitaetshelfer"
include(":app")
