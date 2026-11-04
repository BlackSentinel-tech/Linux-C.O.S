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
            text: "800+ Kali tools + Parrot extras, installed natively\n800+ herramientas de Kali + extras de Parrot, nativas"
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
            text: "blackarch-shell: BlackArch's 2,858 tools in a container (pacman -S <tool>)\nblackarch-shell: las 2.858 herramientas de BlackArch en un contenedor"
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
            text: "AppArmor, firewall and auditd on from the first boot -- this box defends itself too\nAppArmor, firewall y auditd activos desde el primer arranque"
        }
    }
}
