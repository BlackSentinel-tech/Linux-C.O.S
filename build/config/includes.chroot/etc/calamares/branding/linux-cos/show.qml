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
            text: "Kali + Parrot installed natively -- 550+ offensive tools ready at first login"
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
            text: "Run `blackarch-shell` for all 2,858 BlackArch tools, no setup needed"
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
            text: "AppArmor, firewall and auditd are already enforcing -- this box defends itself too"
        }
    }
}
