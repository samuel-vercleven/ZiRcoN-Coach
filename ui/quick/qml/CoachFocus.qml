import QtQuick
import QtQuick.Layouts

Surface {
    id: root
    property var coaching: ({})
    property bool expanded: false
    tint: "#19393e"
    implicitHeight: content.implicitHeight + 40
    ColumnLayout {
        id: content
        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            margins: 20
        }
        spacing: 12
        ZText {
            text: "TON PROCHAIN RÉFLEXE"
            color: "#73e4c8"
            font.pixelSize: 11
            font.letterSpacing: 2
        }
        ZText {
            text: root.coaching.title || ""
            font.pixelSize: 20
            font.weight: Font.DemiBold
            Layout.fillWidth: true
        }
        ZText {
            text: root.coaching.observation || ""
            color: "#adc5ce"
            Layout.fillWidth: true
        }
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: action.implicitHeight + 24
            radius: 12
            color: "#244b50"
            ZText {
                id: action
                anchors {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                    margins: 12
                }
                text: root.coaching.next_game_experiment || ""
                font.weight: Font.DemiBold
            }
        }
        ZText {
            text: "Une piste à tester, pas une cause certaine du résultat."
            color: "#a3bac5"
            font.pixelSize: 12
            Layout.fillWidth: true
        }
        ZButton {
            text: root.expanded ? "Masquer les explications" : "Comprendre ce conseil"
            onClicked: root.expanded = !root.expanded
        }
        ColumnLayout {
            visible: root.expanded
            Layout.fillWidth: true
            spacing: 10
            ZText {
                text: root.coaching.why_review || ""
                color: "#b2c6d6"
                Layout.fillWidth: true
            }
            Repeater {
                model: root.coaching.evidence || []
                ZText {
                    required property string modelData
                    text: modelData
                    color: "#94adc2"
                    font.pixelSize: 12
                    Layout.fillWidth: true
                }
            }
            ZText {
                text: root.coaching.limitation || ""
                color: "#94adc2"
                font.pixelSize: 12
                Layout.fillWidth: true
            }
        }
    }
}
