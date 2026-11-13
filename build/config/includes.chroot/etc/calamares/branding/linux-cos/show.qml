import QtQuick 2.0
import calamares.slideshow 1.0

Presentation {
    id: presentation

    Timer {
        interval: 20000
        running: true
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    Slide {
        Image {
            id: background1
            source: "slide-1.png"
            width: parent.width
            height: parent.height
            fillMode: Image.PreserveAspectCrop
        }
        Text {
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottomMargin: 60
            color: "#eef2ff"
            font.pointSize: 14
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            width: parent.width * 0.9
            text: "3,000+ tools, one system: Kali and Parrot native, BlackArch as plain commands\n3.000+ herramientas, un solo sistema: Kali y Parrot nativas, BlackArch como comandos normales"
        }
    }

    Slide {
        Image {
            id: background2
            source: "slide-1.png"
            width: parent.width
            height: parent.height
            fillMode: Image.PreserveAspectCrop
        }
        Text {
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottomMargin: 60
            color: "#eef2ff"
            font.pointSize: 14
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            width: parent.width * 0.9
            text: "Red team, blue team or both: switch the whole desktop with one click\nRed team, blue team o ambos: cambia todo el escritorio con un clic"
        }
    }

    Slide {
        Image {
            id: background3
            source: "slide-1.png"
            width: parent.width
            height: parent.height
            fillMode: Image.PreserveAspectCrop
        }
        Text {
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottomMargin: 60
            color: "#eef2ff"
            font.pointSize: 14
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            width: parent.width * 0.9
            text: "Hardened by default: AppArmor, firewall, auditd, full-disk encryption\nProtegido por defecto: AppArmor, cortafuegos, auditd, cifrado de disco completo"
        }
    }
}
