import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

ColumnLayout {
    id: root
    property var players: []
    property string version: ""
    property bool enemy: false
    spacing: 8
    ZText {
        text: root.enemy ? "L’ÉQUIPE ADVERSE" : "TON ÉQUIPE"
        color: root.enemy ? "#f29eaf" : "#70e1cc"
        font.pixelSize: 11
        font.letterSpacing: 2
        Layout.bottomMargin: 6
    }
    Repeater {
        model: root.players
        Rectangle {
            required property var modelData
            Layout.fillWidth: true
            implicitHeight: root.width < 320 ? 118 : 100
            radius: 12
            color: modelData.is_player ? "#223d49" : "#142535"
            border.color: modelData.is_player ? "#498d8d" : "#263c4e"
            HoverHandler {
                id: rowHover
            }
            ToolTip.visible: rowHover.hovered
            ToolTip.delay: 600
            ToolTip.text: modelData.position + " · " + modelData.damageText + " dégâts champions · Vision " + modelData.visionText
            RowLayout {
                anchors {
                    top: parent.top
                    left: parent.left
                    right: parent.right
                    margins: 10
                }
                spacing: 9
                Portrait {
                    identity: modelData.champion
                    version: root.version
                    width: 38
                }
                ColumnLayout {
                    spacing: 2
                    Layout.fillWidth: true
                    ZText {
                        text: modelData.champion + (modelData.is_player ? " · Toi" : "")
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                    }
                    ZText {
                        text: modelData.display_name
                        color: "#95acc3"
                        font.pixelSize: 11
                        elide: Text.ElideRight
                        wrapMode: Text.NoWrap
                        Layout.fillWidth: true
                    }
                }
                ZText {
                    text: modelData.kda
                    font.pixelSize: 12
                    color: root.enemy ? "#e4b5c0" : "#93e2d5"
                }
            }
            Row {
                anchors {
                    left: parent.left
                    bottom: parent.bottom
                    leftMargin: 10
                    bottomMargin: root.width < 320 ? 31 : 9
                }
                spacing: 3
                Repeater {
                    model: modelData.items
                    Portrait {
                        required property var modelData
                        kind: "item"
                        identity: String(modelData)
                        version: root.version
                        width: 23
                        radius: 4
                    }
                }
            }
            ZText {
                anchors {
                    right: parent.right
                    bottom: parent.bottom
                    rightMargin: 10
                    bottomMargin: 10
                }
                text: modelData.csText + " CS · " + modelData.goldText + " PO"
                color: "#95acc3"
                font.pixelSize: 10
            }
        }
    }
    ZText {
        visible: root.players.length === 0
        text: "Participants non disponibles"
        color: "#a3b7cc"
    }
}
